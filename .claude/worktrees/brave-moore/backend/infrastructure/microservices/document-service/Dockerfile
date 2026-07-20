# Document Service - PDF Generation & Document Management
FROM python:3.11-slim as base

# Install system dependencies for PDF generation
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    wkhtmltopdf \
    xvfb \
    libfontconfig1 \
    libxrender1 \
    libxtst6 \
    fonts-dejavu \
    fonts-liberation \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r document && useradd -r -g document document

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install document-specific packages
RUN pip install --no-cache-dir \
    reportlab==4.0.* \
    weasyprint==60.0.* \
    pdfkit==1.0.* \
    jinja2==3.1.* \
    matplotlib==3.7.* \
    pillow==10.0.*

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
COPY --chown=document:document ./app /app
COPY --chown=document:document ./config /app/config
COPY --chown=document:document ./templates /app/templates
COPY --chown=document:document ./fonts /app/fonts

# Create necessary directories
RUN mkdir -p /app/logs /app/generated /app/temp && \
    chown -R document:document /app

# Switch to non-root user
USER document

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8006/health || exit 1

# Expose port
EXPOSE 8006

# Environment variables
ENV PYTHONPATH=/app
ENV SERVICE_NAME=document-service
ENV SERVICE_PORT=8006
ENV PYTHONUNBUFFERED=1
ENV QT_QPA_PLATFORM=offscreen

# Start command
CMD ["python", "-m", "uvicorn", "document.main:app", "--host", "0.0.0.0", "--port", "8006", "--workers", "2"]