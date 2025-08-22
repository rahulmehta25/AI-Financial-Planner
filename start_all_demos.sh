#!/bin/bash

echo "🚀 AI Financial Planning System - Complete Demo Launcher"
echo "========================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a port is available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}❌ Port $1 is already in use${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Port $1 is available${NC}"
        return 0
    fi
}

# Function to start backend demo
start_backend() {
    echo -e "\n${BLUE}🔧 Starting Backend Demo...${NC}"
    cd backend
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}⚠️  Virtual environment not found. Creating one...${NC}"
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies if needed
    echo -e "${BLUE}📦 Installing/updating dependencies...${NC}"
    pip install fastapi uvicorn numpy pydantic "python-jose[cryptography]" "passlib[bcrypt]" python-multipart seaborn pandas scipy matplotlib numba reportlab redis sqlalchemy alembic rich plotext
    
    # Start the working demo in background
    echo -e "${BLUE}🚀 Starting backend server...${NC}"
    python working_demo.py > backend.log 2>&1 &
    BACKEND_PID=$!
    
    # Wait for backend to start
    echo -e "${YELLOW}⏳ Waiting for backend to start...${NC}"
    sleep 15
    
    # Check if backend is running
    if curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✅ Backend is running on http://localhost:8000${NC}"
        echo -e "${GREEN}📚 API Docs: http://localhost:8000/docs${NC}"
        echo $BACKEND_PID > backend.pid
    else
        echo -e "${RED}❌ Backend failed to start${NC}"
        echo -e "${YELLOW}📋 Check backend.log for details${NC}"
        return 1
    fi
    
    cd ..
}

# Function to start frontend demo
start_frontend() {
    echo -e "\n${BLUE}🎨 Starting Frontend Demo...${NC}"
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}⚠️  Dependencies not installed. Installing...${NC}"
        npm install --legacy-peer-deps
    fi
    
    # Start frontend in background
    echo -e "${BLUE}🚀 Starting frontend server...${NC}"
    npm run dev > frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    # Wait for frontend to start
    echo -e "${YELLOW}⏳ Waiting for frontend to start...${NC}"
    sleep 10
    
    # Check if frontend is running
    if curl -s http://localhost:3000 > /dev/null; then
        echo -e "${GREEN}✅ Frontend is running on http://localhost:3000${NC}"
        echo $FRONTEND_PID > frontend.pid
    else
        echo -e "${RED}❌ Frontend failed to start${NC}"
        echo -e "${YELLOW}📋 Check frontend.log for details${NC}"
        return 1
    fi
    
    cd ..
}

# Function to start mobile demo
start_mobile() {
    echo -e "\n${BLUE}📱 Starting Mobile Demo...${NC}"
    cd mobile/demo-app
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}⚠️  Dependencies not installed. Installing...${NC}"
        npm install
    fi
    
    # Start mobile demo in background
    echo -e "${BLUE}🚀 Starting mobile demo...${NC}"
    npm start > mobile.log 2>&1 &
    MOBILE_PID=$!
    
    echo -e "${GREEN}✅ Mobile demo started${NC}"
    echo -e "${YELLOW}📱 Scan QR code when it appears${NC}"
    echo $MOBILE_PID > mobile.pid
    
    cd ../..
}

# Function to start ML demo
start_ml_demo() {
    echo -e "\n${BLUE}🤖 Starting ML Simulation Demo...${NC}"
    cd backend
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Start ML demo in background
    echo -e "${BLUE}🚀 Starting ML simulation demo...${NC}"
    python ml_simulation_demo.py > ml_demo.log 2>&1 &
    ML_PID=$!
    
    echo -e "${GREEN}✅ ML demo started${NC}"
    echo $ML_PID > ml_demo.pid
    
    cd ..
}

