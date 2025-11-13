#!/bin/bash

# UAVcast-Free Startup Script
# Starts both backend and frontend services

echo "Starting UAVcast-Free..."
echo ""

# Start backend service
echo "Starting backend..."
sudo systemctl start uavcast-backend.service

# Wait a moment for backend to start
sleep 2

# Start frontend service
echo "Starting frontend..."
sudo systemctl start uavcast-frontend.service

# Wait a moment for services to initialize
sleep 2

# Check status
echo ""
echo "Service Status:"
echo "===================="

# Backend status
if systemctl is-active --quiet uavcast-backend.service; then
    echo "Backend:  Running"
else
    echo "Backend:  Failed"
    echo "   View logs: sudo journalctl -u uavcast-backend -n 50"
fi

# Frontend status
if systemctl is-active --quiet uavcast-frontend.service; then
    echo "Frontend: Running"
else
    echo "Frontend: Failed"
    echo "   View logs: sudo journalctl -u uavcast-frontend -n 50"
fi

echo ""

# Get IP address
IP_ADDR=$(hostname -I | awk '{print $1}')

if systemctl is-active --quiet uavcast-backend.service && systemctl is-active --quiet uavcast-frontend.service; then
    echo "UAVcast-Free is running!"
    echo ""
    echo "Access the UI at:"
    echo "   http://$IP_ADDR:3000"
    echo "   http://localhost:3000"
    echo ""
    echo "Backend API at:"
    echo "   http://$IP_ADDR:8000"
    echo ""
else
    echo "Some services failed to start. Check logs above."
fi
