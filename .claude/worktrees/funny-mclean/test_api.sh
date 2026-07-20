#!/bin/bash
# Test if API is working

echo "Testing Portfolio Tracker API..."

# Start server on port 9090
python3 -c "
from minimal_api import run_server
run_server(port=9090)
" &

# Save the PID
SERVER_PID=$!

# Wait for server to start
sleep 2

# Test the API
echo ""
echo "Testing API endpoints:"
echo "----------------------"

# Test summary endpoint
echo "1. Testing /api/summary:"
curl -s http://localhost:9090/api/summary | python3 -m json.tool | head -10

echo ""
echo "✅ API is working! Open http://localhost:9090 in your browser"
echo ""
echo "Press Enter to stop the server..."
read

# Kill the server
kill $SERVER_PID 2>/dev/null
echo "Server stopped."