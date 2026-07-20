# AI Financial Planner Backend - Quick Deployment Guide

## 🚀 OPTION 1: Render.com (Recommended - Free Tier)

### Step 1: Create GitHub Repository
1. Create a new GitHub repository for your backend
2. Push the following files:
   - `simple_backend.py`
   - `requirements_simple.txt`
   - `Dockerfile.simple`
   - `render.yaml`

### Step 2: Deploy to Render.com
1. Go to [render.com](https://render.com) and sign up/login
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Use these settings:
   - **Name**: `ai-financial-planner-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements_simple.txt`
   - **Start Command**: `python simple_backend.py`
   - **Instance Type**: `Free`

### Step 3: Environment Variables
Add this environment variable in Render.com dashboard:
- `PYTHON_VERSION`: `3.11.0`

### Step 4: Access Your API
Your backend will be available at:
`https://ai-financial-planner-backend.onrender.com`

---

## 🚀 OPTION 2: Railway.app (Alternative)

### Step 1: Install Railway CLI
```bash
npm install -g @railway/cli
```

### Step 2: Deploy
```bash
cd backend
railway login
railway init
railway add
railway deploy
```

### Step 3: Set Environment Variables
```bash
railway variables set PYTHON_VERSION=3.11.0
```

---

## 🚀 OPTION 3: Fly.io (Advanced)

### Step 1: Install Fly CLI
```bash
# macOS
brew install flyctl

# Or download from https://fly.io/docs/hands-on/install-flyctl/
```

### Step 2: Setup and Deploy
```bash
cd backend
fly auth login
fly launch --dockerfile Dockerfile.simple
fly deploy
```

---

## 🚀 OPTION 4: Docker + Any Cloud Provider

### Build and Run Locally
```bash
cd backend
docker build -f Dockerfile.simple -t ai-financial-planner .
docker run -p 8000:8000 ai-financial-planner
```

### Push to Registry
```bash
docker tag ai-financial-planner your-registry/ai-financial-planner
docker push your-registry/ai-financial-planner
```

---

## 🧪 Testing Your Deployment

Once deployed, test these endpoints:

### Health Check
```
GET https://your-backend-url.com/health
```

### API Documentation
```
GET https://your-backend-url.com/docs
```

### Test Simulation
```
POST https://your-backend-url.com/simulate
Content-Type: application/json

{
  "age": 30,
  "income": 75000,
  "savings": 500,
  "risk_tolerance": "moderate"
}
```

### Frontend Compatible Endpoint
```
POST https://your-backend-url.com/api/v1/simulations/monte-carlo
Content-Type: application/json

{
  "age": 30,
  "income": 75000,
  "savings": 500,
  "risk_tolerance": "moderate"
}
```

---

## 🔗 Update Frontend Configuration

Once your backend is deployed, update your frontend's API configuration:

In your frontend code, change the API base URL to your deployed backend:
```javascript
const API_BASE_URL = "https://your-backend-url.onrender.com";
```

---

## 🎯 Quick Commands for Immediate Deployment

### Render.com (Fastest)
1. Create GitHub repo with backend files
2. Go to render.com → New Web Service
3. Connect repo, use Python environment
4. Build: `pip install -r requirements_simple.txt`
5. Start: `python simple_backend.py`
6. Deploy!

### Your backend will be live in ~5 minutes! 🎉

---

## 🆘 Troubleshooting

### Common Issues:
1. **Port binding error**: Make sure `PORT` environment variable is used
2. **CORS errors**: Verify CORS origins include your frontend URL
3. **Module not found**: Check `requirements_simple.txt` includes all dependencies
4. **Build timeout**: Use the simple requirements file, not the full one

### Support:
- Check deployment logs in your platform dashboard
- Test locally first: `python simple_backend.py`
- Verify endpoints work at `/docs` URL

---

## 📋 File Checklist

Make sure you have these files:
- ✅ `simple_backend.py` (main application)
- ✅ `requirements_simple.txt` (minimal dependencies)
- ✅ `Dockerfile.simple` (containerization)
- ✅ `render.yaml` (Render.com config)

Ready to deploy! Choose your platform and go live! 🚀