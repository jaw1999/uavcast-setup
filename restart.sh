#!/bin/bash

# UAVcast-Free Restart Script
# Restarts both backend and frontend services

echo "Restarting UAVcast-Free..."
echo ""

# Restart backend service
echo "Restarting backend..."
sudo systemctl restart uavcast-backend.service

# Wait a moment for backend to start
sleep 2

# Restart frontend service
echo "Restarting frontend..."
sudo systemctl restart uavcast-frontend.service

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
    echo "UAVcast-Free restarted successfully!"
    echo ""
    echo "Access the UI at:"
    echo "   http://$IP_ADDR:3000"
else
    echo "Some services failed to restart. Check logs above."
fi
