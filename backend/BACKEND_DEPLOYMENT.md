# Backend Deployment Guide - AI Financial Planning System

This comprehensive guide will walk you through deploying the AI Financial Planning backend to various cloud platforms with step-by-step instructions.

## 📋 Table of Contents

1. [Quick Start - Render.com (Recommended)](#quick-start---rendercom-recommended)
2. [Alternative Platforms](#alternative-platforms)
3. [Environment Variables Configuration](#environment-variables-configuration)
4. [Frontend Connection Setup](#frontend-connection-setup)
5. [Testing Your Deployment](#testing-your-deployment)
6. [Troubleshooting](#troubleshooting)
7. [Production Optimization](#production-optimization)

## 🚀 Quick Start - Render.com (Recommended)

Render.com provides the easiest deployment experience with automatic HTTPS, continuous deployment, and excellent free tier support.

### Prerequisites

- GitHub account with your code pushed to a repository
- Render.com account (free signup)
- 5 minutes of your time

### Step 1: Prepare Your Repository

1. **Ensure your code is on GitHub:**
   ```bash
   git add .
   git commit -m "feat: prepare backend for deployment"
   git push origin main
   ```

2. **Verify required files are in your backend directory:**
   - `render.yaml` ✓ (already configured)
   - `simple_backend.py` ✓ (main application)
   - `requirements_simple.txt` ✓ (lightweight dependencies)

### Step 2: Deploy on Render.com

1. **Go to [Render.com](https://render.com) and sign up/login**

2. **Click "New +" → "Web Service"**

3. **Connect your GitHub repository:**
   - Select your financial planning repository
   - Click "Connect"

4. **Configure the service:**
   ```
   Name: ai-financial-planner-backend
   Branch: main (or your default branch)
   Root Directory: backend
   Runtime: Python 3
   Build Command: pip install -r requirements_simple.txt
   Start Command: python simple_backend.py
   ```

5. **Set Environment Variables:**
   Click "Advanced" and add these environment variables:
   ```
   PYTHON_VERSION=3.11.0
   PORT=8000
   ```

6. **Deploy:**
   - Click "Create Web Service"
   - Wait 3-5 minutes for deployment
   - Your backend will be live at: `https://your-app-name.onrender.com`

### Step 3: Verify Deployment

Once deployed, test these endpoints:

1. **Health Check:**
   ```
   GET https://your-app-name.onrender.com/health
   ```

2. **API Documentation:**
   ```
   https://your-app-name.onrender.com/docs
   ```

3. **Root Endpoint:**
   ```
   GET https://your-app-name.onrender.com/
   ```

**✅ Success!** Your backend is now live and ready to connect to your frontend.

## 🌐 Alternative Platforms

### Railway (Simple & Modern)

Railway offers excellent developer experience with automatic deployments.

1. **Go to [Railway.app](https://railway.app)**
2. **Click "Start a New Project" → "Deploy from GitHub"**
3. **Select your repository**
4. **Railway will auto-detect Python and deploy**
5. **Add environment variables in the Variables tab**

**Configuration:**
```
Build Command: pip install -r backend/requirements_simple.txt
Start Command: cd backend && python simple_backend.py
Port: 8000
```

### Heroku (Mature Platform)

1. **Install Heroku CLI and login:**
   ```bash
   heroku login
   ```

2. **Create Heroku app:**
   ```bash
   heroku create your-app-name
   ```

3. **Create Procfile in backend directory:**
   ```
   web: python simple_backend.py
   ```

4. **Deploy:**
   ```bash
   git subtree push --prefix backend heroku main
   ```

### Google Cloud Run (Serverless)

1. **Build and push Docker image:**
   ```bash
   cd backend
   gcloud builds submit --tag gcr.io/PROJECT_ID/financial-backend
   ```

2. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy --image gcr.io/PROJECT_ID/financial-backend --platform managed
   ```

### AWS (Advanced)

Use AWS Elastic Beanstalk for easy deployment:

1. **Install EB CLI:**
   ```bash
   pip install awsebcli
   ```

2. **Initialize and deploy:**
   ```bash
   cd backend
   eb init -p python-3.11 financial-backend
   eb create production
   eb deploy
   ```

## 🔧 Environment Variables Configuration

### Required Environment Variables

For production deployment, configure these essential variables:

```bash
# Application Configuration
ENVIRONMENT=production
DEBUG=false
PORT=8000

# Security (Generate secure values)
SECRET_KEY=your-super-secure-secret-key-min-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Origins (Add your frontend URL)
BACKEND_CORS_ORIGINS=["https://your-frontend.vercel.app","https://your-domain.com"]

# Optional - External APIs
OPENAI_API_KEY=your-openai-key-optional
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key-optional
```

### Platform-Specific Environment Variable Setup

#### Render.com
1. Go to your service dashboard
2. Click "Environment" tab
3. Add variables one by one
4. Save changes (triggers auto-redeploy)

#### Railway
1. Select your project
2. Go to "Variables" tab
3. Add variables in key=value format
4. Deploy automatically triggers

#### Heroku
```bash
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set ENVIRONMENT="production"
heroku config:set DEBUG="false"
```

### Generating Secure Values

**Secret Key Generation:**
```python
# Run this in Python to generate a secure secret key
import secrets
print(secrets.token_urlsafe(32))
```

**Or use OpenSSL:**
```bash
openssl rand -base64 32
```

## 🔗 Frontend Connection Setup

### Update Frontend Configuration

1. **Update your frontend's API configuration file:**

   **For Vite/React (src/config/api.ts):**
   ```typescript
   const API_BASE_URL = process.env.NODE_ENV === 'production'
     ? 'https://your-backend-app.onrender.com'  // Your deployed backend URL
     : 'http://localhost:8000';

   export const API_CONFIG = {
     BASE_URL: API_BASE_URL,
     TIMEOUT: 10000,
     RETRY_ATTEMPTS: 3
   };
   ```

2. **Update Environment Variables:**

   **For Vercel deployment (.env.production):**
   ```bash
   VITE_API_BASE_URL=https://your-backend-app.onrender.com
   VITE_ENVIRONMENT=production
   ```

3. **Update CORS Origins on Backend:**
   
   Make sure your backend allows requests from your frontend domain:
   ```python
   # In simple_backend.py, update CORS origins:
   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "https://your-frontend.vercel.app",  # Add your frontend URL
           "https://your-custom-domain.com",    # Add custom domains
           "http://localhost:3000",             # Keep for local dev
           "http://localhost:5173",             # Keep for local dev
       ],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

4. **Redeploy both frontend and backend** after making these changes.

## 🧪 Testing Your Deployment

### Automated Health Checks

Create this simple test script (`test_deployment.py`):

```python
import requests
import time

def test_backend_health(base_url):
    """Test backend health and endpoints"""
    
    print(f"Testing backend at: {base_url}")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"✅ Root endpoint: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
    
    # Test simulation endpoint
    try:
        test_data = {
            "age": 30,
            "income": 75000,
            "savings": 1000,
            "risk_tolerance": "moderate"
        }
        response = requests.post(f"{base_url}/simulate", json=test_data, timeout=10)
        print(f"✅ Simulation endpoint: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Success probability: {result['success_probability']}%")
    except Exception as e:
        print(f"❌ Simulation endpoint failed: {e}")
    
    return True

# Test your deployment
if __name__ == "__main__":
    # Replace with your actual backend URL
    BACKEND_URL = "https://your-app-name.onrender.com"
    test_backend_health(BACKEND_URL)
```

### Manual Testing Steps

1. **Test API Documentation:**
   - Visit: `https://your-backend.onrender.com/docs`
   - Try the interactive API docs

2. **Test Health Endpoint:**
   ```bash
   curl https://your-backend.onrender.com/health
   ```

3. **Test Simulation Endpoint:**
   ```bash
   curl -X POST https://your-backend.onrender.com/simulate \
     -H "Content-Type: application/json" \
     -d '{"age": 30, "income": 75000, "savings": 1000, "risk_tolerance": "moderate"}'
   ```

4. **Test Frontend Connection:**
   - Open your deployed frontend
   - Try creating a financial simulation
   - Check browser developer tools for any CORS errors

## 🛠 Troubleshooting

### Common Issues and Solutions

#### 1. **Deployment Fails - "Build Command Failed"**

**Problem:** Build process fails during dependency installation.

**Solutions:**
```bash
# Option A: Use minimal requirements
# Make sure you're using requirements_simple.txt instead of requirements.txt

# Option B: If you need full requirements, fix dependency conflicts
pip install --upgrade pip
pip install -r requirements.txt --no-deps
```

#### 2. **App Crashes - "Application Error"**

**Problem:** App starts but crashes immediately.

**Solutions:**
1. **Check logs:**
   - Render: Go to service dashboard → Logs tab
   - Railway: Click on service → View logs
   - Heroku: `heroku logs --tail`

2. **Common fixes:**
   ```python
   # Ensure your app binds to correct host/port
   if __name__ == "__main__":
       import os
       port = int(os.environ.get("PORT", 8000))
       uvicorn.run("simple_backend:app", host="0.0.0.0", port=port)
   ```

#### 3. **CORS Errors in Frontend**

**Problem:** Frontend can't connect to backend due to CORS policy.

**Solution:**
```python
# In your backend, update CORS middleware:
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend-domain.vercel.app",  # Add your actual frontend URL
        "http://localhost:3000",  # Keep for development
        "*"  # Only for development/testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 4. **Slow Cold Starts**

**Problem:** First request takes long time (common on free tiers).

**Solutions:**
1. **Add a health check cron job:**
   ```bash
   # Use a service like cron-job.org to ping your app every 14 minutes
   curl https://your-app.onrender.com/health
   ```

2. **Implement keep-alive endpoint:**
   ```python
   @app.get("/keep-alive")
   async def keep_alive():
       return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
   ```

#### 5. **Environment Variable Issues**

**Problem:** App can't read environment variables.

**Solutions:**
1. **Verify variables are set correctly on platform**
2. **Add fallback values:**
   ```python
   import os
   
   SECRET_KEY = os.environ.get("SECRET_KEY", "development-key-change-in-production")
   DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
   ```

#### 6. **Import Errors**

**Problem:** "Module not found" errors.

**Solutions:**
1. **Check Python path:**
   ```python
   import sys
   sys.path.append('/app')
   ```

2. **Use absolute imports:**
   ```python
   # Instead of: from .models import User
   # Use: from app.models import User
   ```

### Platform-Specific Troubleshooting

#### Render.com
- **Logs:** Service dashboard → Logs tab
- **Common fix:** Ensure `render.yaml` is correctly configured
- **Free tier limits:** 512MB RAM, sleeps after 15 minutes of inactivity

#### Railway
- **Logs:** Project dashboard → Service → Logs
- **Common fix:** Check if `PORT` environment variable is set
- **Free tier limits:** 500 hours/month, $5 credit

#### Heroku
- **Logs:** `heroku logs --tail`
- **Common fix:** Create proper `Procfile`
- **Free tier limits:** App sleeps after 30 minutes of inactivity

## 🚀 Production Optimization

### Performance Enhancements

1. **Use Production WSGI Server:**
   ```python
   # Install gunicorn
   pip install gunicorn
   
   # Start command
   gunicorn simple_backend:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. **Add Caching:**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def expensive_simulation(age, income, savings, risk):
       # Cache expensive calculations
       return calculate_simulation(age, income, savings, risk)
   ```

3. **Add Request Logging:**
   ```python
   import logging
   
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)
   
   @app.middleware("http")
   async def log_requests(request, call_next):
       start_time = time.time()
       response = await call_next(request)
       process_time = time.time() - start_time
       logger.info(f"{request.method} {request.url} - {response.status_code} - {process_time:.4f}s")
       return response
   ```

### Security Hardening

1. **Environment-based Configuration:**
   ```python
   import os
   from typing import Literal
   
   ENVIRONMENT: Literal["development", "production"] = os.getenv("ENVIRONMENT", "development")
   DEBUG = ENVIRONMENT == "development"
   
   if ENVIRONMENT == "production":
       # Production-only security settings
       app.add_middleware(
           TrustedHostMiddleware,
           allowed_hosts=["your-domain.com", "*.onrender.com"]
       )
   ```

2. **Rate Limiting:**
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   
   @app.post("/simulate")
   @limiter.limit("10/minute")
   async def simulate(request: Request, data: SimulationRequest):
       # Your simulation logic
       pass
   ```

### Database Integration (Optional)

If you want to add persistent storage:

1. **Add PostgreSQL (Render.com):**
   - Go to Render dashboard → New → PostgreSQL
   - Copy connection string to environment variables
   - Update your app to use database

2. **Simple database integration:**
   ```python
   import os
   import asyncpg
   
   DATABASE_URL = os.getenv("DATABASE_URL")
   
   if DATABASE_URL:
       # Connect to database
       pool = await asyncpg.create_pool(DATABASE_URL)
   ```

## 📈 Monitoring and Maintenance

### Basic Monitoring Setup

1. **Add Health Check Logging:**
   ```python
   @app.get("/health")
   async def health_check():
       """Enhanced health check with system info"""
       import psutil
       import sys
       
       return {
           "status": "healthy",
           "version": "1.0.0",
           "timestamp": datetime.utcnow().isoformat(),
           "system": {
               "python_version": sys.version.split()[0],
               "cpu_usage": psutil.cpu_percent(),
               "memory_usage": psutil.virtual_memory().percent
           }
       }
   ```

2. **Error Tracking (Optional):**
   ```python
   import sentry_sdk
   from sentry_sdk.integrations.fastapi import FastApiIntegration
   
   if os.getenv("SENTRY_DSN"):
       sentry_sdk.init(
           dsn=os.getenv("SENTRY_DSN"),
           integrations=[FastApiIntegration()],
           environment=os.getenv("ENVIRONMENT", "development")
       )
   ```

### Backup and Recovery

For production systems with databases:

1. **Automated Backups:**
   - Render: Automatic daily backups on paid plans
   - Railway: Manual backups via CLI
   - Heroku: `heroku pg:backups:schedule`

2. **Configuration Backup:**
   ```bash
   # Export environment variables
   render env:get > backup.env  # Render
   railway variables > backup.env  # Railway
   heroku config > backup.env  # Heroku
   ```

## 🎯 Next Steps

After successful deployment:

1. **Set up monitoring** for uptime and performance
2. **Configure automated backups** if using a database
3. **Set up CI/CD pipeline** for automatic deployments
4. **Add custom domain** if needed
5. **Scale resources** based on usage patterns
6. **Implement comprehensive logging** and error tracking

## 📚 Additional Resources

- [Render.com Documentation](https://render.com/docs)
- [Railway Documentation](https://docs.railway.app)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Python Production Best Practices](https://docs.python-guide.org/scenarios/web/)

---

**🎉 Congratulations!** Your AI Financial Planning backend is now deployed and ready to serve users. The system is designed to be highly scalable, secure, and maintainable.

For support or questions, refer to your chosen platform's documentation or create an issue in your repository.