# Vercel Deployment Checklist

## Pre-Deployment Checklist

### ✅ Backend Prerequisites

- [ ] Backend API is deployed and accessible via HTTPS
- [ ] WebSocket endpoint supports WSS (secure WebSockets)
- [ ] CORS is configured to allow requests from Vercel domains
- [ ] Health check endpoint is available (`/health`)
- [ ] API endpoints are properly documented and tested

### ✅ Frontend Prerequisites

- [ ] All dependencies are installed (`npm install`)
- [ ] Local build succeeds (`npm run build`)
- [ ] All TypeScript errors are resolved
- [ ] Linting passes (`npm run lint`)
- [ ] No console errors in browser
- [ ] Application works correctly in preview mode

### ✅ Configuration Files

- [ ] `vercel.json` is created and configured
- [ ] `frontend/.env.production` contains production URLs
- [ ] All required environment variables are defined
- [ ] Security headers are properly configured
- [ ] SPA routing rewrites are set up

### ✅ Environment Variables

- [ ] `VITE_API_URL` points to production backend
- [ ] `VITE_WS_URL` points to production WebSocket
- [ ] `VITE_APP_NAME` is set correctly
- [ ] `VITE_ENABLE_MOCK_DATA` is set to `false`
- [ ] No sensitive data in frontend environment variables

## Deployment Steps

### Step 1: Validate Configuration

```bash
# Run the validation script
node validate-vercel-config.js

# Should show all green checkmarks
```

### Step 2: Login to Vercel

```bash
vercel login
# Follow the authentication prompts
```

### Step 3: Deploy to Preview (Recommended First)

```bash
# Deploy preview version for testing
vercel

# Or use the deployment script
./deploy-vercel.sh
# Choose option 1 for preview deployment
```

### Step 4: Test Preview Deployment

- [ ] Visit the preview URL provided by Vercel
- [ ] Test all major application features
- [ ] Verify API connectivity
- [ ] Check browser console for errors
- [ ] Test responsive design on different devices
- [ ] Verify WebSocket connections work

### Step 5: Configure Environment Variables in Vercel Dashboard

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project
3. Go to Settings → Environment Variables
4. Add all required variables for Production environment:

```
VITE_API_URL=https://your-backend-api.com
VITE_WS_URL=wss://your-backend-api.com
VITE_APP_NAME=AI Financial Planning System
VITE_ENABLE_MOCK_DATA=false
NODE_ENV=production
```

### Step 6: Deploy to Production

```bash
# Deploy to production
vercel --prod

# Or use the deployment script
./deploy-vercel.sh
# Choose option 2 for production deployment
```

## Post-Deployment Checklist

### ✅ Functional Testing

- [ ] Home page loads correctly
- [ ] Navigation works properly
- [ ] User authentication flows work
- [ ] API calls are successful
- [ ] Real-time features (WebSocket) function
- [ ] All major user flows are tested

### ✅ Performance Testing

- [ ] Page load times are acceptable (< 3 seconds)
- [ ] Core Web Vitals are in good ranges
- [ ] Bundle size is optimized
- [ ] Assets are properly cached
- [ ] No unnecessary network requests

### ✅ Security Testing

- [ ] HTTPS is enforced
- [ ] Security headers are present
- [ ] No sensitive data exposed in browser
- [ ] CORS is properly configured
- [ ] No mixed content warnings

### ✅ Browser Compatibility

- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile browsers (iOS Safari, Chrome Mobile)

### ✅ Monitoring Setup

- [ ] Vercel Analytics enabled
- [ ] Error tracking configured (Sentry, LogRocket, etc.)
- [ ] Performance monitoring in place
- [ ] Uptime monitoring configured

## Domain Configuration (Optional)

### Custom Domain Setup

If using a custom domain:

1. Add domain in Vercel Dashboard:
   - Go to Project Settings → Domains
   - Add your custom domain
   - Copy the DNS configuration

2. Update DNS records:
   ```
   Type: A, Name: @, Value: 76.76.19.61
   Type: CNAME, Name: www, Value: cname.vercel-dns.com
   ```

3. Update backend CORS configuration to include new domain

4. Test domain propagation:
   ```bash
   nslookup your-domain.com
   curl -I https://your-domain.com
   ```

## Rollback Plan

In case of deployment issues:

### Immediate Rollback

```bash
# List recent deployments
vercel list

# Promote a previous deployment to production
vercel promote [deployment-url] --scope [team-name]
```

### Environment Variable Rollback

1. Go to Vercel Dashboard → Settings → Environment Variables
2. Update problematic variables
3. Trigger new deployment

### Code Rollback

```bash
# Revert to previous commit
git revert [commit-hash]
git push

# Vercel will automatically deploy the reverted code
```

## Troubleshooting Common Issues

### Build Failures

- Check Vercel build logs
- Verify all dependencies are in `package.json`
- Ensure TypeScript compilation succeeds
- Check for missing environment variables

### Runtime Errors

- Check browser console for JavaScript errors
- Verify API endpoints are accessible
- Check CORS configuration
- Validate environment variable values

### Performance Issues

- Analyze bundle size with Vercel Analytics
- Check for unnecessary re-renders
- Optimize images and assets
- Review network requests in browser dev tools

## Continuous Deployment

### GitHub Integration

For automatic deployments:

1. Connect GitHub repository to Vercel project
2. Configure branch settings:
   - Main/master branch → Production
   - Feature branches → Preview deployments
3. Set up branch protection rules
4. Configure deployment notifications

### Quality Gates

Before merging to main:
- [ ] All tests pass
- [ ] Code review completed
- [ ] Preview deployment tested
- [ ] Performance benchmarks met

## Support Resources

- **Vercel Documentation**: [vercel.com/docs](https://vercel.com/docs)
- **Vercel Discord**: Community support channel
- **Status Page**: [vercel-status.com](https://vercel-status.com)
- **GitHub Issues**: Project-specific issues

## Final Verification

After completing all steps:

- [ ] Production URL is accessible
- [ ] All features work as expected
- [ ] Performance metrics are acceptable
- [ ] Monitoring is active
- [ ] Team is notified of successful deployment
- [ ] Documentation is updated

---

**Remember**: Always test in preview environment before deploying to production!