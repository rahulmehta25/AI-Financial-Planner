#!/bin/bash

# Financial Planning Demo - Docker Distribution Creator
# Creates Docker images and orchestration files for easy deployment
# Author: Financial Planning Team

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VERSION=$(cat "$SCRIPT_DIR/VERSION" 2>/dev/null || echo "1.0.0")
BUILD_DATE=$(date +%Y%m%d)
DIST_DIR="$PROJECT_ROOT/dist"
DOCKER_DIR="$DIST_DIR/docker"
IMAGE_NAME="financial-planning-demo"
REGISTRY_PREFIX="demo"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"; }
success() { echo -e "${GREEN}✓ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
error() { echo -e "${RED}✗ $1${NC}"; exit 1; }

# Create Docker build directory
create_docker_directory() {
    log "Creating Docker distribution directory..."
    
    mkdir -p "$DOCKER_DIR"/{images,compose,kubernetes,scripts}
    
    success "Docker directory structure created"
}

# Create optimized Dockerfile for demo
create_demo_dockerfile() {
    log "Creating demo Dockerfile..."
    
    cat > "$DOCKER_DIR/images/Dockerfile.demo" << 'EOF'
# Financial Planning Demo - Optimized Docker Image
# Multi-stage build for minimal production image

# Build stage
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements_demo.txt .
RUN pip install --user --no-cache-dir -r requirements_demo.txt

# Production stage
FROM python:3.11-slim AS production

# Create non-root user
RUN groupadd -r demo && useradd -r -g demo demo

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /home/demo/.local

# Set up application directory
WORKDIR /app
RUN chown demo:demo /app

# Copy application files
COPY --chown=demo:demo backend/app/ ./app/
COPY --chown=demo:demo backend/minimal_working_demo.py .
COPY --chown=demo:demo backend/ml_simulation_demo.py .
COPY --chown=demo:demo backend/working_demo.py .
COPY --chown=demo:demo backend/demo_data/ ./demo_data/
COPY --chown=demo:demo backend/.env.example .env

# Set environment variables
ENV PYTHONPATH=/app
ENV PATH=/home/demo/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV DEMO_MODE=true
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

# Switch to non-root user
USER demo

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "minimal_working_demo.py"]
EOF

    success "Demo Dockerfile created"
}

# Create development Dockerfile
create_dev_dockerfile() {
    log "Creating development Dockerfile..."
    
    cat > "$DOCKER_DIR/images/Dockerfile.dev" << 'EOF'
# Financial Planning Demo - Development Docker Image
# Includes development tools and full feature set

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    vim \
    htop \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create development user
RUN groupadd -r devuser && useradd -r -g devuser -s /bin/bash devuser
RUN mkdir -p /home/devuser && chown devuser:devuser /home/devuser

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt backend/requirements_demo.txt ./
RUN pip install --no-cache-dir -r requirements.txt || \
    pip install --no-cache-dir -r requirements_demo.txt

# Copy application files
COPY backend/ .

# Set up environment
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DEBUG=true
ENV DEMO_MODE=true

# Development tools setup
RUN pip install --no-cache-dir ipython jupyter pytest-cov black isort flake8

# Create directories for development
RUN mkdir -p logs outputs data && \
    chown -R devuser:devuser /app

USER devuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000 8888

# Default to development server
CMD ["python", "working_demo.py"]
EOF

    success "Development Dockerfile created"
}

