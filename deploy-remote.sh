#!/bin/bash
set -e

# UAVcast-Free Remote Deployment Script
# Run this from your local machine to deploy to Raspberry Pi

echo "=========================================="
echo "UAVcast-Free Remote Deployment"
echo "=========================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Prompt for Raspberry Pi details
echo "Enter Raspberry Pi connection details:"
echo ""
read -p "Raspberry Pi IP address: " PI_IP
read -p "Username (default: pi): " PI_USER
PI_USER=${PI_USER:-pi}
read -sp "Password: " PI_PASSWORD
echo ""
echo ""

# Test SSH connection
echo "Testing SSH connection to $PI_USER@$PI_IP..."
sshpass -p "$PI_PASSWORD" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $PI_USER@$PI_IP "echo 'Connection successful'" || {
    echo "Failed to connect to Raspberry Pi"
    echo "Please check:"
    echo "  - IP address is correct"
    echo "  - Raspberry Pi is powered on and connected to network"
    echo "  - Username and password are correct"
    echo "  - SSH is enabled on the Pi (sudo raspi-config → Interface Options → SSH)"
    exit 1
}
echo ""

# Ask if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo "sshpass is not installed on your system"
    echo "Installing sshpass..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install hudochenkov/sshpass/sshpass
    else
        sudo apt-get install -y sshpass
    fi
fi

# Create temporary directory name
REMOTE_DIR="/home/$PI_USER/uavcast-free"
TEMP_ARCHIVE="/tmp/uavcast-free-deploy-$(date +%s).tar.gz"

echo "Creating deployment archive..."
# Create archive excluding node_modules, venv, and other unnecessary files
tar -czf "$TEMP_ARCHIVE" \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='.git' \
    --exclude='dist' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='logs' \
    --exclude='tmp' \
    --exclude='*.log' \
    -C "$SCRIPT_DIR/.." "$(basename "$SCRIPT_DIR")"

echo "Archive created: $TEMP_ARCHIVE"
echo ""

# Copy archive to Pi
echo "Uploading to Raspberry Pi..."
sshpass -p "$PI_PASSWORD" scp "$TEMP_ARCHIVE" $PI_USER@$PI_IP:/tmp/uavcast-deploy.tar.gz
echo "Upload complete"
echo ""

# Execute installation on Pi
echo "Running installation on Raspberry Pi..."
echo "=========================================="
echo ""

sshpass -p "$PI_PASSWORD" ssh -o StrictHostKeyChecking=no $PI_USER@$PI_IP bash << EOF
set -e

echo "Extracting archive..."
cd /home/$PI_USER
rm -rf uavcast-free
tar -xzf /tmp/uavcast-deploy.tar.gz
rm /tmp/uavcast-deploy.tar.gz

echo "Files extracted to $REMOTE_DIR"
echo ""

cd uavcast-free

# Make scripts executable
chmod +x *.sh

echo "=========================================="
echo "Installing Dependencies"
echo "=========================================="
echo ""

# Update system
echo "Updating system packages..."
sudo apt-get update

# Install system dependencies
echo "Installing system dependencies..."
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
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
    libgstreamer-plugins-base1.0-dev \
    wireguard \
    wireguard-tools

# Install VPN clients
echo "Installing VPN clients..."

# Install ZeroTier
if ! command -v zerotier-cli &> /dev/null; then
    echo "Installing ZeroTier..."
    curl -s https://install.zerotier.com | sudo bash
    echo "ZeroTier installed"
else
    echo "ZeroTier already installed"
fi

# Install Tailscale
if ! command -v tailscale &> /dev/null; then
    echo "Installing Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh
    echo "Tailscale installed"
else
    echo "Tailscale already installed"
fi

echo "WireGuard installed"
echo ""

# Stop ModemManager
if systemctl is-active --quiet ModemManager 2>/dev/null; then
    echo "Stopping ModemManager..."
    sudo systemctl stop ModemManager
    sudo systemctl disable ModemManager
fi

# Install Node.js 20.x
echo "Installing Node.js 20.x..."
if ! command -v node &> /dev/null || [ \$(node -v | cut -d'v' -f2 | cut -d'.' -f1) -lt 20 ]; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

echo "Node.js version: \$(node -v)"
echo "npm version: \$(npm -v)"
echo ""

