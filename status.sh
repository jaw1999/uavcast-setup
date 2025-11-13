#!/bin/bash

# UAVcast-Free Status Script
# Shows the status of all services

echo "UAVcast-Free Status"
echo "===================="
echo ""

# Get IP address
IP_ADDR=$(hostname -I | awk '{print $1}')

# Backend status
echo "Backend Service:"
if systemctl is-active --quiet uavcast-backend.service; then
    echo "   Status: Running"
    echo "   URL:    http://$IP_ADDR:8000"
else
    echo "   Status: Stopped"
fi
echo ""

# Frontend status
echo "Frontend Service:"
if systemctl is-active --quiet uavcast-frontend.service; then
    echo "   Status: Running"
    echo "   URL:    http://$IP_ADDR:3000"
else
    echo "   Status: Stopped"
fi
echo ""

# Check if services are enabled
echo "Auto-start on boot:"
if systemctl is-enabled --quiet uavcast-backend.service; then
    echo "   Backend:  Enabled"
else
    echo "   Backend:  Disabled"
fi
if systemctl is-enabled --quiet uavcast-frontend.service; then
    echo "   Frontend: Enabled"
else
    echo "   Frontend: Disabled"
fi
echo ""

# Show recent logs
echo "Recent Logs (last 5 lines):"
echo "===================="
echo ""
echo "Backend:"
sudo journalctl -u uavcast-backend -n 5 --no-pager | tail -5
echo ""
echo "Frontend:"
sudo journalctl -u uavcast-frontend -n 5 --no-pager | tail -5
echo ""

echo "Commands:"
echo "   Start:       ./start.sh"
echo "   Stop:        ./stop.sh"
echo "   Restart:     ./restart.sh"
echo "   View logs:   sudo journalctl -u uavcast-backend -f"
echo "                sudo journalctl -u uavcast-frontend -f"
