#!/bin/bash
set -e

# UAVcast-Free Raspberry Pi Deployment Script
# This script installs all dependencies and sets up the system

echo "=========================================="
echo "UAVcast-Free Deployment Script"
echo "=========================================="
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Working directory: $SCRIPT_DIR"
echo ""

# Update system
echo "Updating system packages..."
sudo apt-get update

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    build-essential \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    v4l-utils \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev

# Stop ModemManager if it exists (it can interfere with serial ports)
if systemctl is-active --quiet ModemManager; then
    echo "Stopping ModemManager..."
    sudo systemctl stop ModemManager
    sudo systemctl disable ModemManager
fi

# Install Node.js 20.x
echo "Installing Node.js 20.x..."
if ! command -v node &> /dev/null || [ $(node -v | cut -d'v' -f2 | cut -d'.' -f1) -lt 20 ]; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

echo "Node.js version: $(node -v)"
echo "npm version: $(npm -v)"

# Create Python virtual environment
echo "Setting up Python virtual environment..."
if [ ! -d "backend/venv" ]; then
    cd backend
    python3 -m venv venv
    cd ..
fi

# Activate virtual environment and install Python dependencies
echo "Installing Python dependencies..."
cd backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ..

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Build frontend for production
echo "Building frontend..."
cd frontend
npm run build
cd ..

# Create necessary directories
echo "Creating required directories..."
mkdir -p config
mkdir -p logs
mkdir -p tmp/hls

# Set up user permissions for serial ports
echo "Setting up serial port permissions..."
sudo usermod -a -G dialout $USER
sudo usermod -a -G video $USER

# Create systemd service for backend
echo "Creating systemd service..."
sudo tee /etc/systemd/system/uavcast-backend.service > /dev/null <<EOF
[Unit]
Description=UAVcast-Free Backend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR/backend
Environment="PATH=$SCRIPT_DIR/backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$SCRIPT_DIR/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for frontend (serve built files with a simple HTTP server)
sudo tee /etc/systemd/system/uavcast-frontend.service > /dev/null <<EOF
[Unit]
Description=UAVcast-Free Frontend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR/frontend
ExecStart=/usr/bin/npx serve -s dist -l 3000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Enable services to start on boot
echo "Enabling services to start on boot..."
sudo systemctl enable uavcast-backend.service
sudo systemctl enable uavcast-frontend.service

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "   1. Reboot your Raspberry Pi (for group permissions to take effect)"
echo "   2. After reboot, services will start automatically"
echo "   3. Access the UI at: http://$(hostname -I | awk '{print $1}'):3000"
echo ""
echo "Manual control:"
echo "   Start:   ./start.sh"
echo "   Stop:    ./stop.sh"
echo "   Status:  ./status.sh"
echo ""
echo "View logs:"
echo "   Backend:  sudo journalctl -u uavcast-backend -f"
echo "   Frontend: sudo journalctl -u uavcast-frontend -f"
echo ""

read -p "Would you like to reboot now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Rebooting..."
    sudo reboot
fi
