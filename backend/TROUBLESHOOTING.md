# Financial Planning System - Troubleshooting Guide

This comprehensive troubleshooting guide helps you diagnose and fix common issues with the Financial Planning System demos and production deployments.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Common Issues](#common-issues)
- [Dependency Problems](#dependency-problems)
- [Port Conflicts](#port-conflicts)
- [Database Issues](#database-issues)
- [API Errors](#api-errors)
- [Frontend Build Issues](#frontend-build-issues)
- [Docker Problems](#docker-problems)
- [Performance Issues](#performance-issues)
- [Security Configuration](#security-configuration)
- [Error Message Decoder](#error-message-decoder)
- [Log File Locations](#log-file-locations)
- [Debug Mode Instructions](#debug-mode-instructions)
- [Frequently Asked Questions](#frequently-asked-questions)
- [Support Information](#support-information)

## Quick Diagnostics

Run these commands to quickly identify system status:

```bash
# System diagnostic script
python3 check_system.py

# Quick health check
curl http://localhost:8000/health

# Check running services
docker-compose ps

# View recent logs
docker-compose logs --tail=50
```

## Common Issues

### Issue: "Demo won't start"

**Symptoms:**
- Script exits immediately
- Error messages about missing dependencies
- Port already in use errors

**Solutions:**

1. **Check Python version:**
   ```bash
   python3 --version  # Should be 3.8+
   ```

2. **Install basic dependencies:**
   ```bash
   pip3 install fastapi uvicorn numpy pydantic
   ```

3. **Check port availability:**
   ```bash
   lsof -i :8000  # Check if port 8000 is in use
   ```

4. **Kill conflicting processes:**
   ```bash
   pkill -f "python.*8000"
   ```

### Issue: "Import errors when starting"

**Symptoms:**
- `ModuleNotFoundError`
- `ImportError` messages
- Missing package errors

**Solutions:**

1. **Install from requirements file:**
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Use virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Check Python path:**
   ```bash
   python3 -c "import sys; print('\n'.join(sys.path))"
   ```

### Issue: "Database connection failed"

**Symptoms:**
- Connection refused errors
- Database not found errors
- Authentication failures

**Solutions:**

1. **Reset database:**
   ```bash
   ./reset_demo_env.sh
   ```

2. **Manual database setup:**
   ```bash
   python3 test_db_setup.py
   ```

3. **Check database status:**
   ```bash
   docker-compose exec postgres pg_isready
   ```

## Dependency Problems

### Python Dependencies

**Problem:** Package installation failures

**Solutions:**

1. **Update pip:**
   ```bash
   python3 -m pip install --upgrade pip
   ```

2. **Install with user flag:**
   ```bash
   pip3 install --user -r requirements.txt
   ```

3. **Use conda instead:**
   ```bash
   conda install fastapi uvicorn numpy scipy matplotlib
   ```

4. **Platform-specific issues:**

   **macOS M1/M2:**
   ```bash
   arch -arm64 pip3 install numpy scipy
   ```

   **Ubuntu/Debian:**
   ```bash
   sudo apt-get update
   sudo apt-get install python3-dev python3-pip
   ```

   **CentOS/RHEL:**
   ```bash
   sudo yum install python3-devel python3-pip
   ```

### Node.js Dependencies (Frontend)

**Problem:** NPM install failures

**Solutions:**

1. **Clear npm cache:**
   ```bash
   npm cache clean --force
   ```

2. **Delete node_modules:**
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **Use yarn instead:**
   ```bash
   yarn install
   ```

## Port Conflicts

### Finding Port Usage

```bash
# Check what's using port 8000
lsof -i :8000

# Check multiple ports
netstat -tulpn | grep -E ":(8000|3000|5432|6379)"

# Find all Python processes using ports
ps aux | grep python | grep -E ":(8000|3000)"
```

### Resolving Conflicts

1. **Kill processes on specific ports:**
   ```bash
   # Kill process on port 8000
   lsof -ti:8000 | xargs kill -9
   
   # Or use our fix script
   ./fix_common_issues.sh --kill-ports
   ```

2. **Change default ports:**
   ```bash
   export BACKEND_PORT=8001
   export FRONTEND_PORT=3001
   python3 working_demo.py
   ```

3. **Docker port conflicts:**
   ```bash
   docker-compose down
   docker container prune
   ```

## Database Issues

### Connection Problems

**Error:** `psycopg2.OperationalError: could not connect to server`

**Solutions:**

1. **Start PostgreSQL:**
   ```bash
   docker-compose up -d postgres
   ```

2. **Check database credentials:**
   ```bash
   # View current environment
   grep -E "(DB_|DATABASE_)" .env
   ```

3. **Reset database:**
   ```bash
   docker-compose down -v
   docker-compose up -d postgres
   python3 app/database/init_db.py
   ```

### Migration Issues

**Error:** `alembic.util.exc.CommandError`

**Solutions:**

1. **Reset migrations:**
   ```bash
   rm -rf alembic/versions/*.py
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   ```

2. **Manual database reset:**
   ```bash
   docker-compose exec postgres dropdb -U financial_planning financial_planning
   docker-compose exec postgres createdb -U financial_planning financial_planning
   alembic upgrade head
   ```

### Data Issues

**Problem:** Demo data not loading

**Solutions:**

1. **Reseed data:**
   ```bash
   python3 scripts/seed_demo_data.py
   ```

2. **Check data integrity:**
   ```bash
   python3 -c "
   from app.database.init_db import check_database_health
   check_database_health()
   "
   ```

## API Errors

### Authentication Errors

**Error:** `401 Unauthorized` or `403 Forbidden`

**Solutions:**

1. **Check JWT secret:**
   ```bash
   grep SECRET_KEY .env
   ```

2. **Generate new secret:**
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Test authentication:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=demo@example.com&password=demo123"
   ```

### Rate Limiting

**Error:** `429 Too Many Requests`

**Solutions:**

1. **Check rate limit settings:**
   ```bash
   grep -E "(RATE_|LIMIT_)" .env
   ```

2. **Temporary bypass:**
   ```bash
   export RATE_LIMIT_ENABLED=false
   ```

3. **Reset rate limit cache:**
   ```bash
   docker-compose restart redis
   ```

### Validation Errors

**Error:** `422 Unprocessable Entity`

**Solutions:**

1. **Check API documentation:**
   - Visit `http://localhost:8000/docs`
   - Review request schema requirements

2. **Validate request data:**
   ```bash
   # Example valid request
   curl -X POST "http://localhost:8000/api/v1/simulations/monte-carlo" \
        -H "Content-Type: application/json" \
        -d '{
          "initial_investment": 10000,
          "monthly_contribution": 500,
          "annual_return": 0.07,
          "volatility": 0.15,
          "years": 10,
          "simulations": 1000
        }'
   ```

## Frontend Build Issues

### Build Failures

**Error:** TypeScript compilation errors

**Solutions:**

1. **Check Node.js version:**
   ```bash
   node --version  # Should be 16+ or 18+
   npm --version
   ```

2. **Clear build cache:**
   ```bash
   rm -rf .next/cache
   npm run build
   ```

3. **Fix TypeScript errors:**
   ```bash
   npx tsc --noEmit  # Check for type errors
   ```

### Development Server Issues

**Problem:** Hot reload not working

**Solutions:**

1. **Check file watchers:**
   ```bash
   # Increase file watcher limit on Linux
   echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
   sudo sysctl -p
   ```

2. **Restart dev server:**
   ```bash
   npm run dev -- --port 3000
   ```

## Docker Problems

### Container Startup Issues

**Problem:** Containers won't start

**Solutions:**

1. **Check Docker daemon:**
   ```bash
   docker info
   sudo systemctl start docker  # Linux
   ```

2. **Clean Docker system:**
   ```bash
   docker system prune -f
   docker volume prune -f
   ```

3. **Rebuild containers:**
   ```bash
   docker-compose down -v
   docker-compose build --no-cache
   docker-compose up -d
   ```

### Memory Issues

**Error:** `OOMKilled` or memory allocation errors

**Solutions:**

1. **Increase Docker memory:**
   - Docker Desktop: Settings > Resources > Memory (increase to 4GB+)

2. **Optimize container resources:**
   ```yaml
   # In docker-compose.yml
   services:
     api:
       mem_limit: 1g
       memswap_limit: 1g
   ```

3. **Monitor memory usage:**
   ```bash
   docker stats
   ```

### Network Issues

**Problem:** Services can't communicate

**Solutions:**

1. **Check Docker networks:**
   ```bash
   docker network ls
   docker network inspect financial-planning_default
   ```

2. **Recreate networks:**
   ```bash
   docker-compose down
   docker network prune
   docker-compose up -d
   ```

## Performance Issues

### Slow API Response

**Symptoms:**
- High response times (>5 seconds)
- Timeouts on complex simulations

**Solutions:**

1. **Enable caching:**
   ```bash
   export REDIS_CACHE_ENABLED=true
   export CACHE_TTL=3600
   ```

2. **Optimize database queries:**
   ```bash
   # Check for slow queries
   docker-compose exec postgres psql -U financial_planning -d financial_planning -c "
   SELECT query, mean_time, calls
   FROM pg_stat_statements
   ORDER BY mean_time DESC
   LIMIT 10;
   "
   ```

3. **Use performance monitoring:**
   ```bash
   python3 performance_demo.py
   ```

### Memory Usage

**Problem:** High memory consumption

**Solutions:**

1. **Monitor memory usage:**
   ```bash
   python3 -c "
   import psutil
   process = psutil.Process()
   print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB')
   "
   ```

2. **Enable garbage collection:**
   ```bash
   export PYTHONMALLOC=malloc
   export PYTHONASYNCIODEBUG=1
   ```

3. **Optimize NumPy operations:**
   ```bash
   export OMP_NUM_THREADS=4
   export NUMBA_CACHE_DIR=/tmp/numba_cache
   ```

## Security Configuration

### SSL/TLS Issues

**Problem:** HTTPS certificate errors

**Solutions:**

1. **Generate self-signed certificate:**
   ```bash
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
   ```

2. **Use development settings:**
   ```bash
   export SSL_VERIFY=false
   export DEVELOPMENT_MODE=true
   ```

### Environment Variables

**Problem:** Missing or incorrect environment variables

**Solutions:**

1. **Check environment file:**
   ```bash
   # Copy template and customize
   cp env.template .env
   
   # Generate secure secret key
   python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env
   ```

2. **Validate environment:**
   ```bash
   python3 -c "
   import os
   from app.core.config import settings
   print('Environment loaded successfully')
   print(f'Database URL: {settings.database_url[:20]}...')
   "
   ```

## Error Message Decoder

### Common Error Patterns

| Error Pattern | Likely Cause | Solution |
|---------------|--------------|----------|
| `ModuleNotFoundError: No module named 'X'` | Missing dependency | `pip install X` |
| `ConnectionRefusedError: [Errno 61]` | Service not running | Start the service |
| `psycopg2.OperationalError` | Database connection issue | Check database status |
| `ValidationError` | Invalid input data | Check API schema |
| `PermissionError` | File/directory permissions | Check file permissions |
| `OSError: [Errno 48] Address already in use` | Port conflict | Kill process or change port |

### Specific Error Codes

**HTTP 500 - Internal Server Error**
```bash
# Check application logs
docker-compose logs api --tail=100

# Enable debug mode
export DEBUG=true
python3 working_demo.py
```

**HTTP 404 - Not Found**
```bash
# Check route registration
curl -s http://localhost:8000/openapi.json | jq '.paths | keys'
```

**HTTP 422 - Validation Error**
```bash
# Get detailed validation info
curl -X POST "http://localhost:8000/api/v1/endpoint" \
     -H "Content-Type: application/json" \
     -d '{}' -v
```

## Log File Locations

### Application Logs
```
backend/logs/
├── api/
│   ├── access.log          # HTTP requests
│   ├── error.log           # Application errors
│   └── debug.log           # Debug information
├── celery/
│   ├── worker.log          # Background tasks
│   └── beat.log            # Scheduled tasks
└── nginx/
    ├── access.log          # Proxy logs
    └── error.log           # Proxy errors
```

### System Logs
```bash
# Docker container logs
docker-compose logs [service_name]

# System logs (Linux)
sudo journalctl -u docker
sudo journalctl -f

# macOS logs
log stream --predicate 'subsystem == "com.docker.docker"'
```

### Database Logs
```bash
# PostgreSQL logs
docker-compose exec postgres tail -f /var/log/postgresql/postgresql.log

# Query logs (if enabled)
docker-compose exec postgres psql -U financial_planning -c "SHOW log_statement;"
```

## Debug Mode Instructions

### Enable Debug Mode

1. **Environment variable:**
   ```bash
   export DEBUG=true
   export LOG_LEVEL=DEBUG
   ```

2. **In code:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   
   # Enable SQLAlchemy query logging
   import logging
   logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
   ```

3. **Docker Compose:**
   ```yaml
   environment:
     - DEBUG=true
     - LOG_LEVEL=DEBUG
     - SQLALCHEMY_ECHO=true
   ```

### Debugging Tools

1. **Interactive debugger:**
   ```python
   import pdb; pdb.set_trace()
   ```

2. **Rich tracebacks:**
   ```bash
   pip install rich
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   python3 -c "from rich.console import Console; Console().print_exception()"
   ```

3. **Profile performance:**
   ```bash
   python3 -m cProfile -o profile.stats working_demo.py
   python3 -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats()"
   ```

## Frequently Asked Questions

### Q: Can I run the demo without Docker?

**A:** Yes! Use the standalone Python demo:
```bash
python3 minimal_working_demo.py
```

### Q: How do I change the default ports?

**A:** Set environment variables:
```bash
export BACKEND_PORT=8001
export FRONTEND_PORT=3001
./start_demo.sh
```

### Q: Why is the simulation slow?

**A:** Several possible causes:
1. **Install Numba for JIT compilation:**
   ```bash
   pip install numba
   ```

2. **Reduce simulation count:**
   ```python
   # Instead of 10000 simulations, use 1000
   simulations = 1000
   ```

3. **Use optimized NumPy:**
   ```bash
   pip install numpy[openblas]
   ```

### Q: How do I reset everything?

**A:** Use the reset script:
```bash
./reset_demo_env.sh
```

Or manually:
```bash
docker-compose down -v
rm -rf logs/* exports/* tmp/*
./start_demo.sh
```

### Q: Can I customize the demo data?

**A:** Yes! Edit the demo data:
```bash
# Edit user data
vim scripts/seed_demo_data.py

# Or load custom data
python3 -c "
from app.database.init_db import create_sample_data
create_sample_data(custom_users=your_data)
"
```

### Q: How do I add new API endpoints?

**A:** Follow this pattern:
```python
# In app/api/v1/endpoints/your_endpoint.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/your-endpoint")
async def your_function():
    return {"message": "Hello World"}

# Register in app/api/v1/api.py
from .endpoints import your_endpoint
api_router.include_router(your_endpoint.router, prefix="/your-prefix")
```

### Q: How do I backup my data?

**A:** Use the backup script:
```bash
python3 scripts/database/backup_manager.py --create
```

Or manual backup:
```bash
docker-compose exec postgres pg_dump -U financial_planning financial_planning > backup.sql
```

## Support Information

### Getting Help

1. **Check logs first:**
   ```bash
   docker-compose logs --tail=100
   ```

2. **Run diagnostics:**
   ```bash
   python3 check_system.py --verbose
   ```

3. **Create issue with:**
   - Operating system and version
   - Python version
   - Docker version (if used)
   - Full error message
   - Steps to reproduce
   - Output of diagnostic script

### Documentation Resources

- **API Documentation:** `http://localhost:8000/docs`
- **Database Schema:** `backend/docs/database_documentation.md`
- **Architecture:** `backend/docs/code_documentation.md`
- **Security:** `backend/SECURITY_AUDIT_REPORT.md`

### Emergency Recovery

If the system is completely broken:

1. **Nuclear option - complete reset:**
   ```bash
   ./stop_demo.sh
   docker system prune -af
   docker volume prune -f
   rm -rf logs/* tmp/* exports/*
   git clean -fdx  # WARNING: Removes all untracked files
   ./start_demo.sh
   ```

2. **Minimal recovery:**
   ```bash
   python3 minimal_working_demo.py
   ```

### Performance Benchmarks

Expected performance on common hardware:

| Hardware | Monte Carlo (1000 sims) | API Response | Memory Usage |
|----------|-------------------------|--------------|--------------|
| M1 MacBook Pro | < 1s | < 200ms | < 100MB |
| Intel i7 Laptop | < 2s | < 400ms | < 150MB |
| AWS t3.medium | < 3s | < 600ms | < 200MB |
| Raspberry Pi 4 | < 10s | < 2s | < 300MB |

If your performance is significantly worse, check:
- Available memory (need 4GB+ recommended)
- CPU load (`htop` or `top`)
- Disk I/O (`iotop`)
- Network latency (if using remote databases)

---

**Last Updated:** 2025-08-22

For additional support, please create an issue with detailed information about your problem, including the output of the diagnostic script and relevant log files.