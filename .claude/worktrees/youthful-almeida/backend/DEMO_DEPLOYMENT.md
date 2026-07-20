# Financial Planning System - Demo Deployment Guide

## 🚀 Quick Start

Get the demo running in under 5 minutes:

```bash
# 1. Quick start (recommended)
make install && make demo

# 2. Manual start
./start_demo.sh

# 3. Stop when done
./stop_demo.sh
```

## 📋 Overview

This financial planning system includes production-ready deployment automation with:

- **Complete containerized environment** (Docker + Docker Compose)
- **Automated system requirements checking**
- **Database migrations and demo data seeding**
- **Health monitoring and alerting**
- **Zero-downtime deployment strategies**
- **Cross-platform compatibility** (macOS, Linux, Windows WSL)

## 🛠️ Prerequisites

### Required Software
- **Docker Desktop** (v20.10+)
- **Docker Compose** (v2.0+) 
- **Python 3.8+**
- **Make** (for Makefile targets)

### System Requirements
- **Memory**: 4GB+ recommended
- **Disk Space**: 2GB+ free space
- **Network**: Internet connection for dependencies

### Quick Prerequisites Check
```bash
make check-deps
```

## 📁 Demo Scripts Overview

| Script | Purpose | Usage |
|--------|---------|-------|
| `start_demo.sh` | Complete demo startup | `./start_demo.sh` |
| `stop_demo.sh` | Graceful shutdown | `./stop_demo.sh` |
| `reset_demo.sh` | Reset to initial state | `./reset_demo.sh` |
| `Makefile` | All deployment targets | `make help` |
| `scripts/seed_demo_data.py` | Generate sample data | `python3 scripts/seed_demo_data.py` |
| `scripts/health_check.py` | Health monitoring | `python3 scripts/health_check.py` |
| `scripts/monitor_demo.sh` | Real-time dashboard | `./scripts/monitor_demo.sh` |

## 🎯 Deployment Workflows

### 1. Development Environment
```bash
# Start development environment with hot reload
make dev

# Or with environment variables
ENVIRONMENT=development DEBUG=true ./start_demo.sh
```

### 2. Demo Environment 
```bash
# Start complete demo with sample data
make demo

# Or manually
DEMO_ENV=demo SEED_DEMO_DATA=true ./start_demo.sh
```

### 3. Production-like Environment
```bash
# Start production configuration
make prod

# Or with production compose file
docker-compose -f docker-compose.prod.yml up -d
```

## 🔧 Configuration Options

### Environment Variables

#### Demo Control
```bash
export DEMO_ENV=development|demo|production
export SEED_DEMO_DATA=true|false
export AUTO_OPEN_BROWSER=true|false
export SKIP_CHECKS=true|false
```

#### Docker Compose Profiles
```bash
export COMPOSE_PROFILES=monitoring,admin,test,load-test
```

#### Reset Options
```bash
export RESET_TYPE=soft|hard|restore
export PRESERVE_USER_DATA=true|false
export PRESERVE_DATA=true|false
```

#### Advanced Options
```bash
export FORCE_BUILD=true|false
export CLEANUP_IMAGES=true|false
export INTERACTIVE=true|false
```

### Configuration Files

#### Environment Configuration
1. Copy template: `cp env.template .env`
2. Edit values in `.env` file
3. Key settings:
   - `DATABASE_URL`: Database connection
   - `REDIS_URL`: Cache connection
   - `SECRET_KEY`: Application secret
   - API keys for external services

## 📊 Service Architecture

### Core Services
- **API Server** (FastAPI) - Port 8000
- **PostgreSQL Database** - Port 5432
- **Redis Cache** - Port 6379
- **Nginx Reverse Proxy** - Port 80/443

### Background Services
- **Celery Worker** - Background tasks
- **Celery Beat** - Scheduled tasks

### Monitoring Stack (Optional)
- **Prometheus** - Metrics collection - Port 9091
- **Grafana** - Monitoring dashboard - Port 3000

### Admin Tools (Optional)
- **pgAdmin** - Database administration - Port 5050
- **Redis Commander** - Redis management - Port 8081

## 🎮 Demo Features

### Sample Data Included
- **5 Demo Users** with different risk profiles
- **Financial Goals** (emergency fund, retirement, etc.)
- **Investment Portfolios** with realistic allocations
- **Monte Carlo Simulations** with 30-year projections
- **AI Recommendations** based on user profiles
- **Market Data Cache** with historical prices
- **Audit Logs** for compliance tracking

### Demo Credentials
```
Email: demo@financialplanning.com
Password: demo123456

Additional demo users:
- sarah.investor@example.com
- mike.conservative@example.com  
- emma.planner@example.com
- david.retiree@example.com
(All use password: demo123456)
```

## 🔍 Monitoring & Health Checks

### Real-time Monitoring
```bash
# Start monitoring dashboard
./scripts/monitor_demo.sh

# Quick health check
./scripts/monitor_demo.sh --quick

# Comprehensive health check
python3 scripts/health_check.py --verbose

# Export health check to JSON
python3 scripts/health_check.py --json health_report.json
```

### Monitoring Endpoints
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics
- **API Documentation**: http://localhost:8000/docs

### Log Monitoring
```bash
# View all logs
make logs

# View specific service logs
make logs-api
make logs-db
make logs-redis

# Monitor logs in real-time
docker-compose logs -f api
```

## 🗃️ Database Management

### Migrations
```bash
# Run latest migrations
make migrate

# Create new migration
make migrate-create MSG="Add new feature"

# View migration status
docker-compose exec api alembic current
```

