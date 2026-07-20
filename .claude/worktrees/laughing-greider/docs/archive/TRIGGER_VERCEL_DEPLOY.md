# How to Trigger Vercel Deployment

## Why Vercel Isn't Auto-Deploying

Your Vercel project might not be auto-deploying because:
1. GitHub integration might be disconnected
2. Auto-deploy might be disabled
3. Build might be failing silently

## Solution: Manual Trigger

### Option 1: Via Vercel Dashboard (Recommended)
1. Go to your [Vercel Dashboard](https://vercel.com/dashboard)
2. Find your `AI-Financial-Planner` project
3. Click on the project
4. Go to **Settings** → **Git**
5. Check if GitHub repo is connected
6. If connected, click **"Redeploy"** button on the latest deployment

### Option 2: Via Vercel CLI
```bash
# Install Vercel CLI if you haven't
npm i -g vercel

# In the project root
cd /Users/rahulmehta/Desktop/AI-ML\ Projects/AI-Financial-Planner

# Deploy
vercel --prod
```

### Option 3: Force Push to Trigger
```bash
# Make a small change to force deployment
echo "# Deploy trigger $(date)" >> README.md
git add README.md
git commit -m "chore: trigger Vercel deployment"
git push origin master
```

## Check These Settings in Vercel Dashboard

1. **Git Integration**:
   - Settings → Git → Ensure GitHub is connected
   - Check if "Auto-deploy" is enabled for master branch

2. **Environment Variables** (Already added by you):
   ```
   NEXT_PUBLIC_SUPABASE_URL=https://tqxhvrsdroafvigbgaxx.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
   ```

3. **Build Settings**:
   - Framework Preset: Vite
   - Build Command: `cd frontend && npm run build`
   - Output Directory: `frontend/dist`

## If Build Is Failing

Check the build logs in Vercel:
1. Go to project → Deployments
2. Click on the failed deployment
3. Check "Build Logs" for errors

Common issues:
- Missing dependencies
- TypeScript errors
- Environment variable issues

## Quick Fix Command

Run this to ensure everything is committed and pushed:
```bash
cd /Users/rahulmehta/Desktop/AI-ML\ Projects/AI-Financial-Planner
git status
git add -A
git commit -m "fix: trigger Vercel deployment with Supabase integration"
git push origin master
```

Then check Vercel dashboard for the deployment.