# Vercel Environment Variables Template

## Required Environment Variables

Configure these environment variables in your Vercel project dashboard:

### API Configuration

```bash
# Backend API URL - Replace with your actual backend URL
VITE_API_URL=https://your-backend-api.herokuapp.com

# WebSocket URL - Replace with your actual WebSocket URL
VITE_WS_URL=wss://your-backend-api.herokuapp.com
```

### Application Configuration

```bash
# Application name displayed in the UI
VITE_APP_NAME=AI Financial Planning System

# Disable mock data in production
VITE_ENABLE_MOCK_DATA=false

# Build environment
NODE_ENV=production
```

## Environment-Specific Values

### Development/Staging
```bash
VITE_API_URL=https://staging-api.yourfinancialplanner.com
VITE_WS_URL=wss://staging-api.yourfinancialplanner.com
VITE_ENABLE_MOCK_DATA=false
```

### Production
```bash
VITE_API_URL=https://api.yourfinancialplanner.com
VITE_WS_URL=wss://api.yourfinancialplanner.com
VITE_ENABLE_MOCK_DATA=false
```

## How to Set Environment Variables in Vercel

### Method 1: Vercel Dashboard

1. Go to your project in [Vercel Dashboard](https://vercel.com/dashboard)
2. Click on your project
3. Go to "Settings" tab
4. Click "Environment Variables" in the sidebar
5. Add each variable with:
   - **Key**: Variable name (e.g., `VITE_API_URL`)
   - **Value**: Variable value (e.g., `https://api.yourfinancialplanner.com`)
   - **Environments**: Select Production, Preview, and/or Development

### Method 2: Vercel CLI

```bash
# Set production environment variable
vercel env add VITE_API_URL production

# Set preview environment variable
vercel env add VITE_API_URL preview

# List all environment variables
vercel env ls

# Remove environment variable
vercel env rm VITE_API_URL production
```

## Backend Integration Checklist

Ensure your backend is configured to accept requests from Vercel:

### CORS Configuration

Update your backend CORS settings to include your Vercel URLs:

```python
# Example for FastAPI backend
BACKEND_CORS_ORIGINS = [
    "https://your-app.vercel.app",
    "https://your-custom-domain.com",
    "https://*.vercel.app",  # For preview deployments
]
```

### SSL/HTTPS

- Ensure your backend supports HTTPS
- WebSocket connections must use WSS (secure WebSockets)
- Update any HTTP URLs to HTTPS

### Health Check Endpoint

Verify your backend has a health check endpoint:

```bash
curl -X GET "https://your-backend-api.com/health"
```

## Testing Environment Variables

### Local Testing

1. Create `.env.production.local` in your frontend directory:
   ```bash
   VITE_API_URL=https://your-backend-api.com
   VITE_WS_URL=wss://your-backend-api.com
   ```

2. Build and test locally:
   ```bash
   cd frontend
   npm run build
   npm run preview
   ```

### Production Testing

After deployment, check that environment variables are working:

1. Open browser developer tools
2. Go to Network tab
3. Verify API calls are going to the correct URL
4. Check Console for any CORS or connection errors

## Security Considerations

### Variable Naming

- All frontend environment variables must start with `VITE_`
- Never include sensitive API keys or secrets in frontend environment variables
- Frontend environment variables are publicly accessible in the built application

### API Keys and Secrets

❌ **DO NOT** put these in frontend environment variables:
- Database passwords
- API keys for backend services
- JWT secrets
- Third-party service credentials

✅ **DO** put these in frontend environment variables:
- Public API URLs
- Application configuration
- Feature flags
- Non-sensitive configuration values

## Troubleshooting

### Common Issues

1. **Variables not loading**:
   - Ensure variable names start with `VITE_`
   - Check spelling and capitalization
   - Redeploy after adding variables

2. **API connection failures**:
   - Verify backend URL is accessible
   - Check CORS configuration
   - Ensure HTTPS/WSS protocols

3. **Build failures**:
   - Check that required variables are set
   - Validate environment variable values
   - Review build logs in Vercel dashboard

### Debugging Commands

```bash
# Check environment variables during build
echo $VITE_API_URL

# Test API connectivity
curl -X GET "https://your-backend-api.com/health"

# View Vercel deployment logs
vercel logs [deployment-url]
```

## Example Complete Configuration

Here's an example of a complete Vercel environment variable setup:

```bash
# Production Environment Variables
VITE_API_URL=https://api.financialplanner.com
VITE_WS_URL=wss://api.financialplanner.com
VITE_APP_NAME=AI Financial Planning System
VITE_ENABLE_MOCK_DATA=false
NODE_ENV=production

# Optional: Analytics and Monitoring
VITE_SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
VITE_ANALYTICS_ID=your-analytics-id

# Optional: Feature Flags
VITE_ENABLE_ADVANCED_FEATURES=true
VITE_ENABLE_DARK_MODE=true
```

Remember to replace all example URLs with your actual backend URLs!