# Create full-stack Dockerfile
create_fullstack_dockerfile() {
    log "Creating full-stack Dockerfile..."
    
    cat > "$DOCKER_DIR/images/Dockerfile.fullstack" << 'EOF'
# Financial Planning Demo - Full Stack Image
# Includes both backend and frontend components

# Node.js build stage for frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /frontend

# Copy frontend package files
COPY frontend/package*.json ./
RUN npm ci --only=production

# Copy frontend source and build
COPY frontend/ .
RUN npm run build

# Python backend stage
FROM python:3.11-slim AS backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN groupadd -r app && useradd -r -g app app

WORKDIR /app

# Install Python dependencies
COPY backend/requirements_demo.txt .
RUN pip install --no-cache-dir -r requirements_demo.txt

# Copy backend files
COPY --chown=app:app backend/app/ ./app/
COPY --chown=app:app backend/minimal_working_demo.py .
COPY --chown=app:app backend/demo_data/ ./demo_data/
COPY --chown=app:app backend/.env.example .env

# Copy frontend build
COPY --from=frontend-builder /frontend/dist /var/www/html

# Configure nginx
COPY docker/nginx.conf /etc/nginx/nginx.conf

# Set up startup script
COPY docker/start-fullstack.sh /start-fullstack.sh
RUN chmod +x /start-fullstack.sh

# Set environment
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DEMO_MODE=true

USER app

EXPOSE 80 8000

CMD ["/start-fullstack.sh"]
EOF

    success "Full-stack Dockerfile created"
}

# Create Docker Compose configurations
create_docker_compose() {
    log "Creating Docker Compose configurations..."
    
    # Basic demo compose
    cat > "$DOCKER_DIR/compose/docker-compose.demo.yml" << 'EOF'
version: '3.8'

services:
  financial-planning-demo:
    build:
      context: ../../
      dockerfile: dist/docker/images/Dockerfile.demo
    container_name: fp-demo
    ports:
      - "8000:8000"
    environment:
      - DEMO_MODE=true
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - DATABASE_URL=sqlite:///./demo_data/financial_data.db
    volumes:
      - demo_data:/app/demo_data
      - demo_logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  demo_data:
  demo_logs:

networks:
  default:
    name: financial-planning-demo
EOF

    # Development compose with services
    cat > "$DOCKER_DIR/compose/docker-compose.dev.yml" << 'EOF'
version: '3.8'

services:
  financial-planning-demo:
    build:
      context: ../../
      dockerfile: dist/docker/images/Dockerfile.dev
    container_name: fp-demo-dev
    ports:
      - "8000:8000"
      - "8888:8888"  # Jupyter
    environment:
      - DEBUG=true
      - DEMO_MODE=true
      - DATABASE_URL=postgresql://demo:demo@postgres:5432/financial_planning
      - REDIS_URL=redis://redis:6379
    volumes:
      - ../../backend:/app
      - dev_data:/app/data
      - dev_logs:/app/logs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    container_name: fp-demo-postgres
    environment:
      - POSTGRES_USER=demo
      - POSTGRES_PASSWORD=demo
      - POSTGRES_DB=financial_planning
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: fp-demo-redis
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    container_name: fp-demo-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: fp-demo-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=demo
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana-datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml
    restart: unless-stopped

volumes:
  dev_data:
  dev_logs:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  default:
    name: financial-planning-dev
EOF

    # Production-like compose
    cat > "$DOCKER_DIR/compose/docker-compose.prod.yml" << 'EOF'
version: '3.8'

services:
  financial-planning-demo:
    build:
      context: ../../
      dockerfile: dist/docker/images/Dockerfile.demo
    container_name: fp-demo-prod
    ports:
      - "8000:8000"
    environment:
      - DEMO_MODE=true
      - API_HOST=0.0.0.0
      - DATABASE_URL=postgresql://demo:${POSTGRES_PASSWORD}@postgres:5432/financial_planning
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - app_data:/app/demo_data
      - app_logs:/app/logs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  postgres:
    image: postgres:15-alpine
    container_name: fp-demo-postgres-prod
    environment:
      - POSTGRES_USER=demo
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=financial_planning
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 512M

  redis:
    image: redis:7-alpine
    container_name: fp-demo-redis-prod
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 128M

  nginx:
    image: nginx:alpine
    container_name: fp-demo-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - nginx_logs:/var/log/nginx
    depends_on:
      - financial-planning-demo
    restart: unless-stopped

volumes:
  app_data:
  app_logs:
  postgres_data:
  redis_data:
  nginx_logs:

networks:
  default:
    name: financial-planning-prod

secrets:
  postgres_password:
    external: true
  secret_key:
    external: true
EOF

    success "Docker Compose configurations created"
}

