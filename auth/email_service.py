"""
AIAS Email Service
Sends OTP verification emails via Gmail SMTP over TLS.
Uses HTML templates for professional email appearance.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import Config


class EmailService:
    """Handles sending verification emails via Gmail SMTP."""

    @staticmethod
    def send_otp_email(recipient_email, otp_code, recipient_name=""):
        """
        Send a professional HTML verification email containing the OTP.

        Args:
            recipient_email: The email address to send to
            otp_code: The 6-digit OTP code (plaintext, for email body only)
            recipient_name: Optional display name for personalization

        Returns:
            dict with keys:
                - success (bool): Whether email was sent
                - error (str|None): Error message if failed
        """
        if not Config.MAIL_USERNAME or not Config.MAIL_PASSWORD:
            return {
                "success": False,
                "error": "Email service not configured. Please set MAIL_USERNAME and MAIL_PASSWORD in .env",
            }

        # Build the HTML email
        html_body = EmailService._build_otp_email_html(recipient_email, otp_code, recipient_name)

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"AIAS Verification Code: {otp_code}"
        msg["From"] = f"{Config.MAIL_SENDER_NAME} <{Config.MAIL_USERNAME}>"
        msg["To"] = recipient_email

        # Plain text fallback
        plain_text = (
            f"Your AIAS verification code is: {otp_code}\n\n"
            f"This code expires in {Config.OTP_EXPIRY_MINUTES} minutes.\n"
            f"If you didn't request this code, please ignore this email.\n"
        )

        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            # Connect via TLS
            context = ssl.create_default_context()
            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.sendmail(Config.MAIL_USERNAME, recipient_email, msg.as_string())

            return {"success": True, "error": None}

        except smtplib.SMTPAuthenticationError:
            return {
                "success": False,
                "error": "Email authentication failed. Check your Gmail App Password in .env",
            }
        except smtplib.SMTPException as e:
            return {"success": False, "error": f"Failed to send email: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Email service error: {str(e)}"}

    @staticmethod
    def _build_otp_email_html(recipient_email, otp_code, recipient_name=""):
        """Build the professional HTML email template matching Google style."""
        greeting = f"Dear {recipient_name}," if recipient_name else "Dear AIAS User,"

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 20px; font-family: Arial, sans-serif; background-color: #f9f9f9;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); overflow: hidden;">
        
        <!-- Logo Header -->
        <div style="padding: 32px 32px 8px 32px;">
            <span style="font-size: 24px; font-family: Georgia, 'Times New Roman', serif; color: #222222;">AIAS</span>
            <span style="font-size: 24px; font-family: Georgia, 'Times New Roman', serif; color: #c4a137;">Platform</span>
        </div>

        <!-- Title Header (No Blue Box) -->
        <div style="padding: 16px 32px; border-bottom: 1px solid #f0f0f0;">
            <h1 style="color: #222222; margin: 0; font-size: 24px; font-weight: 400;">Verification Code</h1>
        </div>

        <!-- Body Content -->
        <div style="padding: 32px;">
            <p style="font-size: 16px; color: #3c4043; margin-top: 0;">{greeting}</p>
            
            <p style="font-size: 16px; color: #3c4043; line-height: 1.5;">
                We received a request to access your AIAS Account <a href="mailto:{recipient_email}" style="color: #1a73e8; text-decoration: none;">{recipient_email}</a> through your email address. Your AIAS verification code is:
            </p>

            <h2 style="font-size: 36px; font-weight: 700; color: #202124; text-align: center; margin: 40px 0;">
                {otp_code}
            </h2>

            <p style="font-size: 14px; color: #3c4043; line-height: 1.5;">
                If you did not request this code, it is possible that someone else is trying to access the AIAS Account <a href="mailto:{recipient_email}" style="color: #1a73e8; text-decoration: none;">{recipient_email}</a>. <strong>Do not forward or give this code to anyone.</strong>
            </p>

            <p style="font-size: 14px; color: #3c4043; line-height: 1.5;">
                You received this message because this email address is listed as the recovery email for the AIAS Account <a href="mailto:{recipient_email}" style="color: #1a73e8; text-decoration: none;">{recipient_email}</a>.
            </p>

            <p style="font-size: 14px; color: #3c4043; line-height: 1.5; margin-bottom: 0;">
                Sincerely yours,<br><br>
                The AIAS Accounts team
            </p>
        </div>
    </div>
</body>
</html>
"""

    @staticmethod
    def send_welcome_email(recipient_email, recipient_name=""):
        """
        Send a welcome email every time a user logs in or signs up.

        Args:
            recipient_email: The email address to send to
            recipient_name: Optional display name for personalization

        Returns:
            dict with keys:
                - success (bool): Whether email was sent
                - error (str|None): Error message if failed
        """
        if not Config.MAIL_USERNAME or not Config.MAIL_PASSWORD:
            return {
                "success": False,
                "error": "Email service not configured.",
            }

        html_body = EmailService._build_welcome_email_html(recipient_email, recipient_name)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Welcome back to AIAS, {recipient_name or 'there'}!"
        msg["From"] = f"{Config.MAIL_SENDER_NAME} <{Config.MAIL_USERNAME}>"
        msg["To"] = recipient_email

        plain_text = (
            f"Welcome to AIAS, {recipient_name or 'there'}!\n\n"
            f"You've successfully signed in to your AIAS account.\n"
            f"We're building the future of intelligent business automation — and you're part of it.\n\n"
            f"— The AIAS Team\n"
        )

        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.sendmail(Config.MAIL_USERNAME, recipient_email, msg.as_string())

            return {"success": True, "error": None}

        except Exception as e:
            return {"success": False, "error": f"Welcome email error: {str(e)}"}

    @staticmethod
    def _build_welcome_email_html(recipient_email, recipient_name=""):
        """Build the welcome email HTML template matching the AIAS design."""
        greeting = f"Hi {recipient_name}," if recipient_name else "Hi there,"

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 20px; font-family: Arial, sans-serif; background-color: #f9f9f9;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); overflow: hidden;">
        
        <!-- Logo Header -->
        <div style="padding: 32px 32px 8px 32px;">
            <span style="font-size: 24px; font-family: Georgia, 'Times New Roman', serif; color: #222222;">AIAS</span>
            <span style="font-size: 24px; font-family: Georgia, 'Times New Roman', serif; color: #c4a137;">Platform</span>
        </div>

        <!-- Title -->
        <div style="padding: 16px 32px; border-bottom: 1px solid #f0f0f0;">
            <h1 style="color: #222222; margin: 0; font-size: 24px; font-weight: 400;">Welcome Back</h1>
        </div>

        <!-- Body Content -->
        <div style="padding: 32px;">
            <p style="font-size: 16px; color: #3c4043; margin-top: 0;">{greeting}</p>
            
            <p style="font-size: 16px; color: #3c4043; line-height: 1.6;">
                You've successfully signed in to your AIAS account. We're glad to have you here.
            </p>

            <!-- Highlight Box -->
            <div style="background-color: #fdf8ef; border-left: 4px solid #c4a137; padding: 20px 24px; margin: 28px 0; border-radius: 0 8px 8px 0;">
                <p style="font-size: 15px; color: #222222; margin: 0; font-weight: 600; line-height: 1.5;">
                    At AIAS, we're building the future of intelligent business automation.
                </p>
                <p style="font-size: 14px; color: #555555; margin: 10px 0 0 0; line-height: 1.5;">
                    From AI-powered workflows to real-time decision making — you now have access to enterprise-grade tools designed to help your business move faster and smarter.
                </p>
            </div>

            <p style="font-size: 15px; color: #3c4043; line-height: 1.6;">
                Here's what you can do today:
            </p>

            <!-- Feature List -->
            <table style="width: 100%; margin: 16px 0 28px 0; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px 12px 10px 0; vertical-align: top; width: 28px;">
                        <span style="color: #c4a137; font-size: 18px; font-weight: 700;">&#10003;</span>
                    </td>
                    <td style="padding: 10px 0; font-size: 14px; color: #3c4043; line-height: 1.5;">
                        <strong>Automate Workflows</strong> — Set up intelligent automation pipelines in minutes.
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px 12px 10px 0; vertical-align: top; width: 28px;">
                        <span style="color: #c4a137; font-size: 18px; font-weight: 700;">&#10003;</span>
                    </td>
                    <td style="padding: 10px 0; font-size: 14px; color: #3c4043; line-height: 1.5;">
                        <strong>AI-Powered Insights</strong> — Get real-time analytics and predictive intelligence.
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px 12px 10px 0; vertical-align: top; width: 28px;">
                        <span style="color: #c4a137; font-size: 18px; font-weight: 700;">&#10003;</span>
                    </td>
                    <td style="padding: 10px 0; font-size: 14px; color: #3c4043; line-height: 1.5;">
                        <strong>Scale with Confidence</strong> — Enterprise-grade security and infrastructure that grows with you.
                    </td>
                </tr>
            </table>

            <p style="font-size: 14px; color: #3c4043; line-height: 1.5;">
                You're now part of a growing community of businesses that are choosing intelligence over complexity. We're excited to have you on this journey.
            </p>

            <p style="font-size: 14px; color: #3c4043; line-height: 1.5; margin-bottom: 0;">
                Welcome aboard,<br><br>
                <strong>The AIAS Team</strong><br>
                <span style="font-size: 13px; color: #888888; font-style: italic;">Building the future of intelligent business.</span>
            </p>
        </div>

        <!-- Footer -->
        <div style="padding: 20px 32px; background-color: #fafafa; border-top: 1px solid #f0f0f0; text-align: center;">
            <p style="font-size: 12px; color: #999999; margin: 0; line-height: 1.5;">
                This email was sent to <a href="mailto:{recipient_email}" style="color: #c4a137; text-decoration: none;">{recipient_email}</a> because you signed in to your AIAS account.
            </p>
        </div>
    </div>
