# ── Build Stage ──
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Production Stage ──
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=5000

# Security: run as non-root
RUN groupadd -g 1000 aias && useradd -u 1000 -g aias -d /app -s /sbin/nologin aias

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Set ownership
RUN chown -R aias:aias /app

# Switch to non-root user
USER aias

# Expose Flask port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.getenv('PORT', '5000'), timeout=4)" || exit 1

# Production entry: gunicorn (with database init pre-check logged but not hard-blocking)
CMD ["sh", "-c", "python -c 'from database.db import db_manager; res = db_manager.health_check(); print(\"[AIAS] Database check:\", res)' && exec python -m gunicorn --bind 0.0.0.0:${PORT:-5000} --workers ${WEB_CONCURRENCY:-4} --threads ${GUNICORN_THREADS:-2} --timeout ${GUNICORN_TIMEOUT:-120} --access-logfile - --error-logfile - 'app:create_app()'"]
