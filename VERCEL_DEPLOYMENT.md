# Vercel Deployment Guide

## Overview

This guide covers deploying the AI Financial Planning System frontend to Vercel with optimal configuration for performance, security, and scalability.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI**: Install globally with `npm install -g vercel`
3. **Backend API**: Ensure your backend is deployed and accessible
4. **Domain (Optional)**: Custom domain for production use

## Quick Start

### Option 1: Automatic Deployment (Recommended)

1. **Connect Repository to Vercel**:
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your Git repository
   - Vercel will automatically detect the configuration

2. **Configure Environment Variables**:
   ```bash
   VITE_API_URL=https://your-backend-api.com
   VITE_WS_URL=wss://your-backend-api.com
   VITE_APP_NAME=AI Financial Planning System
   VITE_ENABLE_MOCK_DATA=false
   ```

### Option 2: Manual Deployment

1. **Login to Vercel**:
   ```bash
   vercel login
   ```

2. **Run Deployment Script**:
   ```bash
   ./deploy-vercel.sh
   ```

3. **Follow the prompts** to configure your deployment

## Configuration Details

### vercel.json Configuration

Our `vercel.json` includes:

- **Framework Detection**: Automatically detects Vite
- **Build Configuration**: Optimized build commands and output directory
- **Security Headers**: Comprehensive security headers for production
- **Caching Strategy**: Optimized caching for static assets
- **SPA Routing**: Proper rewrites for single-page application routing

### Environment Variables

Required environment variables in Vercel dashboard:

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API base URL | `https://api.yourapp.com` |
| `VITE_WS_URL` | WebSocket URL | `wss://api.yourapp.com` |
| `VITE_APP_NAME` | Application name | `AI Financial Planning System` |
| `VITE_ENABLE_MOCK_DATA` | Enable mock data (false for prod) | `false` |

### Performance Optimizations

1. **Asset Caching**:
   - Static assets: 1 year cache
   - Images: 1 day cache
   - HTML: No cache (always fresh)

2. **Build Optimizations**:
   - Code splitting with vendor chunks
   - Source maps for debugging
   - Tree shaking for smaller bundles

3. **Security Headers**:
   - Content Security Policy
   - XSS Protection
   - HTTPS enforcement
   - Frame protection

## Deployment Environments

### Preview Deployments

- **Trigger**: Every pull request and branch push
- **URL**: Unique preview URL per deployment
- **Environment**: Uses staging environment variables

### Production Deployments

- **Trigger**: Pushes to main/master branch
- **URL**: Your custom domain or vercel.app subdomain
- **Environment**: Uses production environment variables

## Custom Domain Setup

1. **Add Domain in Vercel**:
   - Go to Project Settings → Domains
   - Add your custom domain
   - Follow DNS configuration instructions

2. **SSL Certificate**:
   - Automatically provisioned by Vercel
   - Includes automatic renewal

3. **DNS Configuration**:
   ```
   Type: A
   Name: @
   Value: 76.76.19.61
   
   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   ```

## Backend Integration

### API Configuration

Update your backend CORS settings to include Vercel domains:

```python
# backend/app/core/config.py
BACKEND_CORS_ORIGINS = [
    "https://your-app.vercel.app",
    "https://your-custom-domain.com",
    "https://*.vercel.app"  # For preview deployments
]
```

### Environment-Specific APIs

For different environments:

- **Development**: `http://localhost:8000`
- **Staging**: `https://staging-api.yourapp.com`
- **Production**: `https://api.yourapp.com`

## Monitoring and Analytics

### Built-in Vercel Analytics

Enable in Project Settings:
- **Web Analytics**: Track page views and performance
- **Speed Insights**: Core Web Vitals monitoring
- **Audience Analytics**: User behavior insights

### Error Tracking

Consider integrating:
- **Sentry**: Error monitoring and performance tracking
- **LogRocket**: Session replay and debugging

### Performance Monitoring

Monitor:
- **Core Web Vitals**: LCP, FID, CLS
- **Bundle Size**: Track JavaScript bundle growth
- **API Response Times**: Backend integration health

## Troubleshooting

### Common Issues

1. **Build Failures**:
   ```bash
   # Check build locally
   cd frontend
   npm run build
   ```

2. **Environment Variables Not Working**:
   - Ensure variables start with `VITE_`
   - Check Vercel dashboard configuration
   - Redeploy after variable changes

3. **API Connection Issues**:
   - Verify CORS configuration
   - Check network tab in browser dev tools
   - Ensure API URL is accessible

4. **Routing Issues**:
   - Verify `rewrites` in `vercel.json`
   - Check React Router configuration

### Debug Commands

```bash
# Check Vercel CLI status
vercel whoami

# View deployment logs
vercel logs <deployment-url>

# List all deployments
vercel list

# Remove deployment
vercel remove <deployment-name>
```

## Security Considerations

### Environment Variables

- **Never commit** `.env.production` to version control
- Use Vercel dashboard for sensitive configuration
- Rotate API keys regularly

### Content Security Policy

Update CSP headers in `vercel.json` if integrating third-party services:

```json
{
  "key": "Content-Security-Policy",
  "value": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self' https://your-api.com"
}
```

### HTTPS Enforcement

- All Vercel deployments use HTTPS by default
- Automatic redirects from HTTP to HTTPS
- HTTP Strict Transport Security (HSTS) enabled

## Cost Optimization

### Vercel Pricing

- **Hobby Plan**: Free tier with limitations
- **Pro Plan**: $20/month per user
- **Enterprise**: Custom pricing

### Optimization Tips

1. **Bundle Size**: Keep JavaScript bundles under 1MB
2. **Image Optimization**: Use Vercel Image Optimization
3. **Edge Caching**: Leverage Vercel Edge Network
4. **Function Usage**: Minimize serverless function calls

## Continuous Deployment

### GitHub Integration

1. **Automatic Deployments**:
   - Main branch → Production
   - Feature branches → Preview

2. **Deployment Hooks**:
   - Configure webhook URLs for external triggers
   - Integrate with external CI/CD systems

3. **Branch Protection**:
   - Require successful deployment before merge
   - Automatic rollback on failure

### Quality Gates

Before production deployment:
- [ ] Build passes successfully
- [ ] All tests pass
- [ ] Security scan completes
- [ ] Performance benchmarks meet thresholds

## Support and Resources

- **Vercel Documentation**: [vercel.com/docs](https://vercel.com/docs)
- **Vercel Discord**: Community support
- **Status Page**: [vercel-status.com](https://vercel-status.com)

## Next Steps After Deployment

1. **Configure Monitoring**: Set up alerts and dashboards
2. **Performance Testing**: Run load tests on deployed application
3. **Security Audit**: Conduct security review
4. **User Acceptance Testing**: Test with real users
5. **Documentation**: Update deployment procedures

---

**Note**: This guide assumes your backend API is already deployed and accessible. Update the environment variables with your actual backend URLs before deploying to production.