# Financial Planning System - Docker Demo Setup

🚀 **One-Command Demo Deployment** 🚀

This directory contains a bulletproof Docker Compose setup for demonstrating the Financial Planning System. Everything is configured for easy deployment and includes realistic demo data.

## 🎯 Quick Start

### Prerequisites
- Docker Desktop (or Docker Engine + Docker Compose)
- At least 4GB RAM available
- At least 2GB disk space
- Ports 80, 3000, 8000, 6379 available

### One-Command Start
```bash
./start_docker_demo.sh
```

That's it! The demo will be available at: **http://localhost**

## 📋 What's Included

### Services
- **🖥️ Frontend**: Next.js application with modern UI components
- **⚡ Backend**: FastAPI with comprehensive financial planning features
- **💾 Database**: SQLite for demo simplicity (no external database needed)
- **🔄 Redis**: Caching layer for performance
- **🌐 Nginx**: Reverse proxy with optimized configuration
- **🔧 Demo Initializer**: Automatic demo data population

### Features
- ✅ Health checks for all services
- ✅ Auto-restart on failure
- ✅ Hot reload for development
- ✅ Realistic demo data
- ✅ Comprehensive logging
- ✅ Security headers
- ✅ Performance optimizations

## 🔑 Demo Credentials

**Default Demo User:**
- **Email**: `demo@financialplanning.com`
- **Password**: `demo123`

## 🌐 Access URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Main App** | http://localhost | Complete application via Nginx |
| **Frontend** | http://localhost:3000 | Direct Next.js access |
| **Backend API** | http://localhost:8000 | FastAPI backend |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **OpenAPI Spec** | http://localhost:8000/openapi.json | API specification |

## 🛠️ Script Options

The `start_docker_demo.sh` script supports various options:

```bash
# Basic usage
./start_docker_demo.sh                 # Start in foreground
./start_docker_demo.sh -d              # Start in background (detached)
./start_docker_demo.sh -r              # Force rebuild images
./start_docker_demo.sh -c              # Clean environment first
./start_docker_demo.sh -m              # Enable monitoring
./start_docker_demo.sh -v              # Verbose output
./start_docker_demo.sh -q              # Quick start (skip health checks)

# Combined options
./start_docker_demo.sh -r -d -m        # Rebuild, detached, with monitoring
./start_docker_demo.sh -c -r -v        # Clean, rebuild, verbose
```

### Option Details

| Option | Flag | Description |
|--------|------|-------------|
| Detached | `-d`, `--detach` | Run containers in background |
| Rebuild | `-r`, `--rebuild` | Force rebuild of all Docker images |
| Clean | `-c`, `--clean` | Remove existing containers and volumes |
| Monitoring | `-m`, `--monitoring` | Enable Prometheus + Grafana |
| Verbose | `-v`, `--verbose` | Show detailed build output |
| Quick | `-q`, `--quick` | Skip health checks for faster startup |
| Help | `-h`, `--help` | Show usage information |

## 📊 Demo Data

The system automatically generates realistic demo data including:

- **5 Demo Users** with varying profiles:
  - Conservative investors
  - Aggressive investors
  - Young professionals
  - Entrepreneurs
  - Pre-retirees

- **8+ Financial Goals** per user:
  - Emergency funds
  - House down payments
  - Retirement planning
  - Education funds
  - Business investments
  - Vacation funds

- **100+ Transactions** with realistic patterns
- **Monte Carlo Simulations** with probability analyses
- **Risk Assessments** and recommendations

## 🔧 Management Commands

```bash
# View logs
docker compose -f docker-compose.demo.yml -p financial-planning-demo logs -f

# Stop demo
docker compose -f docker-compose.demo.yml -p financial-planning-demo down

# Stop and cleanup (removes volumes)
docker compose -f docker-compose.demo.yml -p financial-planning-demo down -v

# Restart specific service
docker compose -f docker-compose.demo.yml -p financial-planning-demo restart backend

# View service status
docker compose -f docker-compose.demo.yml -p financial-planning-demo ps

# Execute commands in containers
docker compose -f docker-compose.demo.yml -p financial-planning-demo exec backend bash
docker compose -f docker-compose.demo.yml -p financial-planning-demo exec frontend sh
```

## 🏥 Health Monitoring

All services include comprehensive health checks:

