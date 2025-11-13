#!/bin/bash

# UAVcast-Free Development Startup Script
# Starts both backend and frontend in development mode (not as systemd services)
# This is useful for development and testing before deployment

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Starting UAVcast-Free in development mode..."
echo ""

# Check if backend venv exists
if [ ! -d "backend/venv" ]; then
    echo -e "${RED}Backend virtual environment not found!${NC}"
    echo "Run ./deploy.sh first to set up dependencies."
    exit 1
fi

# Check if frontend node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${RED}Frontend dependencies not installed!${NC}"
    echo "Run ./deploy.sh first to set up dependencies."
    exit 1
fi

# Create necessary directories
mkdir -p config logs tmp/hls

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "Stopping services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    exit
}

trap cleanup SIGINT SIGTERM

# Start backend
echo -e "${GREEN}Starting backend...${NC}"
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend-dev.log 2>&1 &
BACKEND_PID=$!
deactivate
cd ..

# Wait for backend to start
sleep 3

# Check if backend started successfully
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${GREEN}Backend started (PID: $BACKEND_PID)${NC}"
else
    echo -e "${RED}Backend failed to start!${NC}"
    echo "Check logs/backend-dev.log for errors"
    exit 1
fi

# Start frontend
echo -e "${GREEN}Starting frontend...${NC}"
cd frontend
npm run dev > ../logs/frontend-dev.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 3

# Check if frontend started successfully
if kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${GREEN}Frontend started (PID: $FRONTEND_PID)${NC}"
else
    echo -e "${RED}Frontend failed to start!${NC}"
    echo "Check logs/frontend-dev.log for errors"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Get IP address
IP_ADDR=$(hostname -I | awk '{print $1}')

echo ""
echo "=========================================="
echo -e "${GREEN}UAVcast-Free is running in dev mode!${NC}"
echo "=========================================="
echo ""
echo "Frontend (Vite Dev Server):"
echo "   http://localhost:5173"
echo "   http://$IP_ADDR:5173"
echo ""
echo "Backend API:"
echo "   http://localhost:8000"
echo "   http://$IP_ADDR:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""
echo "Process IDs:"
echo "   Backend:  $BACKEND_PID"
echo "   Frontend: $FRONTEND_PID"
echo ""
echo "Logs:"
echo "   Backend:  tail -f logs/backend-dev.log"
echo "   Frontend: tail -f logs/frontend-dev.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both services${NC}"
echo ""

# Wait for processes
wait
