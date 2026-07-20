# ML Service - Machine Learning & Recommendations
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    libblas3 \
    liblapack3 \
    libopenblas-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r mlservice && useradd -r -g mlservice mlservice

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install ML-specific packages
RUN pip install --no-cache-dir \
    scikit-learn==1.3.* \
    pandas==2.0.* \
    numpy==1.24.* \
    scipy==1.10.* \
    joblib==1.3.* \
    xgboost==1.7.* \
    lightgbm==4.0.* \
    optuna==3.3.* \
    mlflow==2.6.*

FROM base as development
# Development stage with additional ML tools
RUN pip install --no-cache-dir \
    jupyter==1.0.* \
    matplotlib==3.7.* \
    seaborn==0.12.* \
    plotly==5.15.* \
    pytest==7.4.* \
    pytest-asyncio==0.21.* \
    pytest-cov==4.1.* \
    black==23.7.* \
    flake8==6.0.*

FROM base as production
# Production stage
COPY --chown=mlservice:mlservice ./app /app
COPY --chown=mlservice:mlservice ./config /app/config
COPY --chown=mlservice:mlservice ./models /app/models

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/artifacts && \
    chown -R mlservice:mlservice /app

# Switch to non-root user
USER mlservice

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

# Expose port
EXPOSE 8004

# Environment variables
ENV PYTHONPATH=/app
ENV SERVICE_NAME=ml-service
ENV SERVICE_PORT=8004
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=""

# Start command
CMD ["python", "-m", "uvicorn", "ml.main:app", "--host", "0.0.0.0", "--port", "8004", "--workers", "2"]