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
    ffmpeg \
    modemmanager \
    network-manager \
    nodejs \
    npm \
    libcamera0 \
    libfreetype6

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
echo "Step 5: Installing MediaMTX..."
MEDIAMTX_VERSION="v1.9.3"
ARCH=$(uname -m)

# Determine the correct MediaMTX binary for the architecture
if [ "$ARCH" = "aarch64" ]; then
    MEDIAMTX_ARCH="arm64v8"
elif [ "$ARCH" = "armv7l" ]; then
    MEDIAMTX_ARCH="armv7"
elif [ "$ARCH" = "x86_64" ]; then
    MEDIAMTX_ARCH="amd64"
else
    echo "Warning: Unsupported architecture: $ARCH"
    echo "Defaulting to arm64v8 for Raspberry Pi"
    MEDIAMTX_ARCH="arm64v8"
fi

MEDIAMTX_URL="https://github.com/bluenviron/mediamtx/releases/download/${MEDIAMTX_VERSION}/mediamtx_${MEDIAMTX_VERSION}_linux_${MEDIAMTX_ARCH}.tar.gz"

echo "Downloading MediaMTX ${MEDIAMTX_VERSION} for ${MEDIAMTX_ARCH}..."
echo "URL: ${MEDIAMTX_URL}"

cd /tmp
wget -O mediamtx.tar.gz "$MEDIAMTX_URL"
tar -xzf mediamtx.tar.gz
chmod +x mediamtx
mv mediamtx /usr/local/bin/

# Keep the default config as a template
mkdir -p /opt/uavcast/config
mv mediamtx.yml /opt/uavcast/config/mediamtx.default.yml
rm -f mediamtx.tar.gz LICENSE README.md

echo "MediaMTX installed to /usr/local/bin/mediamtx"
/usr/local/bin/mediamtx --version

echo ""
echo "Step 6: Installing frontend dependencies..."
cd "$PROJECT_DIR/frontend"
npm install

echo ""
echo "Step 7: Building frontend..."
npm run build

echo ""
echo "Step 8: Setting up systemd services..."
cp "$PROJECT_DIR/systemd/uavcast-backend.service" /etc/systemd/system/
cp "$PROJECT_DIR/systemd/uavcast-web.service" /etc/systemd/system/

# Update service files with correct paths
sed -i "s|/path/to/uavcast-free|$PROJECT_DIR|g" /etc/systemd/system/uavcast-backend.service
sed -i "s|/path/to/uavcast-free|$PROJECT_DIR|g" /etc/systemd/system/uavcast-web.service

# Reload systemd
systemctl daemon-reload

echo ""
echo "Step 9: Creating directories..."
mkdir -p /opt/uavcast/config
mkdir -p /opt/uavcast/recordings
mkdir -p /var/log/uavcast

# Set permissions
chown -R $SUDO_USER:$SUDO_USER /opt/uavcast
chown -R $SUDO_USER:$SUDO_USER /var/log/uavcast

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
