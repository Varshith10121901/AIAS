"""
AIAS — Main Flask Application
Entry point for the Sign-In & Verification System.
"""

import os
import sys
import secrets
from datetime import timedelta

from flask import Flask, redirect, render_template, request, jsonify, session as flask_session, url_for
from flask_wtf.csrf import CSRFProtect

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from auth.routes import auth_bp, init_bcrypt
from auth.google_oauth import init_google_oauth
from database.db import Database
from database.security import DatabaseSecurity


def create_app():
    """Application factory."""
    app = Flask(__name__)

    # ── Configuration ──
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=Config.SESSION_LIFETIME_HOURS)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    if Config.FLASK_ENV != "development":
        app.config["SESSION_COOKIE_SECURE"] = True
    app.config["WTF_CSRF_TIME_LIMIT"] = 3600  # 1 hour CSRF token validity

    # ── Security: CSRF Protection ──
    csrf = CSRFProtect(app)

    # ── Initialize Extensions ──
    init_bcrypt(app)

    # ── Google OAuth (only if configured) ──
    if Config.GOOGLE_CLIENT_ID and not Config.GOOGLE_CLIENT_ID.startswith("YOUR_"):
        init_google_oauth(app)

    # ── Initialize Database ──
    db = Database()

    # ── Register Blueprints ──
    app.register_blueprint(auth_bp)

    # ── Root Route: Serve Homepage ──
    @app.route("/")
    def index():
        return render_template(
            "homepage.html",
            logged_in="user_id" in flask_session,
            user_name=flask_session.get("user_name", ""),
            user_email=flask_session.get("user_email", ""),
        )

    # ── Admin Dashboard ──
    ADMIN_EMAILS = {"aiasprivateltd@gmail.com", "varshithkumar815@gmail.com"}

    @app.route("/admin")
    def admin_dashboard():
        """Admin dashboard — only accessible to admin emails."""
        # Check if logged in
        if "user_id" not in flask_session:
            return redirect(url_for("auth.signin"))

        # Check if admin
        user_email = flask_session.get("user_email", "").lower().strip()
        if user_email not in ADMIN_EMAILS:
            return redirect(url_for("index"))

        # Fetch all data from database
        try:
            users = db.execute("SELECT * FROM users ORDER BY created_at DESC", fetch_all=True) or []
            bookings = db.execute("SELECT * FROM bookings ORDER BY created_at DESC", fetch_all=True) or []
            sessions_data = db.execute("SELECT * FROM sessions WHERE expires_at > datetime('now')", fetch_all=True) or []
            otps = db.execute("SELECT * FROM otp_codes", fetch_all=True) or []
            rate_logs = db.execute("SELECT * FROM rate_limit_log ORDER BY created_at DESC LIMIT 100", fetch_all=True) or []
        except Exception:
            users, bookings, sessions_data, otps, rate_logs = [], [], [], [], []

        # Compute stats
        total_users = len(users)
        verified_users = sum(1 for u in users if u["is_verified"])
        google_users = sum(1 for u in users if u["is_google_user"])
        total_bookings = len(bookings)
        booked_count = sum(1 for b in bookings if b["lead_status"] == "booked")
        new_count = sum(1 for b in bookings if b["lead_status"] == "new")
        active_sessions = len(sessions_data)
        total_otps = len(otps)
        bookings_with_problems = [b for b in bookings if b["problem_statement"] and b["problem_statement"].strip()]

        return render_template(
            "admin.html",
            admin_email=user_email,
            users=users,
            bookings=bookings,
            bookings_with_problems=bookings_with_problems,
            rate_logs=rate_logs,
            total_users=total_users,
            verified_users=verified_users,
            google_users=google_users,
            total_bookings=total_bookings,
            booked_count=booked_count,
            new_count=new_count,
            active_sessions=active_sessions,
            total_otps=total_otps,
        )

    # ── Book-a-Call Endpoint (exempt from CSRF — called via chatbot fetch) ──
    @app.route("/book-call", methods=["POST"])
    @csrf.exempt
    def book_call():
        """Receive lead data from chatbot, save to DB, and send email notification."""
        try:
            data = request.get_json(force=True) or {}
            name              = data.get("name", "N/A")
            email             = data.get("email", "N/A")
            whatsapp          = data.get("whatsapp", "")
            service_needed    = data.get("service_needed", "N/A")
            budget_range      = data.get("budget_range", "N/A")
            timeline          = data.get("timeline", "N/A")
            problem_statement = data.get("problem_statement", "")
            source            = data.get("source", "website")
            lead_status       = data.get("lead_status", "new")
            ts                = data.get("timestamp", "N/A")

            # Save to database
            try:
                db.execute(
                    """INSERT INTO bookings
                       (name, email, whatsapp, service_needed, budget_range, timeline, problem_statement, source, lead_status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (name, email, whatsapp, service_needed, budget_range, timeline, problem_statement, source, lead_status)
                )
            except Exception:
                pass  # DB write failure shouldn't break the response

            # Send email notification to team
            try:
                from auth.email_service import EmailService
                EmailService.send_booking_notification(
                    name=name,
                    email=email,
                    whatsapp=whatsapp,
                    service_needed=service_needed,
                    budget_range=budget_range,
                    timeline=timeline,
                    problem_statement=problem_statement,
                    timestamp=ts
                )
            except Exception:
                pass  # Email failure shouldn't break the response

        except Exception:
            pass  # Never fail the frontend
        return jsonify({"success": True})

    # ── Cleanup Task (runs on each request, lightweight) ──
    @app.before_request
    def before_request():
        """Periodic cleanup of expired data."""
        # Run cleanup roughly every 100th request (probabilistic)
        if secrets.randbelow(100) == 0:
            try:
                DatabaseSecurity.cleanup_all()
            except Exception:
                pass  # Don't break requests on cleanup failure

    # ── Error Handlers ──
    @app.errorhandler(404)
    def not_found(e):
        return redirect(url_for("auth.signin"))

    @app.errorhandler(500)
    def server_error(e):
        return "Internal server error", 500

    return app


# ── Run ──
if __name__ == "__main__":
    app = create_app()
    print("\n" + "=" * 56)
    print("  [AIAS] Platform")
    print("  -> http://localhost:5000/")
    print("  -> http://localhost:5000/signin")
    print("  -> http://localhost:5000/register")
    print("=" * 56 + "\n")
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=(Config.FLASK_ENV == "development"),
    )
