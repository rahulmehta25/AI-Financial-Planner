#!/bin/bash

# Financial Planning System - Vercel Deployment Script
# This script helps prepare and deploy the frontend to Vercel

set -e

echo "🚀 Financial Planning System - Vercel Deployment"
echo "================================================"

# Check if we're in the right directory
if [ ! -f "vercel.json" ]; then
    echo "❌ Error: vercel.json not found. Please run this script from the project root."
    exit 1
fi

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Navigate to frontend directory for local build test
cd frontend

echo "🔍 Checking frontend dependencies..."
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

echo "🧪 Testing local build..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Local build successful!"
else
    echo "❌ Local build failed. Please fix build errors before deploying."
    exit 1
fi

# Go back to root
cd ..

echo ""
echo "🌍 Deployment Options:"
echo "1. Preview deployment (recommended for testing)"
echo "2. Production deployment"
echo ""
read -p "Choose deployment type (1 or 2): " deployment_type

case $deployment_type in
    1)
        echo "🚀 Deploying preview to Vercel..."
        vercel --local-config vercel.json
        ;;
    2)
        echo "🚀 Deploying to production..."
        vercel --prod --local-config vercel.json
        ;;
    *)
        echo "❌ Invalid option. Please choose 1 or 2."
        exit 1
        ;;
esac

echo ""
echo "✅ Deployment completed!"
echo ""
echo "📋 Post-deployment checklist:"
echo "1. Update environment variables in Vercel dashboard:"
echo "   - VITE_API_URL: Your backend API URL"
echo "   - VITE_WS_URL: Your backend WebSocket URL"
echo "2. Test the deployed application"
echo "3. Configure custom domain if needed"
echo "4. Set up monitoring and alerts"
echo ""
echo "🔗 Vercel Dashboard: https://vercel.com/dashboard"