# Function to show status
show_status() {
    echo -e "\n${BLUE}📊 Demo Status${NC}"
    echo "=================="
    
    if [ -f "backend/backend.pid" ]; then
        BACKEND_PID=$(cat backend/backend.pid)
        if ps -p $BACKEND_PID > /dev/null; then
            echo -e "${GREEN}✅ Backend: Running (PID: $BACKEND_PID)${NC}"
        else
            echo -e "${RED}❌ Backend: Not running${NC}"
        fi
    else
        echo -e "${RED}❌ Backend: Not started${NC}"
    fi
    
    if [ -f "frontend/frontend.pid" ]; then
        FRONTEND_PID=$(cat frontend/frontend.pid)
        if ps -p $FRONTEND_PID > /dev/null; then
            echo -e "${GREEN}✅ Frontend: Running (PID: $FRONTEND_PID)${NC}"
        else
            echo -e "${RED}❌ Frontend: Not running${NC}"
        fi
    else
        echo -e "${RED}❌ Frontend: Not started${NC}"
    fi
    
    if [ -f "backend/ml_demo.pid" ]; then
        ML_PID=$(cat backend/ml_demo.pid)
        if ps -p $ML_PID > /dev/null; then
            echo -e "${GREEN}✅ ML Demo: Running (PID: $ML_PID)${NC}"
        else
            echo -e "${RED}❌ ML Demo: Not running${NC}"
        fi
    else
        echo -e "${RED}❌ ML Demo: Not started${NC}"
    fi
    
    if [ -f "mobile/demo-app/mobile.pid" ]; then
        MOBILE_PID=$(cat mobile/demo-app/mobile.pid)
        if ps -p $MOBILE_PID > /dev/null; then
            echo -e "${GREEN}✅ Mobile Demo: Running (PID: $MOBILE_PID)${NC}"
        else
            echo -e "${RED}❌ Mobile Demo: Not running${NC}"
        fi
    else
        echo -e "${RED}❌ Mobile Demo: Not started${NC}"
    fi
}

# Function to stop all demos
stop_all() {
    echo -e "\n${RED}🛑 Stopping all demos...${NC}"
    
    # Stop backend
    if [ -f "backend/backend.pid" ]; then
        BACKEND_PID=$(cat backend/backend.pid)
        kill $BACKEND_PID 2>/dev/null
        rm -f backend/backend.pid
        echo -e "${YELLOW}🛑 Backend stopped${NC}"
    fi
    
    # Stop frontend
    if [ -f "frontend/frontend.pid" ]; then
        FRONTEND_PID=$(cat frontend/frontend.pid)
        kill $FRONTEND_PID 2>/dev/null
        rm -f frontend/frontend.pid
        echo -e "${YELLOW}🛑 Frontend stopped${NC}"
    fi
    
    # Stop ML demo
    if [ -f "backend/ml_demo.pid" ]; then
        ML_PID=$(cat backend/ml_demo.pid)
        kill $ML_PID 2>/dev/null
        rm -f backend/ml_demo.pid
        echo -e "${YELLOW}🛑 ML Demo stopped${NC}"
    fi
    
    # Stop mobile demo
    if [ -f "mobile/demo-app/mobile.pid" ]; then
        MOBILE_PID=$(cat mobile/demo-app/mobile.pid)
        kill $MOBILE_PID 2>/dev/null
        rm -f mobile/demo-app/mobile.pid
        echo -e "${YELLOW}🛑 Mobile Demo stopped${NC}"
    fi
    
    echo -e "${GREEN}✅ All demos stopped${NC}"
}

# Main menu
case "${1:-start}" in
    "start")
        echo -e "${GREEN}🚀 Starting all demos...${NC}"
        
        # Check ports
        check_port 8000 || exit 1
        check_port 3000 || exit 1
        
        start_backend
        start_frontend
        start_ml_demo
        start_mobile
        
        echo -e "\n${GREEN}🎉 All demos started!${NC}"
        show_status
        
        echo -e "\n${BLUE}🔗 Quick Access:${NC}"
        echo -e "  📚 Backend API: http://localhost:8000/docs"
        echo -e "  🎨 Frontend: http://localhost:3000"
        echo -e "  📱 Mobile: Scan QR code from mobile demo"
        echo -e "  🤖 ML Demo: Check ml_demo.log for output"
        ;;
    
    "status")
        show_status
        ;;
    
    "stop")
        stop_all
        ;;
    
    "restart")
        stop_all
        sleep 2
        $0 start
        ;;
    
    *)
        echo -e "${BLUE}Usage: $0 [start|status|stop|restart]${NC}"
        echo -e "  start   - Start all demos"
        echo -e "  status  - Show demo status"
        echo -e "  stop    - Stop all demos"
        echo -e "  restart - Restart all demos"
        exit 1
        ;;
esac
