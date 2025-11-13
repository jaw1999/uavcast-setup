#!/bin/bash
set -e

echo "==============================================="
echo "UAVcast-Free Installation Script"
echo "==============================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: Please run as root (use sudo)"
    exit 1
fi

# Check if running on Raspberry Pi OS 64-bit
if [ ! -f /etc/os-release ]; then
    echo "Error: /etc/os-release not found"
    exit 1
fi

# Source OS info
. /etc/os-release

echo "Detected OS: $PRETTY_NAME"

# Check for 64-bit
if [ "$(uname -m)" != "aarch64" ]; then
    echo "Warning: Not running on 64-bit system. UAVcast-Free requires 64-bit Raspberry Pi OS."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "Step 1: Updating system..."
apt-get update

echo ""
echo "Step 2: Installing system dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    v4l-utils \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    libgstreamer1.0-dev \
    modemmanager \
    network-manager \
    nodejs \
    npm

echo ""
echo "Step 3: Setting up Python virtual environment..."
PROJECT_DIR=$(dirname "$(dirname "$(readlink -f "$0")")")
cd "$PROJECT_DIR/backend"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

echo ""
echo "Step 4: Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

deactivate

echo ""
echo "Step 5: Installing frontend dependencies..."
cd "$PROJECT_DIR/frontend"
npm install

echo ""
echo "Step 6: Building frontend..."
npm run build

echo ""
echo "Step 7: Setting up systemd services..."
cp "$PROJECT_DIR/systemd/uavcast-backend.service" /etc/systemd/system/
cp "$PROJECT_DIR/systemd/uavcast-web.service" /etc/systemd/system/

# Update service files with correct paths
sed -i "s|/path/to/uavcast-free|$PROJECT_DIR|g" /etc/systemd/system/uavcast-backend.service
sed -i "s|/path/to/uavcast-free|$PROJECT_DIR|g" /etc/systemd/system/uavcast-web.service

# Reload systemd
systemctl daemon-reload

echo ""
echo "Step 8: Creating directories..."
mkdir -p /etc/uavcast
mkdir -p /var/log/uavcast
mkdir -p /tmp/uavcast/hls

# Set permissions
chown -R $SUDO_USER:$SUDO_USER /etc/uavcast
chown -R $SUDO_USER:$SUDO_USER /var/log/uavcast
chown -R $SUDO_USER:$SUDO_USER /tmp/uavcast

echo ""
echo "==============================================="
echo "Installation Complete!"
echo "==============================================="
echo ""
echo "To start UAVcast-Free:"
echo "  sudo systemctl enable --now uavcast-backend"
echo "  sudo systemctl enable --now uavcast-web"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u uavcast-backend -f"
echo "  sudo journalctl -u uavcast-web -f"
echo ""
echo "Access web interface at:"
echo "  http://$(hostname -I | awk '{print $1}'):8000"
echo "  or http://raspberrypi.local:8000"
echo ""
echo "Optional: Install VPN clients"
echo "  ZeroTier: curl -s https://install.zerotier.com | sudo bash"
echo "  Tailscale: curl -fsSL https://tailscale.com/install.sh | sh"
echo "  WireGuard: sudo apt-get install -y wireguard"
echo ""
