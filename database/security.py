"""
AIAS Database Security Utilities
Handles expired data cleanup, rate limit log management,
and database integrity checks.
"""

from datetime import datetime, timedelta, timezone

from database.db import db
from config import Config


class DatabaseSecurity:
    """Database hardening and maintenance utilities."""

    @staticmethod
    def cleanup_all():
        """Run all cleanup operations."""
        DatabaseSecurity.cleanup_expired_otps()
        DatabaseSecurity.cleanup_expired_sessions()
        DatabaseSecurity.cleanup_old_rate_logs()

    @staticmethod
    def cleanup_expired_otps():
        """Purge expired and used OTPs."""
        now = datetime.now(timezone.utc).isoformat()
        db.execute(
            "DELETE FROM otp_codes WHERE expires_at < ? OR is_used = 1",
            (now,),
        )

    @staticmethod
    def cleanup_expired_sessions():
        """Remove expired sessions."""
        now = datetime.now(timezone.utc).isoformat()
        db.execute(
            "DELETE FROM sessions WHERE expires_at < ?",
            (now,),
        )

    @staticmethod
    def cleanup_old_rate_logs():
        """Remove rate limit logs older than 2 hours."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        db.execute(
            "DELETE FROM rate_limit_log WHERE created_at < ?",
            (cutoff,),
        )

    @staticmethod
    def log_rate_event(email, action):
        """Log a rate-limited action (OTP request, failed login, etc.)."""
        db.execute(
            "INSERT INTO rate_limit_log (email, action) VALUES (?, ?)",
            (email.lower().strip(), action),
        )

    @staticmethod
    def count_recent_events(email, action, minutes=60):
        """Count how many times an action occurred in the last N minutes."""
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
        result = db.execute(
            """SELECT COUNT(*) as cnt FROM rate_limit_log
               WHERE email = ? AND action = ? AND created_at > ?""",
            (email.lower().strip(), action, cutoff),
            fetch_one=True,
        )
        return result["cnt"] if result else 0

    @staticmethod
    def check_database_integrity():
        """Run SQLite integrity check."""
        result = db.execute("PRAGMA integrity_check", fetch_one=True)
        return result[0] == "ok" if result else False
