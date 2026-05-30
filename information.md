# AIAS Project Information

This document provides a high-level overview of the AIAS platform and its key components.

## 1. Project Summary

AIAS is a business lead management platform that includes:

- User registration and secure sign-in
- Password reset with verification
- Google account integration
- Aria chatbot for lead qualification
- Booking management for consultations
- Email notifications
- Admin dashboard for managing leads and bookings
- Database persistence
- Caching and performance optimization
- Docker deployment

## 2. Main Technology Stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.12, Flask |
| Authentication | Bcrypt, CSRF Protection, OAuth |
| Database | MongoDB Atlas |
| Caching | Redis |
| Email | Gmail SMTP |
| Video Integration | Zoom |
| Frontend | HTML, CSS, JavaScript |
| Deployment | Docker, Docker Compose |

## 3. Key Features

- **Secure Authentication**: Email/password and Google OAuth sign-in
- **Lead Qualification**: Aria chatbot for capturing lead information
- **Booking Management**: Track and schedule consultations
- **Admin Dashboard**: Centralized management interface
- **Email Notifications**: Automated communications with leads and team
- **Video Consultations**: Zoom meeting integration for calls
- **Rate Limiting**: Protection against abuse and brute force attempts
- **Session Management**: Secure user sessions with caching

## 4. Core Components

The application consists of several main modules:

- **Authentication Module**: Handles user registration, sign-in, and password reset
- **Booking Module**: Manages lead capture and consultation scheduling
- **Admin Module**: Provides administrative operations and dashboards
- **Database Layer**: Manages data persistence and model operations
- **Cache Layer**: Handles session caching and rate limiting
- **Email Service**: Sends notifications and verification emails

## 5. High-Level Architecture

The platform follows a layered architecture:

```
Client → Web Interface → Flask App → Database/Cache/External Services
```

Key integration points:

- **Gmail SMTP**: For sending verification and notification emails
- **Zoom API**: For creating video meeting links
- **Google OAuth**: For social login
- **MongoDB**: For data persistence
- **Redis**: For caching and session management

## 6. Deployment

### Local Development

The application can be run locally using Python:

1. Set up a virtual environment
2. Install dependencies from requirements.txt
3. Configure environment variables
4. Run the Flask application

### Docker Deployment

For production, the application is containerized with:

- **Web Container**: Runs the Flask application
- **Redis Container**: Provides caching and session support

Both containers are orchestrated using Docker Compose.

## 7. Configuration

The platform requires configuration through environment variables for:

- Flask application settings
- Database connection credentials
- Email service configuration
- OAuth credentials (Google, Zoom)
- Security settings
- Performance tuning

Configuration must be stored securely and never committed to version control.

## 8. Admin Operations

The admin dashboard allows administrators to:

- View and manage user accounts
- Monitor leads and bookings
- Schedule consultations with clients
- Send notifications and communications
- Access system metrics and logs
- Manage cache and performance settings

Admin access is restricted to authenticated users with administrative privileges.

## 9. Security Considerations

The platform implements multiple security layers:

- Session-based authentication with token validation
- Password hashing and encryption
- CSRF protection on forms
- HTTP-only session cookies
- Account lockout after failed login attempts
- OTP verification for sensitive operations
- Rate limiting to prevent abuse
- Input validation and sanitization

Admin features require proper authentication to prevent unauthorized access.

## 10. Monitoring and Health Checks

The application includes health checks for:

- Database connectivity
- Cache availability
- Email service status
- API endpoint responsiveness

These checks ensure the platform is operating correctly in production.

## 11. Next Steps for Production

Before deploying to production, ensure:

- All credentials are stored securely
- HTTPS is enabled
- Database backups are configured
- Monitoring and logging are in place
- Security policies are enforced
- Load testing has been performed
- Disaster recovery procedures are documented
