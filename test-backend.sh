#!/bin/bash

# Test Backend Deployment Script
# Usage: ./test-backend.sh https://your-backend-url.onrender.com

BACKEND_URL=${1:-"https://ai-financial-planner-backend.onrender.com"}

echo "🔍 Testing Backend at: $BACKEND_URL"
echo "================================================"

# Test health endpoint
echo -n "Testing /health endpoint... "
HEALTH=$(curl -s "$BACKEND_URL/health" | python3 -m json.tool 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ SUCCESS"
    echo "$HEALTH"
else
    echo "❌ FAILED"
fi

echo ""
echo -n "Testing /simulate endpoint... "
SIMULATE=$(curl -s -X POST "$BACKEND_URL/simulate" \
    -H "Content-Type: application/json" \
    -d '{
        "initial_amount": 100000,
        "monthly_contribution": 1000,
        "years": 10,
        "expected_return": 0.07
    }' | python3 -m json.tool 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "✅ SUCCESS"
    echo "$SIMULATE" | head -10
else
    echo "❌ FAILED"
fi

echo ""
echo -n "Testing API docs... "
DOCS=$(curl -s -I "$BACKEND_URL/docs" | grep "200 OK")
if [ "$DOCS" ]; then
    echo "✅ SUCCESS - API docs available at $BACKEND_URL/docs"
else
    echo "⚠️  API docs might not be accessible"
fi

echo ""
echo "================================================"
echo "📊 Backend Deployment Status:"
if [ "$HEALTH" ]; then
    echo "✅ Backend is LIVE and responding!"
    echo "🔗 API URL: $BACKEND_URL"
    echo "📚 API Docs: $BACKEND_URL/docs"
    echo ""
    echo "Next step: Update Vercel environment variables with this URL"
else
    echo "⚠️  Backend might still be deploying. Wait 2-3 minutes and try again."
fi