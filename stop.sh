#!/bin/bash

# UAVcast-Free Stop Script
# Stops both backend and frontend services

echo "Stopping UAVcast-Free..."
echo ""

# Stop frontend service
echo "Stopping frontend..."
sudo systemctl stop uavcast-frontend.service

# Stop backend service
echo "Stopping backend..."
sudo systemctl stop uavcast-backend.service

# Wait a moment
sleep 1

# Check status
echo ""
echo "Service Status:"
echo "===================="

# Backend status
if systemctl is-active --quiet uavcast-backend.service; then
    echo "Backend:  Still running"
else
    echo "Backend:  Stopped"
fi

# Frontend status
if systemctl is-active --quiet uavcast-frontend.service; then
    echo "Frontend: Still running"
else
    echo "Frontend: Stopped"
fi

echo ""

if ! systemctl is-active --quiet uavcast-backend.service && ! systemctl is-active --quiet uavcast-frontend.service; then
    echo "UAVcast-Free stopped successfully"
else
    echo "Some services are still running"
fi
