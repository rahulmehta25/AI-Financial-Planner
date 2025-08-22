# User Service - Authentication & Profile Management
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
RUN groupadd -r userservice && useradd -r -g userservice userservice

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install security-focused packages
RUN pip install --no-cache-dir \
    cryptography==41.0.* \
    bcrypt==4.0.* \
    passlib[bcrypt]==1.7.* \
    python-jose[cryptography]==3.3.* \
    python-multipart==0.0.*

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
COPY --chown=userservice:userservice ./app /app
COPY --chown=userservice:userservice ./config /app/config

# Create necessary directories
RUN mkdir -p /app/logs && \
    chown -R userservice:userservice /app

# Switch to non-root user
USER userservice

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Expose port
EXPOSE 8002

# Environment variables
ENV PYTHONPATH=/app
ENV SERVICE_NAME=user-service
ENV SERVICE_PORT=8002
ENV PYTHONUNBUFFERED=1

# Start command
CMD ["python", "-m", "uvicorn", "user.main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "4"]