</body>
</html>
"""

    @staticmethod
    def send_booking_notification(name="N/A", email="N/A", whatsapp="", service_needed="N/A",
                                  budget_range="N/A", timeline="N/A", problem_statement="",
                                  timestamp=""):
        """
        Send an internal booking notification to the AIAS team email
        whenever a user books a call via the chatbot.
        """
        if not Config.MAIL_USERNAME or not Config.MAIL_PASSWORD:
            return {"success": False, "error": "Email service not configured."}

        TEAM_EMAIL = "aiasprivateltd@gmail.com"

        # Build rows for the details table
        rows = [
            ("Name", name, True),
            ("Email", email, False),
            ("WhatsApp", whatsapp or "Not provided", True),
            ("Service Needed", service_needed, False),
            ("Budget Range", budget_range, True),
            ("Timeline", timeline, False),
            ("Problem Statement", problem_statement or "Not provided", True),
            ("Submitted At", timestamp, False),
        ]
        table_rows = ""
        for i, (label, value, shaded) in enumerate(rows):
            bg = ' style="background:#fdf8ef;"' if shaded else ""
            table_rows += f"""
        <tr{bg}>
          <td style="padding:12px 16px;font-size:13px;color:#888;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;width:160px;border-bottom:1px solid #f0f0f0;">{label}</td>
          <td style="padding:12px 16px;font-size:15px;color:#1a1a1a;{'font-weight:600;' if i == 0 else ''}border-bottom:1px solid #f0f0f0;">{value}</td>
        </tr>"""

        html_body = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:20px;font-family:Arial,sans-serif;background:#f9f9f9;">
  <div style="max-width:600px;margin:0 auto;background:#ffffff;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;">

    <!-- Header -->
    <div style="padding:28px 32px 8px 32px;">
      <span style="font-size:22px;font-family:Georgia,serif;color:#222;">AIAS</span>
      <span style="font-size:22px;font-family:Georgia,serif;color:#c4a137;">Platform</span>
    </div>
    <div style="padding:14px 32px;border-bottom:1px solid #f0f0f0;">
      <h1 style="color:#222;margin:0;font-size:22px;font-weight:400;">📅 New Call Booking</h1>
    </div>

    <!-- Body -->
    <div style="padding:28px 32px;">
      <p style="font-size:15px;color:#3c4043;margin:0 0 20px;">A new lead has booked a call through the AIAS website chatbot. Here are their details:</p>

      <table style="width:100%;border-collapse:collapse;margin-bottom:24px;">
        {table_rows}
      </table>

      <div style="background:#fdf8ef;border-left:4px solid #c4a137;padding:16px 20px;border-radius:0 8px 8px 0;margin-bottom:20px;">
        <p style="font-size:14px;color:#222;margin:0;font-weight:600;">Action Required</p>
        <p style="font-size:13px;color:#555;margin:8px 0 0;">Contact this lead within <strong>24 working hours</strong>. Reply to <strong>{email}</strong>{f' or WhatsApp <strong>{whatsapp}</strong>' if whatsapp else ''}.</p>
      </div>

      <p style="font-size:13px;color:#888;margin:0;">This notification was sent automatically by the AIAS chatbot system.</p>
    </div>

    <!-- Footer -->
    <div style="padding:16px 32px;background:#fafafa;border-top:1px solid #f0f0f0;text-align:center;">
      <p style="font-size:12px;color:#999;margin:0;">AIAS Platform · aiasprivateltd@gmail.com · +91 7022756962</p>
    </div>
  </div>
</body>
</html>
"""

        plain = (
            f"NEW CALL BOOKING — AIAS Platform\n\n"
            f"Name             : {name}\n"
            f"Email            : {email}\n"
            f"WhatsApp         : {whatsapp or 'Not provided'}\n"
            f"Service Needed   : {service_needed}\n"
            f"Budget Range     : {budget_range}\n"
            f"Timeline         : {timeline}\n"
            f"Problem          : {problem_statement or 'Not provided'}\n"
            f"Submitted        : {timestamp}\n\n"
            f"Contact within 24 working hours.\n"
        )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"📅 New Call Booking: {name} — {service_needed}"
        msg["From"] = f"{Config.MAIL_SENDER_NAME} <{Config.MAIL_USERNAME}>"
        msg["To"] = TEAM_EMAIL
        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.sendmail(Config.MAIL_USERNAME, TEAM_EMAIL, msg.as_string())
            return {"success": True, "error": None}
        except Exception as e:
            return {"success": False, "error": str(e)}
