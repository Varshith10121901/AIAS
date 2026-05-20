"""
AIAS Configuration Module
Loads environment variables and provides app-wide settings.
"""

import os
import secrets
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Determine environment
flask_env = os.getenv("FLASK_ENV", "production")

# Required for local OAuth over HTTP (not HTTPS)
if flask_env == "development":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


class Config:
    """Base configuration."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))
    FLASK_ENV = os.getenv("FLASK_ENV", "production")

    # Database
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "aias.db")

    # Email (Gmail SMTP)
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_SENDER_NAME = "AIAS Security"

    # OTP Settings
    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 5
    OTP_MAX_ATTEMPTS = 5

    # Rate Limiting
    MAX_OTP_REQUESTS_PER_HOUR = 5
    LOCKOUT_DURATION_MINUTES = 15
    MAX_FAILED_LOGINS = 5

    # Session
    SESSION_LIFETIME_HOURS = 24
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")

    # Security Headers
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
