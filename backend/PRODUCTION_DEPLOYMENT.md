# AI Financial Planning Backend - Production Deployment Guide

This guide covers deploying the AI Financial Planning Backend to production.

## 🚀 Quick Production Setup

### 1. Environment Configuration

Copy the production environment template:
```bash
cp .env.production .env
```

Update the following critical settings in `.env`:
```bash
# Security - CHANGE THESE!
SECRET_KEY=your-super-secret-key-here-at-least-32-characters
ENVIRONMENT=production
DEBUG=false

# Frontend URL
BACKEND_CORS_ORIGINS=["https://ai-financial-planner-zeta.vercel.app"]

# Database (SQLite for simplicity)
DATABASE_URL=sqlite+aiosqlite:///./financial_planning.db

# Server
HOST=0.0.0.0
PORT=8000
```

### 2. Install Dependencies

```bash
pip install -r requirements-production.txt
```

### 3. Initialize Database

```bash
python -c "
import asyncio
from app.database.init_db import init_db
asyncio.run(init_db())
"
```

### 4. Start Production Server

```bash
python start-production.py
```

## 🔧 Configuration Details

### Required API Endpoints

The backend provides these endpoints that match the frontend expectations:

- **Authentication**: `/api/v1/auth/login`, `/api/v1/auth/register`
- **AI Chat**: `/api/v1/ai/chat`, `/api/v1/ai/recommendations`
- **Simulations**: `/api/v1/simulations/monte-carlo`
- **Portfolio**: `/api/v1/portfolio/overview`, `/api/v1/portfolio/holdings`

### CORS Configuration

The backend is configured to accept requests from:
- `https://ai-financial-planner-zeta.vercel.app` (Production)
- `https://ai-financial-planner-*.vercel.app` (Preview deployments)
- Local development origins (localhost:3000, localhost:5173, etc.)

### Database Configuration

- **Default**: SQLite with `aiosqlite` driver for simplicity
- **Location**: `./financial_planning.db` in the application directory
- **Migrations**: Handled automatically on startup

### Security Features

- JWT authentication with configurable expiry
- Password hashing with bcrypt
- Rate limiting on authentication endpoints
- CORS protection
- Request logging and audit trails

## 🐳 Docker Deployment

### Build Production Image

```bash
docker build -f Dockerfile.production -t financial-planner-backend .
```

### Run Container

```bash
docker run -d \
  --name financial-planner-backend \
  -p 8000:8000 \
  -e SECRET_KEY=your-secret-key-here \
  -e BACKEND_CORS_ORIGINS='["https://ai-financial-planner-zeta.vercel.app"]' \
  -v $(pwd)/data:/app/data \
  financial-planner-backend
```

## ☁️ Cloud Deployment

### Railway

1. Connect your GitHub repository to Railway
2. Set environment variables:
   - `SECRET_KEY`: Your secret key
   - `BACKEND_CORS_ORIGINS`: Your frontend URL
   - `DATABASE_URL`: `sqlite+aiosqlite:///./financial_planning.db`
3. Deploy with `python start-production.py`

### Render

1. Create new Web Service
2. Use build command: `pip install -r requirements-production.txt`
3. Use start command: `python start-production.py`
4. Set environment variables in Render dashboard

### Heroku

```bash
# Create Heroku app
heroku create your-app-name

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set BACKEND_CORS_ORIGINS='["https://your-frontend.vercel.app"]'

# Deploy
git push heroku main
```

## 🔍 Health Checks

The backend provides several health check endpoints:

- `/health` - Comprehensive health status
- `/status` - Simple service status
- `/` - Basic API information

### Example Health Check Response

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "fastapi": {"available": true, "status": "healthy"},
    "database": {"available": true, "status": "healthy"},
    "api_router": {"available": true, "status": "healthy"}
  },
  "uptime_seconds": 3600,
  "environment": "production"
}
```

## 🔒 Security Considerations

### Production Checklist

- [ ] Changed default `SECRET_KEY`
- [ ] Set `DEBUG=false`
- [ ] Configure proper CORS origins (remove `"*"` if used)
- [ ] Enable HTTPS in production
- [ ] Set up proper logging and monitoring
- [ ] Regular security updates
- [ ] Database backups if using persistent storage

### API Keys (Optional)

For AI features, set these environment variables:
```bash
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

## 📊 Monitoring

### Logs

Application logs are written to stdout in production mode. 

### Performance

Monitor these endpoints for performance:
- Database query times
- Authentication response times
- Simulation execution times

## 🚨 Troubleshooting

### Common Issues

1. **CORS Errors**: Check `BACKEND_CORS_ORIGINS` includes your frontend URL
2. **Database Errors**: Ensure write permissions for SQLite file
3. **Authentication Issues**: Verify `SECRET_KEY` is set and consistent
4. **Import Errors**: Check all dependencies in `requirements-production.txt`

### Debug Mode

For debugging, temporarily set:
```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

Then check `/debug` endpoint for system information.

## 🔄 Updates and Maintenance

### Update Process

1. Pull latest code
2. Install/update dependencies
3. Run database migrations (if any)
4. Restart application

### Database Backups

For SQLite database:
```bash
cp financial_planning.db financial_planning_backup_$(date +%Y%m%d).db
```

## 📞 Support

For deployment issues:
1. Check application logs
2. Verify environment variables
3. Test health check endpoints
4. Check CORS configuration for frontend connectivity

The backend is designed to gracefully degrade if optional services (Redis, external APIs) are unavailable, ensuring core functionality remains operational.