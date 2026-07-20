# Banking Service - Plaid/Yodlee Integration
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
RUN groupadd -r banking && useradd -r -g banking banking

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install banking-specific packages
RUN pip install --no-cache-dir \
    plaid-python==9.1.* \
    cryptography==41.0.* \
    python-jose[cryptography]==3.3.*

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
COPY --chown=banking:banking ./app /app
COPY --chown=banking:banking ./config /app/config

# Create necessary directories
RUN mkdir -p /app/logs && \
    chown -R banking:banking /app

# Switch to non-root user
USER banking

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Expose port
EXPOSE 8003

# Environment variables
ENV PYTHONPATH=/app
ENV SERVICE_NAME=banking-service
ENV SERVICE_PORT=8003
ENV PYTHONUNBUFFERED=1

# Start command
CMD ["python", "-m", "uvicorn", "banking.main:app", "--host", "0.0.0.0", "--port", "8003", "--workers", "4"]