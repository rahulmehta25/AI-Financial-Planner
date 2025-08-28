#!/bin/bash

# AI Financial Planning Platform Startup Script
# This script launches the complete enterprise-grade financial planning platform

set -e

echo "🚀 Starting AI Financial Planning Platform..."
echo "================================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p monitoring/grafana/provisioning
mkdir -p nginx
mkdir -p ssl
mkdir -p scripts

# Create basic monitoring configuration
echo "📊 Setting up monitoring configuration..."
cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'financial-planner-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
EOF

# Create basic Nginx configuration
echo "🌐 Setting up Nginx configuration..."
cat > nginx/default.conf << EOF
server {
    listen 80;
    server_name localhost;

    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    location /api/ {
        proxy_pass http://api:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    location /health {
        proxy_pass http://api:8000;
        proxy_set_header Host \$host;
    }
}
EOF

# Create basic database initialization script
echo "🗄️ Setting up database initialization..."
cat > scripts/init.sql << EOF
-- Initialize financial planning database
CREATE DATABASE IF NOT EXISTS financial_planner;
CREATE DATABASE IF NOT EXISTS financial_planner_ts;

-- Create extensions for TimescaleDB
\c financial_planner_ts;
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Basic user table
\c financial_planner;
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample user
INSERT INTO users (email) VALUES ('demo@financialplanner.com') ON CONFLICT DO NOTHING;
EOF

# Create environment file
echo "⚙️ Creating environment configuration..."
cat > .env << EOF
# Database Configuration
POSTGRES_DB=financial_planner
POSTGRES_USER=financial_user
POSTGRES_PASSWORD=secure_password_123

# Redis Configuration
REDIS_PASSWORD=redis_password_123

# API Configuration
API_PORT=8000
FRONTEND_PORT=3000

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
JAEGER_PORT=16686

# Environment
ENVIRONMENT=development
DEBUG=true
EOF

echo "🔧 Environment configuration created."

# Build and start services
echo "🏗️ Building and starting services..."
docker-compose up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

# Check API health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is healthy"
else
    echo "❌ API health check failed"
fi

# Check database connection
if docker-compose exec -T postgres pg_isready -U financial_user -d financial_planner > /dev/null 2>&1; then
    echo "✅ PostgreSQL is healthy"
else
    echo "❌ PostgreSQL health check failed"
fi

# Check Redis connection
if docker-compose exec -T redis redis-cli -a redis_password_123 ping > /dev/null 2>&1; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis health check failed"
fi

# Check TimescaleDB connection
if docker-compose exec -T timescaledb pg_isready -U financial_user -d financial_planner_ts > /dev/null 2>&1; then
    echo "✅ TimescaleDB is healthy"
else
    echo "❌ TimescaleDB health check failed"
fi

echo ""
echo "🎉 Platform startup complete!"
echo "================================================"
echo "🌐 Frontend: http://localhost:3000"
echo "🔌 API: http://localhost:8000"
echo "📊 Grafana: http://localhost:3001 (admin/admin_password_123)"
echo "📈 Prometheus: http://localhost:9090"
echo "🔍 Jaeger: http://localhost:16686"
echo "📝 Kibana: http://localhost:5601"
echo "🗄️ PostgreSQL: localhost:5432"
echo "🗄️ TimescaleDB: localhost:5433"
echo "🔴 Redis: localhost:6379"
echo ""
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🔒 Health Check: http://localhost:8000/health"
echo ""
echo "🚀 To stop the platform, run: docker-compose down"
echo "📊 To view logs, run: docker-compose logs -f [service_name]"
echo ""

# Show running containers
echo "🐳 Running containers:"
docker-compose ps

echo ""
echo "✨ AI Financial Planning Platform is ready!"
echo "Start building your financial future! 🚀💰"