- **Backend**: HTTP health endpoint with database connectivity
- **Frontend**: Next.js health API route
- **Redis**: Redis ping command
- **Nginx**: HTTP status check

Health check intervals:
- Backend: Every 30s (40s startup grace period)
- Frontend: Every 30s (30s startup grace period)  
- Redis: Every 10s (10s startup grace period)
- Nginx: Every 30s

## 🚨 Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check what's using the ports
lsof -i :80 -i :3000 -i :8000 -i :6379

# Stop conflicting services or use different ports
```

#### Docker Issues
```bash
# Reset Docker state
docker system prune -a
docker volume prune

# Restart Docker Desktop
# Then try again: ./start_docker_demo.sh -c -r
```

#### Memory Issues
```bash
# Check Docker memory allocation
docker system df

# Increase Docker Desktop memory limit to 4GB+
# Settings > Resources > Memory
```

#### Build Failures
```bash
# Clean build with verbose output
./start_docker_demo.sh -c -r -v

# Check individual service logs
docker compose -f docker-compose.demo.yml logs backend
docker compose -f docker-compose.demo.yml logs frontend
```

### Service-Specific Issues

#### Backend Won't Start
1. Check database permissions: `docker compose logs backend`
2. Verify SQLite directory is writable
3. Check environment variables in `.env.demo`

#### Frontend Build Issues
1. Clear Node modules: `docker compose down -v`
2. Rebuild with: `./start_docker_demo.sh -r`
3. Check Node.js memory allocation

#### Nginx Configuration
1. Verify config syntax: `docker compose config`
2. Check upstream services are running
3. Review nginx logs: `docker compose logs nginx`

## 🔒 Security Notes

**⚠️ This is a DEMO configuration with relaxed security:**

- Default passwords are used
- CORS is permissive
- Debug mode is enabled
- SSL/TLS is not configured
- Rate limiting is disabled

**🚫 DO NOT USE IN PRODUCTION**

## 📁 File Structure

```
├── docker-compose.demo.yml     # Main composition file
├── .env.demo                   # Environment variables
├── start_docker_demo.sh       # Startup script
├── config/
│   └── nginx.demo.conf        # Nginx configuration
├── backend/
│   ├── Dockerfile.demo        # Backend container config
│   └── scripts/
│       └── demo_data_seeder.py # Data initialization
└── frontend/
    └── Dockerfile.demo        # Frontend container config
```

## 🎯 Demo Scenarios

### Scenario 1: Financial Planning Demo
1. Login with demo credentials
2. Explore pre-populated financial goals
3. Run Monte Carlo simulations
4. View risk analysis reports
5. Test recommendation engine

### Scenario 2: API Integration Demo  
1. Visit http://localhost:8000/docs
2. Test API endpoints interactively
3. View realistic data responses
4. Test authentication flows

### Scenario 3: Development Setup
1. Start with: `./start_docker_demo.sh -v`
2. Edit code files (hot reload enabled)
3. View changes immediately
4. Test API integrations

## 📈 Performance Optimizations

- **Multi-stage Docker builds** for smaller images
- **Volume caching** for Node modules and dependencies  
- **Nginx gzip compression** for static assets
- **Redis caching** for frequently accessed data
- **SQLite optimization** with appropriate pragmas
- **Health check tuning** for fast startup

## 🔄 Update Process

To update the demo with new changes:

```bash
# Clean and rebuild everything
./start_docker_demo.sh -c -r -v

# Or update specific services
docker compose -f docker-compose.demo.yml build backend
docker compose -f docker-compose.demo.yml up -d backend
```

## 📞 Support

If you encounter issues:

1. **Check logs**: `docker compose logs -f [service]`
2. **Verify prerequisites**: Docker version, available ports, system resources
3. **Clean restart**: `./start_docker_demo.sh -c -r`
4. **Check the troubleshooting section** above

## 🎊 Success Indicators

When everything is working correctly, you should see:

- ✅ All services show "healthy" status
- ✅ Main app loads at http://localhost
- ✅ Login works with demo credentials
- ✅ API documentation is accessible
- ✅ Demo data is populated
- ✅ No error messages in logs

---

**🎉 Enjoy your Financial Planning System demo!** 

The complete system is now running with realistic data and full functionality. Perfect for demonstrations, development, and testing integrations.