# Notification Service - Email, SMS, Push, WebSocket
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r notification && useradd -r -g notification notification

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install notification-specific packages
RUN pip install --no-cache-dir \
    celery[redis]==5.3.* \
    twilio==8.5.* \
    sendgrid==6.10.* \
    pyfcm==1.5.* \
    websockets==11.0.* \
    jinja2==3.1.*

FROM base as development
# Development stage
RUN pip install --no-cache-dir \
    pytest==7.4.* \
    pytest-asyncio==0.21.* \
    pytest-cov==4.1.* \
    black==23.7.* \
    flake8==6.0.*

FROM base as production
# Production stage
COPY --chown=notification:notification ./app /app
COPY --chown=notification:notification ./config /app/config
COPY --chown=notification:notification ./templates /app/templates

# Create necessary directories
RUN mkdir -p /app/logs && \
    chown -R notification:notification /app

# Switch to non-root user
USER notification

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8005/health || exit 1

# Expose port
EXPOSE 8005

# Environment variables
ENV PYTHONPATH=/app
ENV SERVICE_NAME=notification-service
ENV SERVICE_PORT=8005
ENV PYTHONUNBUFFERED=1

# Start command (includes both web server and WebSocket server)
CMD ["python", "-m", "uvicorn", "notification.main:app", "--host", "0.0.0.0", "--port", "8005", "--workers", "2"]