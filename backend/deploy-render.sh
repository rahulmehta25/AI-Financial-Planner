#!/bin/bash

# Quick Render.com Deployment Script for AI Financial Planning Backend
# This script prepares your repository for deployment on Render.com

set -e

echo "🚀 AI Financial Planning Backend - Render.com Deployment Setup"
echo "=============================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "simple_backend.py" ]; then
    echo -e "${RED}Error: simple_backend.py not found. Please run this script from the backend directory.${NC}"
    exit 1
fi

# Check if git is initialized
if [ ! -d ".git" ]; then
    cd ..
    if [ ! -d ".git" ]; then
        echo -e "${YELLOW}Git repository not found. Initializing...${NC}"
        git init
        echo -e "${GREEN}✓ Git repository initialized${NC}"
    fi
    cd backend
fi

echo -e "${GREEN}✓ Found backend files${NC}"

# Verify required files exist
echo "Checking required files..."

files=("simple_backend.py" "requirements_simple.txt" "render.yaml")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file exists${NC}"
    else
        echo -e "${RED}✗ $file missing${NC}"
        exit 1
    fi
done

# Check if requirements_simple.txt has the right dependencies
echo "Validating requirements..."
if grep -q "fastapi" requirements_simple.txt && grep -q "uvicorn" requirements_simple.txt; then
    echo -e "${GREEN}✓ Required dependencies found${NC}"
else
    echo -e "${RED}✗ Missing required dependencies in requirements_simple.txt${NC}"
    exit 1
fi

# Generate a secure secret key if needed
if [ ! -f "../.env.production.example" ]; then
    echo "Generating secure secret key..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    cat > "../.env.production.example" << EOF
# Production Environment Variables for Render.com
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=$SECRET_KEY
PORT=8000

# Add your frontend URL here after deployment
BACKEND_CORS_ORIGINS=["https://your-frontend.vercel.app"]

# Optional API keys (add your own)
OPENAI_API_KEY=your-openai-key-here
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key-here
EOF
    echo -e "${GREEN}✓ Created .env.production.example with secure secret key${NC}"
fi

# Update render.yaml with current date
echo "Updating render.yaml..."
sed -i.bak "s/# Your GitHub repo URL will go here/# Updated $(date)/" render.yaml
echo -e "${GREEN}✓ Updated render.yaml${NC}"

# Check git status
cd ..
echo ""
echo "Current git status:"
git status --porcelain

# Commit changes if there are any
if [ -n "$(git status --porcelain)" ]; then
    echo ""
    echo -e "${YELLOW}You have uncommitted changes. Committing them now...${NC}"
    
    git add .
    git commit -m "feat: prepare backend for Render.com deployment

- Updated deployment configuration
- Added production environment template
- Verified all required files for deployment"
    
    echo -e "${GREEN}✓ Changes committed${NC}"
else
    echo -e "${GREEN}✓ Repository is clean${NC}"
fi

echo ""
echo "=============================================================="
echo -e "${GREEN}🎉 Ready for Render.com deployment!${NC}"
echo ""
echo "Next steps:"
echo "1. Push to GitHub:"
echo "   ${YELLOW}git push origin main${NC}"
echo ""
echo "2. Go to https://render.com and:"
echo "   - Click 'New +' → 'Web Service'"
echo "   - Connect your GitHub repository"
echo "   - Use these settings:"
echo "     ${YELLOW}Name: ai-financial-planner-backend${NC}"
echo "     ${YELLOW}Branch: main${NC}"
echo "     ${YELLOW}Root Directory: backend${NC}"
echo "     ${YELLOW}Build Command: pip install -r requirements_simple.txt${NC}"
echo "     ${YELLOW}Start Command: python simple_backend.py${NC}"
echo ""
echo "3. Add environment variables:"
echo "   - Copy values from .env.production.example"
echo "   - Set PYTHON_VERSION=3.11.0"
echo ""
echo "4. Deploy and test:"
echo "   - Your API will be available at: https://your-app-name.onrender.com"
echo "   - Test health: https://your-app-name.onrender.com/health"
echo "   - API docs: https://your-app-name.onrender.com/docs"
echo ""
echo -e "${GREEN}For detailed instructions, see BACKEND_DEPLOYMENT.md${NC}"
echo ""

# Show current repository URL if available
REPO_URL=$(git config --get remote.origin.url 2>/dev/null || echo "Not set")
if [ "$REPO_URL" != "Not set" ]; then
    echo "Repository URL: ${YELLOW}$REPO_URL${NC}"
else
    echo -e "${YELLOW}Don't forget to add a GitHub remote:${NC}"
    echo "git remote add origin https://github.com/yourusername/your-repo.git"
fi

echo ""