"""
AIAS Database Models
Data access layer for Users, OTPs, and Sessions.
All queries use parameterized statements to prevent SQL injection.
"""

from datetime import datetime, timedelta, timezone

from database.db import db
from config import Config


class UserModel:
    """User data access operations."""

    @staticmethod
    def create_user(email, password_hash, display_name="", is_google_user=False):
        """Create a new user account."""
        return db.execute(
            """INSERT INTO users (email, password_hash, display_name, is_google_user, is_verified)
               VALUES (?, ?, ?, ?, ?)""",
            (email.lower().strip(), password_hash, display_name, int(is_google_user), int(is_google_user)),
        )

    @staticmethod
    def get_by_email(email):
        """Find a user by email (case-insensitive)."""
        return db.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.lower().strip(),),
            fetch_one=True,
        )

    @staticmethod
    def get_by_id(user_id):
        """Find a user by ID."""
        return db.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
            fetch_one=True,
        )

    @staticmethod
    def verify_user(email):
        """Mark a user as email-verified."""
        db.execute(
            "UPDATE users SET is_verified = 1, updated_at = CURRENT_TIMESTAMP WHERE email = ?",
            (email.lower().strip(),),
        )

    @staticmethod
    def increment_failed_attempts(email):
        """Increment failed login attempts. Lock account if threshold reached."""
        user = UserModel.get_by_email(email)
        if not user:
            return

        new_count = user["failed_login_attempts"] + 1
        locked_until = None

        if new_count >= Config.MAX_FAILED_LOGINS:
            locked_until = (
                datetime.now(timezone.utc) + timedelta(minutes=Config.LOCKOUT_DURATION_MINUTES)
            ).isoformat()

        db.execute(
            """UPDATE users
               SET failed_login_attempts = ?, locked_until = ?, updated_at = CURRENT_TIMESTAMP
               WHERE email = ?""",
            (new_count, locked_until, email.lower().strip()),
        )

    @staticmethod
    def reset_failed_attempts(email):
        """Reset failed login counter on successful login."""
        db.execute(
            """UPDATE users
               SET failed_login_attempts = 0, locked_until = NULL, updated_at = CURRENT_TIMESTAMP
               WHERE email = ?""",
            (email.lower().strip(),),
        )

    @staticmethod
    def is_locked(email):
        """Check if account is currently locked."""
        user = UserModel.get_by_email(email)
        if not user or not user["locked_until"]:
            return False
        locked_until = datetime.fromisoformat(user["locked_until"])
        if datetime.now(timezone.utc) > locked_until:
            # Lock expired, reset
            UserModel.reset_failed_attempts(email)
            return False
        return True

    @staticmethod
    def update_password(email, password_hash):
        """Update user's password hash."""
        db.execute(
            "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE email = ?",
            (password_hash, email.lower().strip()),
        )

    @staticmethod
    def email_exists(email):
        """Check if an email is already registered."""
        result = db.execute(
            "SELECT COUNT(*) as cnt FROM users WHERE email = ?",
            (email.lower().strip(),),
            fetch_one=True,
        )
        return result["cnt"] > 0 if result else False


class OTPModel:
    """OTP data access operations."""

    @staticmethod
    def create_otp(email, otp_hash, purpose="signin"):
        """Store a hashed OTP with expiry."""
        expires_at = (
            datetime.now(timezone.utc) + timedelta(minutes=Config.OTP_EXPIRY_MINUTES)
        ).isoformat()

        # Invalidate any existing unused OTPs for this email and purpose
        db.execute(
            """UPDATE otp_codes SET is_used = 1
               WHERE email = ? AND purpose = ? AND is_used = 0""",
            (email.lower().strip(), purpose),
        )

        return db.execute(
            """INSERT INTO otp_codes (email, otp_hash, purpose, expires_at)
               VALUES (?, ?, ?, ?)""",
            (email.lower().strip(), otp_hash, purpose, expires_at),
        )

    @staticmethod
    def get_active_otp(email, purpose="signin"):
        """Get the latest active (unused, not expired) OTP for an email."""
        now = datetime.now(timezone.utc).isoformat()
        return db.execute(
            """SELECT * FROM otp_codes
               WHERE email = ? AND purpose = ? AND is_used = 0 AND expires_at > ?
               ORDER BY created_at DESC LIMIT 1""",
            (email.lower().strip(), purpose, now),
            fetch_one=True,
        )

    @staticmethod
    def increment_attempts(otp_id):
        """Increment verification attempts for an OTP."""
        db.execute(
            "UPDATE otp_codes SET attempts = attempts + 1 WHERE id = ?",
            (otp_id,),
        )

    @staticmethod
    def mark_used(otp_id):
        """Mark OTP as used (one-time use)."""
        db.execute(
            "UPDATE otp_codes SET is_used = 1 WHERE id = ?",
            (otp_id,),
        )

    @staticmethod
    def cleanup_expired():
        """Delete expired OTPs from database."""
        now = datetime.now(timezone.utc).isoformat()
        db.execute(
            "DELETE FROM otp_codes WHERE expires_at < ? OR is_used = 1",
            (now,),
        )


class SessionModel:
    """Session data access operations."""

    @staticmethod
    def create_session(user_id, session_token):
        """Create a new session."""
        expires_at = (
            datetime.now(timezone.utc) + timedelta(hours=Config.SESSION_LIFETIME_HOURS)
        ).isoformat()
        return db.execute(
            """INSERT INTO sessions (user_id, session_token, expires_at)
               VALUES (?, ?, ?)""",
            (user_id, session_token, expires_at),
        )

    @staticmethod
    def get_session(session_token):
        """Retrieve a valid session."""
        now = datetime.now(timezone.utc).isoformat()
        return db.execute(
            """SELECT * FROM sessions
               WHERE session_token = ? AND expires_at > ?""",
            (session_token, now),
            fetch_one=True,
        )

    @staticmethod
    def delete_session(session_token):
        """Delete a session (logout)."""
        db.execute(
            "DELETE FROM sessions WHERE session_token = ?",
            (session_token,),
        )

    @staticmethod
    def delete_user_sessions(user_id):
        """Delete all sessions for a user."""
        db.execute(
            "DELETE FROM sessions WHERE user_id = ?",
            (user_id,),
        )

    @staticmethod
    def cleanup_expired():
        """Remove expired sessions."""
        now = datetime.now(timezone.utc).isoformat()
        db.execute(
            "DELETE FROM sessions WHERE expires_at < ?",
            (now,),
        )
