# Quick Render.com Deployment Guide for AI Financial Planner

## Overview
Deploy your FastAPI backend to Render.com in under 5 minutes. The backend is already configured and ready to deploy.

## Prerequisites
- GitHub repository with your code
- Render.com account (free signup)

## Deployment Steps

### 1. Push Code to GitHub
```bash
cd "/Users/rahulmehta/Desktop/Financial Planning"
git add .
git commit -m "feat: prepare backend for Render.com deployment"
git push origin main
```

### 2. Deploy on Render.com

1. **Go to [render.com](https://render.com) and sign up/login**

2. **Click "New +" → "Web Service"**

3. **Connect GitHub Repository:**
   - Click "Connect a repository"
   - Select your financial planning repository
   - Click "Connect"

4. **Configure Service:**
   ```
   Name: ai-financial-planner-backend
   Branch: main
   Root Directory: backend
   Runtime: Python 3
   Build Command: pip install -r requirements_simple.txt
   Start Command: python simple_backend.py
   Instance Type: Free
   ```

5. **Environment Variables:**
   Click "Advanced" → "Add Environment Variable":
   ```
   PYTHON_VERSION = 3.11.0
   FRONTEND_URL = https://ai-financial-planner-zeta.vercel.app
   DEBUG = false
   PORT = 10000
   ```

6. **Deploy:**
   - Click "Create Web Service"
   - Wait 3-5 minutes for deployment
   - Your backend will be live at: `https://ai-financial-planner-backend-xxxx.onrender.com`

### 3. Test Your Deployment

Once deployed, test these endpoints:

**Health Check:**
```
https://your-backend-url.onrender.com/health
```

**API Documentation:**
```
https://your-backend-url.onrender.com/docs
```

**Test Simulation:**
```bash
curl -X POST "https://your-backend-url.onrender.com/simulate" \
  -H "Content-Type: application/json" \
  -d '{"age": 30, "income": 75000, "savings": 1000, "risk_tolerance": "moderate"}'
```

### 4. Update Frontend Configuration

Update your frontend's API configuration with the new backend URL:

**In `/frontend/src/config/api.ts`:**
```typescript
const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? 'https://your-backend-url.onrender.com'  // Replace with your actual URL
  : 'http://localhost:8000';

export const API_CONFIG = {
  BASE_URL: API_BASE_URL,
  // ... rest of config
};
```

**Redeploy your frontend** to Vercel with the updated configuration.

## Backend Features Ready
Your deployed backend includes:

✅ FastAPI with automatic OpenAPI docs  
✅ CORS configured for your Vercel frontend  
✅ Monte Carlo financial simulations  
✅ Health check endpoint  
✅ Production-ready logging  
✅ Environment variable support  

## API Endpoints Available

- `GET /` - API information
- `GET /health` - Health check
- `POST /simulate` - Run financial simulation
- `POST /api/v1/simulations/monte-carlo` - Monte Carlo simulation (frontend endpoint)
- `GET /docs` - Interactive API documentation
- `GET /redoc` - Alternative API documentation

## Troubleshooting

**If deployment fails:**
1. Check the build logs in Render dashboard
2. Verify all files exist in the backend directory
3. Check that `requirements_simple.txt` contains all dependencies

**If CORS errors occur:**
1. Verify your frontend URL is in the CORS origins
2. Check that FRONTEND_URL environment variable is set correctly
3. Make sure both frontend and backend are using HTTPS in production

**Cold starts (first request slow):**
This is normal on the free tier. The app "sleeps" after 15 minutes of inactivity.

## Next Steps

1. **Get your backend URL** from the Render dashboard
2. **Update your frontend configuration** with the new backend URL
3. **Test the connection** between frontend and backend
4. **Monitor performance** in the Render dashboard

## Files Already Configured

The following files are already set up for deployment:

- `/backend/simple_backend.py` - Main application with CORS configured
- `/backend/requirements_simple.txt` - Minimal dependencies
- `/backend/render.yaml` - Render.com configuration
- `/backend/deploy-render.sh` - Deployment helper script

## Support

Your backend is now live and ready to serve your AI Financial Planner frontend! 

If you encounter issues, check the Render.com logs or refer to the comprehensive `BACKEND_DEPLOYMENT.md` guide.