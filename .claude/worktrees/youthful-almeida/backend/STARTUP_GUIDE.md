# FastAPI Application Startup Guide

This guide explains how to start the AI Financial Planning System backend in various configurations.

## Quick Start

The application has been designed to work with graceful degradation - it will start even if dependencies are missing.

### Option 1: With Full Dependencies (Recommended)

```bash
# Install minimal requirements
pip install -r requirements_minimal.txt

# Start the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Using the Startup Script

```bash
# The startup script will detect available dependencies and start accordingly
python3 start_app.py
```

### Option 3: Diagnostic Mode (No Dependencies)

```bash
# Run diagnostic mode to check what's available
python3 app/minimal_main.py
```

### Option 4: Import Test

```bash
# Test if the application can be imported
python3 -c "from app.main import app; print('Application imported successfully')"
```

## Application Modes

The application supports three startup modes:

### 1. Full Mode
- All dependencies available
- Complete API functionality
- Database connectivity
- All endpoints operational

### 2. Degraded Mode  
- FastAPI available but some services missing
- Fallback endpoints for critical functionality
- Mock responses where services unavailable
- Health checks show service status

### 3. Minimal Mode
- No FastAPI dependencies
- Diagnostic information only
- Mock data examples
- Service availability report

## Health Check Endpoints

Once running, check application status:

```bash
# Basic status
curl http://localhost:8000/

# Comprehensive health check
curl http://localhost:8000/health

# Service status summary
curl http://localhost:8000/status

# Mock simulation data (always available)
curl http://localhost:8000/api/v1/mock/simulation
```

## Expected Health Check Response

```json
{
  "message": "AI Financial Planning System API",
  "version": "1.0.0",
  "status": "running",
  "services": {
    "fastapi": true,
    "database": false,
    "api_router": true,
    "settings": true,
    "exceptions": true
  },
  "timestamp": "2025-08-22T22:30:00.000000Z"
}
```

## Troubleshooting

### Import Errors
- The application logs all import errors with specific reasons
- Check `/health` endpoint for detailed error information
- Missing dependencies are handled gracefully

### Database Issues
- Application starts even without database connectivity
- Database errors are logged but don't prevent startup
- Health check shows database status

### Missing Services
- Individual services can fail without affecting others
- Fallback routes provide mock responses
- `/debug` endpoint (in development) shows detailed information

## Development Setup

1. **Clone and Navigate**
   ```bash
   cd backend/
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements_minimal.txt
   ```

3. **Environment Variables** (Optional)
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Start Development Server**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access Documentation**
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## Production Deployment

The application is designed to work in various deployment scenarios:

```bash
# With Gunicorn (production)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# With Docker
docker build -t financial-planning-api .
docker run -p 8000:8000 financial-planning-api

# Direct uvicorn (development/testing)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Error Handling

The application includes comprehensive error handling:

- **Import Errors**: Graceful fallbacks for missing dependencies
- **Database Errors**: Non-blocking database issues
- **Service Errors**: Individual service failures don't crash the app
- **Configuration Errors**: Fallback to default settings

All errors are logged with appropriate severity levels and provide actionable information for troubleshooting.