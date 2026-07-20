# Simulation Service - Monte Carlo Engine
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r simulation && useradd -r -g simulation simulation

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional packages for numerical computing
RUN pip install --no-cache-dir \
    numpy==1.24.* \
    scipy==1.10.* \
    numba==0.57.* \
    cupy-cuda11x==12.*

FROM base as development
# Development stage with additional tools
RUN pip install --no-cache-dir \
    pytest==7.4.* \
    pytest-asyncio==0.21.* \
    pytest-cov==4.1.* \
    black==23.7.* \
    flake8==6.0.*

FROM base as production
# Production stage
COPY --chown=simulation:simulation ./app /app
COPY --chown=simulation:simulation ./config /app/config

# Create necessary directories
RUN mkdir -p /app/logs /app/data && \
    chown -R simulation:simulation /app

# Switch to non-root user
USER simulation

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Expose port
EXPOSE 8001

# Environment variables
ENV PYTHONPATH=/app
ENV SERVICE_NAME=simulation-service
ENV SERVICE_PORT=8001
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0

# Start command
CMD ["python", "-m", "uvicorn", "simulation.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]