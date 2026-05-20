"""
AIAS Rate Limiter
Prevents brute force attacks, email spam, and abuse.
Uses database-backed sliding window rate limiting.
"""

from database.security import DatabaseSecurity
from config import Config


class RateLimiter:
    """Rate limiting for OTP requests and verification attempts."""

    @staticmethod
    def check_otp_request(email):
        """
        Check if the user can request a new OTP.

        Returns:
            dict with keys:
                - allowed (bool): Whether the request is allowed
                - error (str|None): Error message if blocked
                - wait_minutes (int): Minutes to wait if blocked
        """
        count = DatabaseSecurity.count_recent_events(email, "otp_request", minutes=60)

        if count >= Config.MAX_OTP_REQUESTS_PER_HOUR:
            return {
                "allowed": False,
                "error": f"Too many verification requests. Please wait before trying again.",
                "wait_minutes": 60,
            }

        return {"allowed": True, "error": None, "wait_minutes": 0}

    @staticmethod
    def log_otp_request(email):
        """Log an OTP request for rate tracking."""
        DatabaseSecurity.log_rate_event(email, "otp_request")

    @staticmethod
    def check_login_attempt(email):
        """
        Check if the user can attempt a login.

        Returns:
            dict with keys:
                - allowed (bool): Whether the attempt is allowed
                - error (str|None): Error message if blocked
        """
        count = DatabaseSecurity.count_recent_events(email, "failed_login", minutes=Config.LOCKOUT_DURATION_MINUTES)

        if count >= Config.MAX_FAILED_LOGINS:
            return {
                "allowed": False,
                "error": f"Account temporarily locked due to too many failed attempts. Please try again in {Config.LOCKOUT_DURATION_MINUTES} minutes.",
            }

        return {"allowed": True, "error": None}

    @staticmethod
    def log_failed_login(email):
        """Log a failed login attempt."""
        DatabaseSecurity.log_rate_event(email, "failed_login")

    @staticmethod
    def log_successful_login(email):
        """Log a successful login (for analytics, not rate limiting)."""
        DatabaseSecurity.log_rate_event(email, "successful_login")
