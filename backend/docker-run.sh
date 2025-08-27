#!/bin/bash
# One-click Docker deployment for AI Financial Planner Backend

echo "🚀 Starting AI Financial Planner Backend with Docker..."
echo "========================================================"

# Build the Docker image
echo "📦 Building Docker image..."
docker build -f Dockerfile.simple -t ai-financial-planner-backend .

# Stop any existing container
echo "🛑 Stopping existing container (if any)..."
docker stop ai-financial-planner-backend-container 2>/dev/null || true
docker rm ai-financial-planner-backend-container 2>/dev/null || true

# Run the container
echo "🚀 Starting container..."
docker run -d \
    --name ai-financial-planner-backend-container \
    -p 8000:8000 \
    -e PORT=8000 \
    ai-financial-planner-backend

# Wait a moment for startup
sleep 3

echo ""
echo "✅ Backend is now running!"
echo "========================================"
echo "🌐 API Base URL: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "❤️  Health Check: http://localhost:8000/health"
echo "🎮 Test Simulation: POST http://localhost:8000/simulate"
echo "========================================"
echo ""

# Test the deployment
echo "🧪 Testing deployment..."
sleep 2

echo "Testing health endpoint..."
curl -s http://localhost:8000/health | python3 -m json.tool

echo ""
echo "🎉 Your backend is LIVE and ready to connect to your frontend!"
echo "Update your frontend API configuration to use: http://localhost:8000"