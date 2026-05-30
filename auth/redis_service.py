import json
import logging
import threading
import time

import redis

from config import Config

logger = logging.getLogger("aias.redis")


class _CircuitState:
    """Thread-safe circuit breaker state machine."""
    CLOSED = "CLOSED"       # Normal — all operations go through
    OPEN = "OPEN"           # Failed — operations return fallback, waiting for cooldown
    HALF_OPEN = "HALF_OPEN" # Testing — trying one real operation to see if recovered


class RedisService:
    """
    Redis connection manager with circuit breaker for automatic recovery.

    Connection Type : redis-py ConnectionPool → TCP
    Target          : Configured via REDIS_URL (default: localhost:6379)
    Pooling         : redis.ConnectionPool (max_connections=20)
    Recovery        : Circuit breaker — CLOSED → OPEN (on failure) → HALF_OPEN (after cooldown) → CLOSED (on success)
    """

    _client = None
    _lock = threading.Lock()

    # Circuit breaker state
    _circuit_state = _CircuitState.CLOSED
    _last_failure_time = 0.0
    _consecutive_failures = 0
    _failure_threshold = 1        # open circuit after first failed get_client() (which already retries 2x internally)
    _cooldown_seconds = Config.REDIS_CIRCUIT_BREAKER_COOLDOWN  # seconds before trying again

    @classmethod
    def _should_attempt(cls):
        """
        Determine whether we should attempt a Redis operation based on circuit state.
        Returns True if CLOSED, or if OPEN and cooldown has elapsed (transitions to HALF_OPEN).
        """
        if cls._circuit_state == _CircuitState.CLOSED:
            return True

        if cls._circuit_state == _CircuitState.OPEN:
            elapsed = time.monotonic() - cls._last_failure_time
            if elapsed >= cls._cooldown_seconds:
                # Cooldown expired — transition to half-open for a probe
                cls._circuit_state = _CircuitState.HALF_OPEN
                logger.info(
                    "[Redis] Circuit breaker → HALF_OPEN (cooldown %.0fs elapsed, probing recovery)",
                    elapsed
                )
                return True
            return False

        # HALF_OPEN — allow one attempt
        return True

    @classmethod
    def _record_success(cls):
        """Record a successful operation — close the circuit."""
        if cls._circuit_state != _CircuitState.CLOSED:
            logger.info("[Redis] Circuit breaker → CLOSED (connection recovered)")
        cls._circuit_state = _CircuitState.CLOSED
        cls._consecutive_failures = 0

    @classmethod
    def _record_failure(cls, error_msg=""):
        """Record a failure — open the circuit if threshold reached."""
        cls._consecutive_failures += 1
        cls._last_failure_time = time.monotonic()

        if cls._consecutive_failures >= cls._failure_threshold or cls._circuit_state == _CircuitState.HALF_OPEN:
            if cls._circuit_state != _CircuitState.OPEN:
                logger.warning(
                    "[Redis] Circuit breaker → OPEN (failures=%d, cooldown=%ds): %s",
                    cls._consecutive_failures, cls._cooldown_seconds, error_msg[:200]
                )
            cls._circuit_state = _CircuitState.OPEN
            # Discard the broken client so next probe creates a fresh one
            cls._client = None

    @classmethod
    def get_client(cls):
        """
        Retrieve the Redis client instance.
        Returns None if the circuit is open (Redis unavailable).
        Creates a new connection with retry (2 attempts, 0.5s backoff).
        """
        if not cls._should_attempt():
            return None

        if cls._client is not None:
            return cls._client

        with cls._lock:
            # Double-check after acquiring lock
            if cls._client is not None:
                return cls._client

            # Try to connect with retry
            for attempt in range(1, 3):  # 2 attempts
                try:
                    pool = redis.ConnectionPool.from_url(
                        Config.REDIS_URL,
                        decode_responses=True,
                        max_connections=Config.REDIS_MAX_CONNECTIONS,
                        socket_connect_timeout=Config.REDIS_SOCKET_TIMEOUT,
                        socket_timeout=Config.REDIS_SOCKET_TIMEOUT,
                        retry_on_timeout=True,
                        health_check_interval=30,
                    )
                    client = redis.Redis(connection_pool=pool)
                    # Test connectivity
                    client.ping()
                    cls._client = client
                    cls._record_success()
                    logger.info(
                        "[Redis] Connected — URL=%s | Pool=%d max | Timeout=%ds",
                        Config.REDIS_URL.split("@")[-1] if "@" in Config.REDIS_URL else Config.REDIS_URL,
                        Config.REDIS_MAX_CONNECTIONS,
                        Config.REDIS_SOCKET_TIMEOUT,
                    )
                    return cls._client
                except Exception as exc:
                    if attempt < 2:
                        logger.warning(
                            "[Redis] Connection attempt %d failed: %s — retrying in 0.5s",
                            attempt, str(exc)[:200]
                        )
                        time.sleep(0.5)
                    else:
                        cls._record_failure(str(exc))
                        logger.warning(
                            "[Redis] All connection attempts failed. "
                            "Caching & Redis rate limiting degraded. Error: %s",
                            str(exc)[:200]
                        )
                        return None

    @classmethod
    def _safe_op(cls, operation_name, fn, fallback=None):
        """
        Execute a Redis operation with circuit breaker protection.
        If the circuit is open or the operation fails, returns the fallback value.
        """
        if not cls._should_attempt():
            return fallback

        client = cls.get_client()
        if not client:
            return fallback

        try:
            result = fn(client)
            cls._record_success()
            return result
        except (redis.ConnectionError, redis.TimeoutError, ConnectionResetError, OSError) as exc:
            cls._record_failure(str(exc))
            logger.warning("[Redis] %s failed (circuit may open): %s", operation_name, str(exc)[:200])
            return fallback
        except Exception as exc:
            # Non-connection errors (e.g. bad data) — don't trip the circuit
            logger.warning("[Redis] %s error (non-connection): %s", operation_name, str(exc)[:200])
            return fallback

    @classmethod
    def cache_session(cls, session_token, user_id, expires_in_seconds):
        """Cache a session token mapping in Redis with expiration TTL."""
        def _op(client):
            session_data = {"user_id": user_id, "session_token": session_token}
            client.set(f"session:{session_token}", json.dumps(session_data), ex=expires_in_seconds)
            return True
        return cls._safe_op("cache_session", _op, fallback=False)

    @classmethod
    def get_cached_session(cls, session_token):
        """Fetch a cached session token mapping from Redis."""
        def _op(client):
            data = client.get(f"session:{session_token}")
            return json.loads(data) if data else None
        return cls._safe_op("get_cached_session", _op, fallback=None)

    @classmethod
    def delete_cached_session(cls, session_token):
        """Delete a cached session token mapping from Redis."""
        def _op(client):
            client.delete(f"session:{session_token}")
            return True
        return cls._safe_op("delete_cached_session", _op, fallback=False)

    @classmethod
    def delete_user_sessions(cls, user_id):
        """Scan and clear all cached sessions belonging to a specific user ID."""
        def _op(client):
            cursor = 0
            keys_to_delete = []
            while True:
                cursor, keys = client.scan(cursor, match="session:*", count=100)
                for k in keys:
                    data = client.get(k)
                    if data:
                        try:
                            sess = json.loads(data)
                            if sess.get("user_id") == user_id:
                                keys_to_delete.append(k)
                        except Exception:
                            pass
                if cursor == 0:
                    break
            if keys_to_delete:
                client.delete(*keys_to_delete)
            return True
        return cls._safe_op("delete_user_sessions", _op, fallback=False)

    @classmethod
    def check_rate_limit(cls, key, limit, window_seconds):
        """
        Perform sliding window rate limiting using Redis sorted sets.
        Returns a tuple of (allowed: bool, current_count: int).
        Fails open (allows request) if Redis is unavailable.
        """
        def _op(client):
            now = time.time()
            clear_before = now - window_seconds

            # Atomic pipeline
            pipe = client.pipeline()
            pipe.zremrangebyscore(key, 0, clear_before)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, window_seconds + 10)

            results = pipe.execute()
            cardinality = results[2]

            if cardinality > limit:
                return False, cardinality
            return True, cardinality

        result = cls._safe_op("check_rate_limit", _op, fallback=(True, 0))
        return result

    @classmethod
    def health_check(cls):
        """
        Check Redis connectivity and return status report.
        Fast path: returns cached state when circuit is OPEN (no re-probe).
        Returns dict with: status, latency_ms, connection_type, circuit_state, error.
        """
        result = {
            "service": "Redis",
            "connection_type": "redis-py ConnectionPool → TCP",
            "server": Config.REDIS_URL.split("@")[-1] if "@" in Config.REDIS_URL else Config.REDIS_URL,
            "pooling": f"ConnectionPool (max={Config.REDIS_MAX_CONNECTIONS})",
            "circuit_state": cls._circuit_state,
            "consecutive_failures": cls._consecutive_failures,
            "status": "offline",
            "latency_ms": None,
            "error": None,
        }

        # Fast path: if circuit is OPEN and cooldown hasn't elapsed, just report state
        if cls._circuit_state == _CircuitState.OPEN:
            cooldown_remaining = cls._cooldown_seconds - (time.monotonic() - cls._last_failure_time)
            if cooldown_remaining > 0:
                result["error"] = f"Circuit OPEN — auto-retry in {cooldown_remaining:.0f}s"
                return result

        # If we already have a live client, use it for a fast ping
        # Otherwise attempt a fresh connection (this also respects circuit state)
        client = cls._client if cls._client else cls.get_client()
        if not client:
            result["error"] = "Could not establish connection"
            return result

        try:
            t0 = time.monotonic()
            client.ping()
            elapsed = (time.monotonic() - t0) * 1000

            info = client.info(section="server")
            result["status"] = "healthy"
            result["latency_ms"] = round(elapsed, 1)
            result["redis_version"] = info.get("redis_version", "unknown")
            result["circuit_state"] = cls._circuit_state
            cls._record_success()
        except Exception as exc:
            cls._record_failure(str(exc))
            result["status"] = "degraded"
            result["circuit_state"] = cls._circuit_state
            result["error"] = str(exc)[:300]

        return result