# Create Python virtual environment
echo "Setting up Python virtual environment..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
echo "Installing Python dependencies..."
pip install -r requirements.txt
deactivate
cd ..
echo ""

# Install frontend dependencies with retry
echo "Installing frontend dependencies..."
cd frontend

# Try npm install with retries
MAX_RETRIES=3
RETRY_COUNT=0
SUCCESS=false

while [ \$RETRY_COUNT -lt \$MAX_RETRIES ] && [ "\$SUCCESS" = "false" ]; do
    echo "Attempt \$((RETRY_COUNT + 1)) of \$MAX_RETRIES..."

    if npm install --legacy-peer-deps --verbose; then
        SUCCESS=true
        echo "npm install successful"
    else
        RETRY_COUNT=\$((RETRY_COUNT + 1))
        if [ \$RETRY_COUNT -lt \$MAX_RETRIES ]; then
            echo "npm install failed, retrying in 10 seconds..."
            sleep 10
        else
            echo "npm install failed after \$MAX_RETRIES attempts"
            echo "This is usually due to network issues."
            echo "You can manually complete the installation by running:"
            echo "  cd $REMOTE_DIR/frontend"
            echo "  npm install --legacy-peer-deps"
            echo "  npm run build"
            exit 1
        fi
    fi
done

echo ""

# Build frontend
echo "Building frontend..."
if npm run build; then
    echo "Frontend built successfully"
else
    echo "Frontend build failed"
    exit 1
fi
cd ..
echo ""

# Create necessary directories
echo "Creating required directories..."
mkdir -p config
mkdir -p logs
mkdir -p tmp/hls

# Set up user permissions
echo "Setting up permissions..."
sudo usermod -a -G dialout $PI_USER
sudo usermod -a -G video $PI_USER

# Create systemd services
echo "Creating systemd services..."
sudo tee /etc/systemd/system/uavcast-backend.service > /dev/null <<SERVICE
[Unit]
Description=UAVcast-Free Backend
After=network.target

[Service]
Type=simple
User=$PI_USER
WorkingDirectory=$REMOTE_DIR/backend
Environment="PATH=$REMOTE_DIR/backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$REMOTE_DIR/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

sudo tee /etc/systemd/system/uavcast-frontend.service > /dev/null <<SERVICE
[Unit]
Description=UAVcast-Free Frontend
After=network.target uavcast-backend.service

[Service]
Type=simple
User=$PI_USER
WorkingDirectory=$REMOTE_DIR/frontend
ExecStart=/usr/bin/npx serve -s dist -l 3000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

# Reload and enable services
sudo systemctl daemon-reload
sudo systemctl enable uavcast-backend.service
sudo systemctl enable uavcast-frontend.service

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Starting services..."
sudo systemctl start uavcast-backend.service
sudo systemctl start uavcast-frontend.service

# Wait for services to start
sleep 3

# Check status
if systemctl is-active --quiet uavcast-backend.service && systemctl is-active --quiet uavcast-frontend.service; then
    echo "Services started successfully!"
    echo ""
    echo "Access the UI at:"
    echo "   http://$PI_IP:3000"
    echo "   http://\$(hostname -I | awk '{print \$1}'):3000"
    echo ""
    echo "Backend API at:"
    echo "   http://$PI_IP:8000"
    echo ""
else
    echo "Some services failed to start"
    echo "Check logs with:"
    echo "   sudo journalctl -u uavcast-backend -n 50"
    echo "   sudo journalctl -u uavcast-frontend -n 50"
fi

echo "Management commands:"
echo "   Start:   cd $REMOTE_DIR && ./start.sh"
echo "   Stop:    cd $REMOTE_DIR && ./stop.sh"
echo "   Status:  cd $REMOTE_DIR && ./status.sh"
echo "   Restart: cd $REMOTE_DIR && ./restart.sh"
echo ""

EOF

# Cleanup local temp file
rm "$TEMP_ARCHIVE"

echo ""
echo "=========================================="
echo "Deployment Successful!"
echo "=========================================="
echo ""
echo "Your UAVcast-Free installation is ready at:"
echo "   http://$PI_IP:3000"
echo ""
echo "To manage services via SSH:"
echo "   ssh $PI_USER@$PI_IP"
echo "   cd $REMOTE_DIR"
echo "   ./status.sh    # Check status"
echo "   ./restart.sh   # Restart services"
echo ""