# Create Kubernetes manifests
create_kubernetes_manifests() {
    log "Creating Kubernetes manifests..."
    
    mkdir -p "$DOCKER_DIR/kubernetes"/{base,overlays}/{demo,dev,prod}
    
    # Base deployment
    cat > "$DOCKER_DIR/kubernetes/base/deployment.yml" << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: financial-planning-demo
  labels:
    app: financial-planning-demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: financial-planning-demo
  template:
    metadata:
      labels:
        app: financial-planning-demo
    spec:
      containers:
      - name: demo
        image: financial-planning-demo:latest
        ports:
        - containerPort: 8000
        env:
        - name: DEMO_MODE
          value: "true"
        - name: API_HOST
          value: "0.0.0.0"
        - name: API_PORT
          value: "8000"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        volumeMounts:
        - name: demo-data
          mountPath: /app/demo_data
        - name: demo-logs
          mountPath: /app/logs
      volumes:
      - name: demo-data
        persistentVolumeClaim:
          claimName: demo-data-pvc
      - name: demo-logs
        persistentVolumeClaim:
          claimName: demo-logs-pvc
EOF

    # Service
    cat > "$DOCKER_DIR/kubernetes/base/service.yml" << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: financial-planning-demo-service
  labels:
    app: financial-planning-demo
spec:
  selector:
    app: financial-planning-demo
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
EOF

    # PVC
    cat > "$DOCKER_DIR/kubernetes/base/pvc.yml" << 'EOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: demo-data-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: demo-logs-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF

    # Demo ingress
    cat > "$DOCKER_DIR/kubernetes/overlays/demo/ingress.yml" << 'EOF'
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: financial-planning-demo-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
spec:
  rules:
  - host: demo.financial-planning.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: financial-planning-demo-service
            port:
              number: 80
EOF

    success "Kubernetes manifests created"
}

# Create Docker helper scripts
create_docker_scripts() {
    log "Creating Docker helper scripts..."
    
    # Build script
    cat > "$DOCKER_DIR/scripts/build.sh" << 'EOF'
#!/bin/bash

# Financial Planning Demo - Docker Build Script
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$(dirname "$DOCKER_DIR")")"

VERSION=${1:-latest}
BUILD_TYPE=${2:-demo}

echo "Building Financial Planning Demo Docker Images"
echo "=============================================="
echo "Version: $VERSION"
echo "Build Type: $BUILD_TYPE"
echo ""

cd "$PROJECT_ROOT"

case $BUILD_TYPE in
    "demo")
        echo "Building demo image..."
        docker build -f "$DOCKER_DIR/images/Dockerfile.demo" -t "financial-planning-demo:$VERSION" .
        docker tag "financial-planning-demo:$VERSION" "financial-planning-demo:latest"
        ;;
    "dev")
        echo "Building development image..."
        docker build -f "$DOCKER_DIR/images/Dockerfile.dev" -t "financial-planning-demo:$VERSION-dev" .
        docker tag "financial-planning-demo:$VERSION-dev" "financial-planning-demo:dev"
        ;;
    "fullstack")
        echo "Building full-stack image..."
        docker build -f "$DOCKER_DIR/images/Dockerfile.fullstack" -t "financial-planning-demo:$VERSION-fullstack" .
        docker tag "financial-planning-demo:$VERSION-fullstack" "financial-planning-demo:fullstack"
        ;;
    "all")
        echo "Building all images..."
        docker build -f "$DOCKER_DIR/images/Dockerfile.demo" -t "financial-planning-demo:$VERSION" .
        docker build -f "$DOCKER_DIR/images/Dockerfile.dev" -t "financial-planning-demo:$VERSION-dev" .
        docker build -f "$DOCKER_DIR/images/Dockerfile.fullstack" -t "financial-planning-demo:$VERSION-fullstack" .
        
        # Tag latest versions
        docker tag "financial-planning-demo:$VERSION" "financial-planning-demo:latest"
        docker tag "financial-planning-demo:$VERSION-dev" "financial-planning-demo:dev"
        docker tag "financial-planning-demo:$VERSION-fullstack" "financial-planning-demo:fullstack"
        ;;
    *)
        echo "Invalid build type: $BUILD_TYPE"
        echo "Valid options: demo, dev, fullstack, all"
        exit 1
        ;;
