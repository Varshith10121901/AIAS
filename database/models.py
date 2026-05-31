from datetime import datetime, timedelta, timezone
from bson import ObjectId

from database.db import db, sanitize_doc
from config import Config


def to_object_id(val):
    """Safely convert a string to a BSON ObjectId if valid."""
    if isinstance(val, ObjectId):
        return val
    try:
        return ObjectId(str(val))
    except Exception:
        return val


class UserModel:
    """User data access operations using MongoDB."""

    @staticmethod
    def create_user(email, password_hash, display_name="", is_google_user=False):
        """Create a new user account."""
        display_name = (display_name or "").strip()
        email_clean = email.lower().strip()
        
        user_doc = {
            "email": email_clean,
            "password_hash": password_hash,
            "display_name": display_name,
            "is_google_user": bool(is_google_user),
            "is_verified": bool(is_google_user),
            "failed_login_attempts": 0,
            "locked_until": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        res = db.users.insert_one(user_doc)
        return str(res.inserted_id)

    @staticmethod
    def get_by_email(email):
        """Find a user by email (case-insensitive)."""
        email_clean = email.lower().strip()
        doc = db.users.find_one({"email": email_clean})
        return sanitize_doc(doc)

    @staticmethod
    def get_by_id(user_id):
        """Find a user by ID."""
        doc = db.users.find_one({"_id": to_object_id(user_id)})
        return sanitize_doc(doc)

    @staticmethod
    def verify_user(email):
        """Mark a user as email-verified."""
        email_clean = email.lower().strip()
        db.users.update_one(
            {"email": email_clean},
            {"$set": {"is_verified": True, "updated_at": datetime.now(timezone.utc)}}
        )

    @staticmethod
    def increment_failed_attempts(email):
        """Increment failed login attempts. Lock account if threshold reached."""
        email_clean = email.lower().strip()
        user = UserModel.get_by_email(email_clean)
        if not user:
            return

        new_count = user.get("failed_login_attempts", 0) + 1
        locked_until = None

        if new_count >= Config.MAX_FAILED_LOGINS:
            locked_until = datetime.now(timezone.utc) + timedelta(minutes=Config.LOCKOUT_DURATION_MINUTES)

        db.users.update_one(
            {"email": email_clean},
            {
                "$set": {
                    "failed_login_attempts": new_count,
                    "locked_until": locked_until,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )

    @staticmethod
    def reset_failed_attempts(email):
        """Reset failed login counter on successful login."""
        email_clean = email.lower().strip()
        db.users.update_one(
            {"email": email_clean},
            {
                "$set": {
                    "failed_login_attempts": 0,
                    "locked_until": None,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )

    @staticmethod
    def is_locked(email):
        """Check if account is currently locked."""
        user = UserModel.get_by_email(email)
        if not user or not user.get("locked_until"):
            return False
        
        locked_until = user["locked_until"]
        if isinstance(locked_until, str):
            locked_until = datetime.fromisoformat(locked_until)
            
        if datetime.now(timezone.utc) > locked_until:
            # Lock expired, reset
            UserModel.reset_failed_attempts(email)
            return False
        return True

    @staticmethod
    def update_password(email, password_hash):
        """Update user's password hash."""
        email_clean = email.lower().strip()
        db.users.update_one(
            {"email": email_clean},
            {"$set": {"password_hash": password_hash, "updated_at": datetime.now(timezone.utc)}}
        )

    @staticmethod
    def email_exists(email):
        """Check if an email is already registered."""
        email_clean = email.lower().strip()
        count = db.users.count_documents({"email": email_clean})
        return count > 0


class OTPModel:
    """OTP data access operations using MongoDB."""

    @staticmethod
    def create_otp(email, otp_hash, purpose="signin"):
        """Store a hashed OTP with expiry."""
        email_clean = email.lower().strip()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=Config.OTP_EXPIRY_MINUTES)

        # Invalidate any existing unused OTPs for this email and purpose
        db.otp_codes.update_many(
            {"email": email_clean, "purpose": purpose, "is_used": False},
            {"$set": {"is_used": True}}
        )

        otp_doc = {
            "email": email_clean,
            "otp_hash": otp_hash,
            "purpose": purpose,
            "attempts": 0,
            "max_attempts": Config.OTP_MAX_ATTEMPTS,
            "is_used": False,
            "created_at": datetime.now(timezone.utc),
            "expires_at": expires_at,
        }
        res = db.otp_codes.insert_one(otp_doc)
        return str(res.inserted_id)

    @staticmethod
    def get_active_otp(email, purpose="signin"):
        """Get the latest active (unused, not expired) OTP for an email."""
        email_clean = email.lower().strip()
        now = datetime.now(timezone.utc)
        
        doc = db.otp_codes.find_one({
            "email": email_clean,
            "purpose": purpose,
            "is_used": False,
            "expires_at": {"$gt": now}
        }, sort=[("created_at", -1)])
        
        return sanitize_doc(doc)

    @staticmethod
    def increment_attempts(otp_id):
        """Increment verification attempts for an OTP."""
        db.otp_codes.update_one(
            {"_id": to_object_id(otp_id)},
            {"$inc": {"attempts": 1}}
        )

    @staticmethod
    def mark_used(otp_id):
        """Mark OTP as used (one-time use)."""
        db.otp_codes.update_one(
            {"_id": to_object_id(otp_id)},
            {"$set": {"is_used": True}}
        )

    @staticmethod
    def cleanup_expired():
        """Delete expired/used OTPs from database."""
        now = datetime.now(timezone.utc)
        db.otp_codes.delete_many({
            "$or": [
                {"expires_at": {"$lt": now}},
                {"is_used": True}
            ]
        })


class SessionModel:
    """Session data access operations using MongoDB."""

    @staticmethod
    def create_session(user_id, session_token):
        """Create a new session."""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=Config.SESSION_LIFETIME_HOURS)
        
        session_doc = {
            "user_id": str(user_id),
            "session_token": session_token,
            "created_at": datetime.now(timezone.utc),
            "expires_at": expires_at,
        }
        res = db.sessions.insert_one(session_doc)
        
        # Cache session in Redis
        try:
            from auth.redis_service import RedisService
            ttl_seconds = int((expires_at - datetime.now(timezone.utc)).total_seconds())
            if ttl_seconds > 0:
                RedisService.cache_session(session_token, str(user_id), ttl_seconds)
        except Exception:
            pass
            
        return str(res.inserted_id)

    @staticmethod
    def get_session(session_token):
        """Retrieve a valid session."""
        # Try fetching from Redis cache first
        try:
            from auth.redis_service import RedisService
            cached = RedisService.get_cached_session(session_token)
            if cached:
                # Wrap cached value to look like a database row if needed
                # RedisService.get_cached_session returns the user_id (string) or dict.
                # If it's a string user_id, construct a dict representation.
                if isinstance(cached, str):
                    return {"user_id": cached, "session_token": session_token}
                return cached
        except Exception:
            pass

        now = datetime.now(timezone.utc)
        doc = db.sessions.find_one({
            "session_token": session_token,
            "expires_at": {"$gt": now}
        })
        
        session_record = sanitize_doc(doc)
        
        # Cache session in Redis if found in DB
        if session_record:
            try:
                from auth.redis_service import RedisService
                ttl_seconds = int((session_record["expires_at"] - now).total_seconds())
                if ttl_seconds > 0:
                    RedisService.cache_session(session_token, session_record["user_id"], ttl_seconds)
            except Exception:
                pass
                
        return session_record

    @staticmethod
    def delete_session(session_token):
        """Delete a session (logout)."""
        db.sessions.delete_one({"session_token": session_token})
        
        # Clear from Redis cache
        try:
            from auth.redis_service import RedisService
            RedisService.delete_cached_session(session_token)
        except Exception:
            pass

    @staticmethod
    def delete_user_sessions(user_id):
        """Delete all sessions for a user."""
        db.sessions.delete_many({"user_id": str(user_id)})
        
        # Clear user sessions from Redis
        try:
            from auth.redis_service import RedisService
            RedisService.delete_user_sessions(str(user_id))
        except Exception:
            pass

    @staticmethod
    def cleanup_expired():
        """Remove expired sessions."""
        now = datetime.now(timezone.utc)
        db.sessions.delete_many({"expires_at": {"$lt": now}})