### Backup & Restore
```bash
# Create backup
make backup

# Restore from backup
make restore BACKUP=backups/backup-20240101-120000.sql

# Scheduled backups (manual setup)
crontab -e
# Add: 0 2 * * * cd /path/to/project && make backup
```

### Demo Data Management
```bash
# Seed demo data
make seed

# Reset to initial state (soft reset)
./reset_demo.sh

# Complete reset (hard reset)
./reset_demo.sh --type hard

# Reset preserving user data
./reset_demo.sh --preserve-users

# Restore from backup
./reset_demo.sh --type restore --backup-dir backups/demo-20240101-120000
```

## 🧪 Testing

### Unit Tests
```bash
make test-unit
```

### Integration Tests
```bash
make test-integration
```

### Load Testing
```bash
make load-test
# Opens Locust UI at http://localhost:8089
```

### Performance Testing
```bash
make test-performance
make benchmark
```

## 🔒 Security

### Security Audits
```bash
# Run security audit
make security

# Comprehensive audit
make audit

# Check for vulnerabilities
make update-deps
```

### Security Best Practices
- All secrets in environment variables
- Database credentials in `.env` file
- API keys not committed to version control
- SSL/TLS termination at nginx
- Rate limiting enabled
- Input validation on all endpoints

## 🚢 Deployment Strategies

### Blue-Green Deployment
```bash
# Deploy to staging
make deploy-staging

# Switch traffic after validation
scripts/deployment/blue-green-deploy.sh
```

### Canary Deployment
```bash
# Gradual rollout
scripts/deployment/canary-deploy.sh --percentage 10
```

### Rollback
```bash
# Quick rollback
scripts/deployment/rollback.sh

# Or using make
make rollback
```

## 🐳 Docker Operations

### Image Management
```bash
# Build images
make docker-build

# Build production images
make docker-build-prod

# Push to registry (configure first)
make docker-push

# Clean up images
make docker-clean
```

### Container Management
```bash
# View container status
docker-compose ps

# Restart specific service
docker-compose restart api

# Scale services
docker-compose up -d --scale celery-worker=3

# Access container shell
make shell          # API container
make shell-db       # Database
make shell-redis    # Redis
```

## ☸️ Kubernetes Deployment

### Local Kubernetes
```bash
# Deploy to local cluster
make k8s-deploy

# Deploy production configuration
make k8s-deploy-prod

# Check status
make k8s-status

# Delete resources
make k8s-delete
```

### Helm Charts
```bash
# Install with Helm
helm install financial-planning ./helm/financial-planning

# Upgrade
helm upgrade financial-planning ./helm/financial-planning

# Uninstall
helm uninstall financial-planning
```

## 🛠️ Troubleshooting

### Common Issues

#### Docker Issues
```bash
# Docker not running
sudo systemctl start docker  # Linux
# Or start Docker Desktop

# Port conflicts
./stop_demo.sh
# Check: lsof -i :8000

# Permission issues
sudo chown -R $USER:$USER .
```

#### Database Issues
```bash
# Database connection failed
docker-compose logs postgres
make health

# Migration issues
docker-compose exec api alembic current
docker-compose exec api alembic upgrade head
```

#### API Issues
```bash
# API not responding
docker-compose logs api
curl http://localhost:8000/health

# Dependency issues
docker-compose exec api pip list
make install
```

### Diagnostic Commands
```bash
# Full system status
make status

# Health check with details
python3 scripts/health_check.py --verbose

# Resource usage
make monitoring

# View all logs
make logs
```

### Performance Issues
```bash
# Check resource usage
./scripts/monitor_demo.sh --quick

# Profile application
make profile

# Database performance
make vacuum-db
```

## 📈 Scaling & Performance

### Horizontal Scaling
```bash
# Scale API workers
docker-compose up -d --scale api=3

# Scale background workers  
docker-compose up -d --scale celery-worker=5

# Load balancer configuration in nginx.conf
```

### Performance Optimization
```bash
# Enable monitoring
COMPOSE_PROFILES=monitoring make start

# View metrics in Grafana
# http://localhost:3000

# Database optimization
make vacuum-db

# Cache optimization
docker-compose exec redis redis-cli info memory
```

## 🔄 Maintenance

### Regular Maintenance
```bash
# Update dependencies
make update-deps

# Rotate logs
make rotate-logs

# Clean up temporary files
make clean

# Complete cleanup
make clean-all
```

### Scheduled Tasks
```bash
# Add to crontab for regular maintenance
0 2 * * * cd /path/to/project && make backup
0 3 * * 0 cd /path/to/project && make vacuum-db
0 4 * * 0 cd /path/to/project && make rotate-logs
```

## 📚 Additional Resources

### API Documentation
- **Interactive Docs**: http://localhost:8000/docs
- **OpenAPI Spec**: http://localhost:8000/openapi.json

### Monitoring Dashboards
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9091

### Database Tools
- **pgAdmin**: http://localhost:5050
- **Redis Commander**: http://localhost:8081

### Development Tools
```bash
# Code formatting
make format

# Linting
make lint

# Type checking
make mypy

# Pre-commit hooks
make pre-commit
```

## 🆘 Support

### Getting Help
1. Check this documentation
2. Run `make help` for available commands
3. Check logs: `make logs`
4. Run health check: `python3 scripts/health_check.py`
5. View system status: `make status`

### Common Commands Reference
```bash
# Quick start
make demo

# Stop everything
./stop_demo.sh

# Reset demo
./reset_demo.sh

# Health check
python3 scripts/health_check.py

# Monitor in real-time
./scripts/monitor_demo.sh

# View logs
make logs

# Run tests
make test

# Complete cleanup
make clean-all
```

---

**🎉 You're ready to explore the Financial Planning System!**

Start with `make demo` and visit http://localhost:8000/docs to begin testing the API.