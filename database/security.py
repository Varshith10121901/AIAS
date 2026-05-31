from datetime import datetime, timedelta, timezone

from database.db import db


class DatabaseSecurity:
    """Database hardening and maintenance utilities using MongoDB."""

    @staticmethod
    def cleanup_all():
        """Run all cleanup operations."""
        DatabaseSecurity.cleanup_expired_otps()
        DatabaseSecurity.cleanup_expired_sessions()
        DatabaseSecurity.cleanup_old_rate_logs()

    @staticmethod
    def cleanup_expired_otps():
        """Purge expired and used OTPs."""
        now = datetime.now(timezone.utc)
        db.otp_codes.delete_many({
            "$or": [
                {"expires_at": {"$lt": now}},
                {"is_used": True}
            ]
        })

    @staticmethod
    def cleanup_expired_sessions():
        """Remove expired sessions."""
        now = datetime.now(timezone.utc)
        db.sessions.delete_many({"expires_at": {"$lt": now}})

    @staticmethod
    def cleanup_old_rate_logs():
        """Remove rate limit logs older than 2 hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=2)
        db.rate_limit_log.delete_many({"created_at": {"$lt": cutoff}})

    @staticmethod
    def log_rate_event(email, action):
        """Log a rate-limited action (OTP request, failed login, etc.)."""
        db.rate_limit_log.insert_one({
            "email": email.lower().strip(),
            "action": action,
            "created_at": datetime.now(timezone.utc)
        })

    @staticmethod
    def count_recent_events(email, action, minutes=60):
        """Count how many times an action occurred in the last N minutes."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return db.rate_limit_log.count_documents({
            "email": email.lower().strip(),
            "action": action,
            "created_at": {"$gt": cutoff}
        })

    @staticmethod
    def check_database_integrity():
        """Run a basic connectivity check (ping MongoDB)."""
        try:
            db.command("ping")
            return True
        except Exception:
            return False