esac

echo ""
echo "Build completed successfully!"
echo ""
echo "Available images:"
docker images | grep financial-planning-demo | head -10
EOF

    # Run script
    cat > "$DOCKER_DIR/scripts/run.sh" << 'EOF'
#!/bin/bash

# Financial Planning Demo - Docker Run Script
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(dirname "$SCRIPT_DIR")/compose"

MODE=${1:-demo}
ACTION=${2:-up}

echo "Financial Planning Demo - Docker Runner"
echo "======================================"
echo "Mode: $MODE"
echo "Action: $ACTION"
echo ""

cd "$COMPOSE_DIR"

case $MODE in
    "demo")
        docker-compose -f docker-compose.demo.yml $ACTION -d
        ;;
    "dev")
        docker-compose -f docker-compose.dev.yml $ACTION -d
        ;;
    "prod")
        docker-compose -f docker-compose.prod.yml $ACTION -d
        ;;
    *)
        echo "Invalid mode: $MODE"
        echo "Valid options: demo, dev, prod"
        exit 1
        ;;
esac

if [ "$ACTION" = "up" ]; then
    echo ""
    echo "Waiting for services to start..."
    sleep 10
    
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo "✓ Demo is running successfully!"
        echo ""
        echo "Access URLs:"
        echo "  Demo: http://localhost:8000"
        echo "  API Docs: http://localhost:8000/docs"
        echo "  Health: http://localhost:8000/health"
        
        if [ "$MODE" = "dev" ]; then
            echo "  Grafana: http://localhost:3000 (admin/demo)"
            echo "  Prometheus: http://localhost:9090"
            echo "  PostgreSQL: localhost:5432 (demo/demo)"
        fi
    else
        echo "⚠ Demo may still be starting up..."
        echo "Check status with: docker-compose -f docker-compose.$MODE.yml logs"
    fi
fi
EOF

    # Stop script
    cat > "$DOCKER_DIR/scripts/stop.sh" << 'EOF'
#!/bin/bash

# Financial Planning Demo - Docker Stop Script
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(dirname "$SCRIPT_DIR")/compose"

MODE=${1:-demo}

echo "Stopping Financial Planning Demo ($MODE mode)..."

cd "$COMPOSE_DIR"

case $MODE in
    "demo")
        docker-compose -f docker-compose.demo.yml down
        ;;
    "dev")
        docker-compose -f docker-compose.dev.yml down
        ;;
    "prod")
        docker-compose -f docker-compose.prod.yml down
        ;;
    "all")
        docker-compose -f docker-compose.demo.yml down 2>/dev/null || true
        docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
        docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
        ;;
    *)
        echo "Invalid mode: $MODE"
        echo "Valid options: demo, dev, prod, all"
        exit 1
        ;;
esac

