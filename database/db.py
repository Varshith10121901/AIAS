"""
AIAS Database Connection Manager
Provides secure SQLite connection handling with WAL mode,
parameterized queries, and automatic table creation.
"""

import os
import sqlite3
import threading
from contextlib import contextmanager

from config import Config


class Database:
    """Thread-safe SQLite database manager."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern — one database instance across the app."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.db_path = Config.DATABASE_PATH
        self._ensure_directory()
        self._init_database()
        self._initialized = True

    def _ensure_directory(self):
        """Create database directory if it doesn't exist."""
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def _get_connection(self):
        """Create a new connection with security settings."""
        conn = sqlite3.connect(
            self.db_path,
            timeout=30,
        )
        conn.row_factory = sqlite3.Row
        # Security & performance pragmas
        conn.execute("PRAGMA journal_mode=WAL")        # Write-Ahead Logging for concurrency
        conn.execute("PRAGMA foreign_keys=ON")          # Enforce foreign key constraints
        conn.execute("PRAGMA secure_delete=ON")         # Zero-fill deleted data
        conn.execute("PRAGMA auto_vacuum=FULL")         # Reclaim space automatically
        conn.execute("PRAGMA busy_timeout=5000")        # Wait 5s on lock contention
        return conn

    @contextmanager
    def get_db(self):
        """Context manager for database connections. Auto-commits or rolls back."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute(self, query, params=(), fetch_one=False, fetch_all=False):
        """
        Execute a parameterized query safely.
        NEVER use string formatting for queries — always use ? placeholders.
        """
        with self.get_db() as conn:
            cursor = conn.execute(query, params)
            if fetch_one:
                return cursor.fetchone()
            if fetch_all:
                return cursor.fetchall()
            return cursor.lastrowid

    def execute_many(self, query, params_list):
        """Execute a query with multiple parameter sets."""
        with self.get_db() as conn:
            conn.executemany(query, params_list)

    def _init_database(self):
        """Create all tables on first run."""
        with self.get_db() as conn:
            # ---- USERS TABLE ----
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                    password_hash TEXT,
                    display_name TEXT NOT NULL DEFAULT '',
                    is_google_user INTEGER NOT NULL DEFAULT 0,
                    is_verified INTEGER NOT NULL DEFAULT 0,
                    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
                    locked_until TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # ---- OTP TABLE ----
            conn.execute("""
                CREATE TABLE IF NOT EXISTS otp_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL COLLATE NOCASE,
                    otp_hash TEXT NOT NULL,
                    purpose TEXT NOT NULL DEFAULT 'signin',
                    attempts INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 5,
                    is_used INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT NOT NULL
                )
            """)

            # ---- ACTIVE SESSIONS TABLE ----
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # ---- RATE LIMIT LOG ----
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rate_limit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL COLLATE NOCASE,
                    action TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # ---- BOOKINGS TABLE (Chatbot leads) ----
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL DEFAULT '',
                    email TEXT DEFAULT '',
                    whatsapp TEXT DEFAULT '',
                    service_needed TEXT DEFAULT '',
                    budget_range TEXT DEFAULT '',
                    timeline TEXT DEFAULT '',
                    problem_statement TEXT DEFAULT '',
                    source TEXT DEFAULT 'website',
                    lead_status TEXT DEFAULT 'new',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # ---- INDEXES for performance ----
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_otp_email ON otp_codes(email)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_otp_expires ON otp_codes(expires_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_rate_limit_email ON rate_limit_log(email, action)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_bookings_email ON bookings(email)")


# Global database instance
db = Database()
