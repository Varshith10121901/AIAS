# AIAS - Business Lead Management Platform

AIAS is a modern platform that helps businesses connect with potential clients and manage lead qualification seamlessly. The platform features secure authentication, an intelligent Aria chatbot for lead capture, and booking management for consultations.

## Key Features

- **Secure Sign-In & Registration** - Safe account creation with email verification and password security
- **Flexible Authentication** - Sign in with email/password or Google account
- **Aria Chatbot** - Intelligent chatbot to qualify leads and capture essential information
- **Booking Management** - Schedule and manage consultations with built-in calendar integration
- **Professional Notifications** - Automated email updates for users and administrators
- **Admin Dashboard** - Centralized management of leads, bookings, and user activities
- **Video Consultations** - Support for video calls through Zoom integration

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Docker and Docker Compose (for containerized deployment)
- Environment configuration file (`.env`)

### Quick Start - Local Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration values
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Access the platform:
   ```
   http://localhost:5000
   ```

### Quick Start - Docker Deployment

1. Build and start the containers:
   ```bash
   docker compose up --build
   ```

2. Access the platform:
   ```
   http://localhost:5000
   ```

## Configuration

The platform requires configuration through a `.env` file. Key configuration areas include:
- Application settings and security keys
- Database connection credentials
- Email service configuration
- Social authentication (Google OAuth)
- Video meeting service (Zoom)

**Important:** Never commit the `.env` file to version control. Keep your configuration secure and local.

## Support & Documentation

For additional documentation and implementation details, refer to:
- `information.md` - Detailed technical documentation
- `.env.example` - Configuration template with all required variables