echo "Demo stopped successfully!"
EOF

    # Make scripts executable
    chmod +x "$DOCKER_DIR/scripts"/*.sh
    
    success "Docker helper scripts created"
}

# Create distribution package
create_docker_package() {
    log "Creating Docker distribution package..."
    
    cd "$DIST_DIR"
    
    # Create docker distribution archive
    tar -czf "financial-planning-demo-docker-${VERSION}-${BUILD_DATE}.tar.gz" docker/
    
    # Create Docker distribution README
    cat > "$DOCKER_DIR/README.md" << 'EOF'
# Financial Planning Demo - Docker Distribution

This directory contains Docker-based deployment options for the Financial Planning Demo.

## Quick Start

### Demo Mode (Recommended)
```bash
# Build and run demo
./scripts/build.sh
./scripts/run.sh demo

# Access demo at http://localhost:8000
```

### Development Mode
```bash
# Build and run with full development stack
./scripts/build.sh latest dev
./scripts/run.sh dev

# Includes PostgreSQL, Redis, Prometheus, Grafana
```

## Directory Structure

```
docker/
├── images/                 # Dockerfiles
│   ├── Dockerfile.demo     # Production-optimized demo
│   ├── Dockerfile.dev      # Development with tools
│   └── Dockerfile.fullstack # Backend + Frontend
├── compose/                # Docker Compose files
│   ├── docker-compose.demo.yml      # Simple demo
│   ├── docker-compose.dev.yml       # Development stack
│   └── docker-compose.prod.yml      # Production-like
├── kubernetes/             # Kubernetes manifests
│   ├── base/              # Base configurations
│   └── overlays/          # Environment-specific
└── scripts/               # Helper scripts
    ├── build.sh           # Build images
    ├── run.sh             # Run containers
    └── stop.sh            # Stop containers
```

## Usage Examples

### Build Specific Image
```bash
./scripts/build.sh v1.0.0 demo     # Demo image
./scripts/build.sh v1.0.0 dev      # Development image
./scripts/build.sh v1.0.0 all      # All images
```

### Run Different Modes
```bash
./scripts/run.sh demo               # Basic demo
./scripts/run.sh dev                # Development stack
./scripts/run.sh prod               # Production-like
```

### Kubernetes Deployment
```bash
kubectl apply -f kubernetes/base/
kubectl apply -f kubernetes/overlays/demo/
```

## Configuration

Environment variables can be set in the compose files or passed at runtime:
- `DEMO_MODE=true` - Enable demo mode
- `DEBUG=true` - Enable debug logging
- `API_HOST=0.0.0.0` - API host binding
- `API_PORT=8000` - API port

## Monitoring

Development mode includes:
- Prometheus (http://localhost:9090)
- Grafana (http://localhost:3000, admin/demo)
- PostgreSQL (localhost:5432, demo/demo)

## Troubleshooting

### Check Logs
```bash
docker-compose -f compose/docker-compose.demo.yml logs
```

### Health Check
```bash
curl http://localhost:8000/health
```

### Reset Environment
```bash
./scripts/stop.sh all
docker system prune -f
./scripts/build.sh latest all
./scripts/run.sh demo
```

For more information, see the main demo documentation.
EOF

    success "Docker distribution package created"
}

# Generate Docker documentation
create_docker_documentation() {
    log "Creating Docker documentation..."
    
    cat > "$DOCKER_DIR/DOCKER_DEPLOYMENT_GUIDE.md" << 'EOF'
# Financial Planning Demo - Docker Deployment Guide

## Overview

The Financial Planning Demo provides multiple Docker deployment options ranging from simple single-container demos to full development environments with monitoring and persistence.

## Deployment Options

### 1. Simple Demo Container
**Best for**: Quick evaluation, minimal resource usage
```bash
docker run -p 8000:8000 financial-planning-demo:latest
```

### 2. Docker Compose Demo
**Best for**: Persistent demo with volume management
```bash
docker-compose -f compose/docker-compose.demo.yml up -d
```

### 3. Development Environment
**Best for**: Development, testing, full feature exploration
```bash
docker-compose -f compose/docker-compose.dev.yml up -d
```

### 4. Production-like Deployment
**Best for**: Performance testing, scalability evaluation
```bash
docker-compose -f compose/docker-compose.prod.yml up -d
```

## Image Variants

### Demo Image (`Dockerfile.demo`)
- **Size**: ~200MB
- **Features**: Core simulation engine, basic API
- **Use Case**: Production demos, minimal footprint
- **Resources**: 1GB RAM, 1 CPU core

### Development Image (`Dockerfile.dev`)
- **Size**: ~500MB  
- **Features**: Full development tools, debugging support
- **Use Case**: Development, debugging, testing
- **Resources**: 2GB RAM, 2 CPU cores

### Full-stack Image (`Dockerfile.fullstack`)
- **Size**: ~300MB
- **Features**: Backend + Frontend, nginx proxy
- **Use Case**: Complete application demo
- **Resources**: 1.5GB RAM, 2 CPU cores

## Environment Configuration

### Core Variables
```bash
# Application
DEMO_MODE=true                    # Enable demo mode
DEBUG=false                       # Debug logging
API_HOST=0.0.0.0                 # Host binding
API_PORT=8000                     # Port number

# Database
DATABASE_URL=sqlite:///./demo_data/financial_data.db
# Or PostgreSQL: postgresql://user:pass@host:5432/dbname

# Security (Demo only - change in production)
SECRET_KEY=demo-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Performance
SIMULATION_COUNT=10000            # Monte Carlo simulations
ENABLE_ML_FEATURES=true           # ML recommendations
```

### Resource Limits
```yaml
# Docker Compose resource limits
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'  
      memory: 2G
```

## Networking

### Port Mapping
- **8000**: Main API and demo interface
- **8888**: Jupyter notebook (dev mode)
- **5432**: PostgreSQL (dev/prod modes)
- **6379**: Redis (dev/prod modes)
- **3000**: Grafana monitoring (dev mode)
- **9090**: Prometheus metrics (dev mode)

### Service Discovery
Services communicate via Docker network names:
- `postgres`: Database service
- `redis`: Cache service
- `financial-planning-demo`: Main application

## Data Persistence

### Volume Mounts
```yaml
volumes:
  - demo_data:/app/demo_data       # Demo scenarios and results
  - demo_logs:/app/logs            # Application logs
  - postgres_data:/var/lib/postgresql/data  # Database
```

### Backup Strategy
```bash
# Backup demo data
docker run --rm -v demo_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/demo_data.tar.gz -C /data .

# Restore demo data
docker run --rm -v demo_data:/data -v $(pwd):/backup alpine \
  tar xzf /backup/demo_data.tar.gz -C /data
```

## Security Considerations

### Demo Security (Current)
⚠️ **Warning**: Demo configuration uses default credentials
- Default JWT secret key
- Demo database passwords
- Exposed ports without authentication
- No SSL/TLS encryption

### Production Security (Required)
```bash
# Use environment variables for secrets
export SECRET_KEY=$(openssl rand -base64 32)
export POSTGRES_PASSWORD=$(openssl rand -base64 16)

# Enable SSL/TLS
export ENABLE_HTTPS=true
export SSL_CERT_PATH=/etc/ssl/certs/
export SSL_KEY_PATH=/etc/ssl/private/

# Restrict network access
export API_HOST=127.0.0.1  # Localhost only
```

## Monitoring and Logging

### Health Checks
```bash
# Container health
docker ps --filter "name=fp-demo"

# Application health
curl http://localhost:8000/health

# Service logs
docker-compose logs financial-planning-demo
```

### Metrics Collection
Development mode includes Prometheus metrics:
```bash
# API metrics
curl http://localhost:8000/metrics

# System metrics via Prometheus
curl http://localhost:9090/api/v1/query?query=up

# Grafana dashboards
open http://localhost:3000  # admin/demo
```

## Scaling and Performance

### Horizontal Scaling
```yaml
# Docker Compose scaling
services:
  financial-planning-demo:
    deploy:
      replicas: 3
```

### Performance Tuning
```bash
# Increase simulation performance
export SIMULATION_COUNT=50000
export ENABLE_PARALLEL_PROCESSING=true

# Database optimization
export DATABASE_POOL_SIZE=20
export DATABASE_MAX_OVERFLOW=10

# Memory optimization
export PYTHON_GC_THRESHOLD=700,10,10
```

## Kubernetes Deployment

### Basic Deployment
```bash
# Apply base configuration
kubectl apply -f kubernetes/base/

# Apply environment overlay
kubectl apply -f kubernetes/overlays/demo/

# Check status
kubectl get pods -l app=financial-planning-demo
```

### Advanced Kubernetes Features
```yaml
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: financial-planning-demo-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: financial-planning-demo
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker logs financial-planning-demo

# Common causes:
# - Port already in use
# - Insufficient memory
# - Missing environment variables
```

#### Database Connection Failed
```bash
# Check database status
docker-compose exec postgres pg_isready

# Reset database
docker-compose down -v
docker-compose up -d
```

#### Performance Issues
```bash
# Check resource usage
docker stats financial-planning-demo

# Reduce simulation count
export SIMULATION_COUNT=1000

# Check available memory
free -h
```

#### Network Connectivity
```bash
# Test internal connectivity
docker-compose exec financial-planning-demo ping postgres

# Test external access
curl http://localhost:8000/health
```

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true

# Start with interactive shell
docker-compose run --rm financial-planning-demo bash

# Monitor real-time logs
docker-compose logs -f
```

### Performance Profiling
```bash
# CPU profiling
docker-compose exec financial-planning-demo python -m cProfile working_demo.py

# Memory profiling
docker-compose exec financial-planning-demo python -m memory_profiler working_demo.py
```

## Best Practices

### Development
- Use development compose for feature work
- Mount source code as volumes for hot reloading
- Enable debug mode and verbose logging
- Use separate databases for each developer

### Testing
- Run tests inside containers for consistency
- Use dedicated test databases
- Automate testing with CI/CD pipelines
- Test resource limits and scaling

### Production Readiness
- Use production-optimized images
- Implement proper secret management
- Configure resource limits and health checks
- Set up monitoring and alerting
- Plan backup and recovery procedures

## Support

For Docker-specific issues:
1. Check container logs: `docker-compose logs`
2. Verify resource availability: `docker stats`
3. Test connectivity: `curl http://localhost:8000/health`
4. Review configuration: `docker-compose config`

For application issues, refer to the main demo documentation.
EOF

    success "Docker documentation created"
}

# Main execution
main() {
    echo -e "${BLUE}"
    echo "Financial Planning Demo - Docker Distribution Creator"
    echo "===================================================="
    echo "Version: $VERSION"
    echo "Build Date: $BUILD_DATE"
    echo -e "${NC}"
    
    create_docker_directory
    create_demo_dockerfile
    create_dev_dockerfile
    create_fullstack_dockerfile
    create_docker_compose
    create_kubernetes_manifests
    create_docker_scripts
    create_docker_package
    create_docker_documentation
    
    # Final summary
    echo ""
    success "Docker distribution created successfully!"
    echo ""
    echo -e "${GREEN}Docker Distribution Contents:${NC}"
    echo "├── Images: Demo, Development, Full-stack"
    echo "├── Compose: Single, Multi-service, Production-like"
    echo "├── Kubernetes: Base manifests and overlays"
    echo "├── Scripts: Build, run, and management utilities"
    echo "└── Documentation: Complete deployment guides"
    echo ""
    echo -e "${GREEN}Quick Start Commands:${NC}"
    echo "cd $DOCKER_DIR"
    echo "./scripts/build.sh $VERSION demo"
    echo "./scripts/run.sh demo"
    echo ""
    echo -e "${BLUE}Docker distribution is ready for deployment!${NC}"
}

# Run main function
main "$@"