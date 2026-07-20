#!/bin/bash

echo "🔍 Checking Vercel Deployment Status..."
echo "========================================"

# List recent deployments
echo -e "\n📋 Recent Deployments:"
vercel ls --yes 2>/dev/null | head -10

# Get the most recent deployment URL
LATEST_DEPLOYMENT=$(vercel ls --yes 2>/dev/null | grep -m 1 "https://" | awk '{print $2}')

if [ ! -z "$LATEST_DEPLOYMENT" ]; then
    echo -e "\n🔗 Latest Deployment: $LATEST_DEPLOYMENT"
    
    # Check if it's an error or ready
    STATUS=$(vercel ls --yes 2>/dev/null | grep -m 1 "https://" | awk '{print $3}')
    echo "📊 Status: $STATUS"
    
    if [ "$STATUS" = "●" ]; then
        STATE=$(vercel ls --yes 2>/dev/null | grep -m 1 "https://" | awk '{print $4}')
        echo "📊 State: $STATE"
    fi
fi

echo -e "\n💡 To see detailed build logs, visit:"
echo "   https://vercel.com/rmehta2500-4681s-projects/ai-financial-planner"

echo -e "\n🛠️  To deploy manually, run:"
echo "   vercel --prod"

echo -e "\n📝 To check build locally, run:"
echo "   cd frontend && npm run build"