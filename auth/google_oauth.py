"""
AIAS Google OAuth 2.0
Handles 'Sign in with Google' using authlib.
"""

from authlib.integrations.flask_client import OAuth

from config import Config

# OAuth instance (initialized in app.py)
oauth = OAuth()


def init_google_oauth(app):
    """Initialize Google OAuth with the Flask app."""
    oauth.init_app(app)

    oauth.register(
        name="google",
        client_id=Config.GOOGLE_CLIENT_ID,
        client_secret=Config.GOOGLE_CLIENT_SECRET,
        server_metadata_url=Config.GOOGLE_DISCOVERY_URL,
        client_kwargs={
            "scope": "openid email profile",
        },
    )


def get_google_client():
    """Get the Google OAuth client."""
    return oauth.google
