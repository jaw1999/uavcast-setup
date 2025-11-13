# UAVcast-Free

Open-source companion computer software for UAVs enabling long-range operations over cellular networks.

## Features

- **MAVLink Telemetry Routing**: Bidirectional telemetry forwarding between flight controller and ground stations
- **Live Video Streaming**: WebM/VP8 video streaming with in-browser preview
- **VPN Integration**: User-managed VPN support (ZeroTier, Tailscale, WireGuard)
- **Network Management**: Modem detection, signal monitoring, and connectivity testing
- **Configuration Profiles**: Save and load complete system configurations
- **Live Telemetry Display**: Real-time flight data (altitude, speed, battery, GPS)
- **Flight Map**: Interactive map showing drone position and flight path
- **Web Interface**: Modern React-based UI with real-time updates
- **System Monitoring**: CPU, memory, temperature, and network statistics

## Hardware Requirements

- **Computer**: Raspberry Pi Zero 2W, 3, 4, or 5 (or any Linux SBC)
- **OS**: Raspberry Pi OS 64-bit (Bookworm or newer) or Ubuntu 22.04+
- **Flight Controller**: MAVLink-compatible (Pixhawk, APM, Cube, etc.)
- **Modem**: USB LTE modem (optional, for cellular connectivity)
- **Camera** (optional): USB webcam or Raspberry Pi Camera Module

## Quick Start

### Prerequisites

Install system dependencies:

```bash
# Update package list
sudo apt-get update

# Install Python 3.11+
sudo apt-get install -y python3 python3-pip python3-venv

# Install Node.js 18+ (for frontend development)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install GStreamer (for video streaming)
sudo apt-get install -y \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav

# Install optional tools
sudo apt-get install -y \
    v4l-utils \
    network-manager \
    modemmanager
```

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/uavcast-free.git
cd uavcast-free

# Install backend dependencies
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Running in Development

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Access the web interface at: `http://localhost:5173`

## VPN Setup

UAVcast-Free requires you to manage your own VPN infrastructure. The app provides configuration interfaces for three popular VPN solutions.

### ZeroTier

1. Create account at [zerotier.com](https://zerotier.com)
2. Create a private network and note the **Network ID** (16-character hex)
3. In UAVcast web interface:
   - Navigate to **VPN** tab
   - Select **ZeroTier**
   - Enter your Network ID
   - Click **Connect**
4. Authorize the device in your ZeroTier network admin panel
5. Install ZeroTier on your ground station and join the same network
6. Use the assigned ZeroTier IP for telemetry destinations

**Example:**
- Network ID: `a09acf0233b1c5d7`
- Drone IP: `172.22.x.x`
- Ground Station IP: `172.22.y.y`

### Tailscale

1. Create account at [tailscale.com](https://tailscale.com)
2. Generate an auth key:
   - Go to Settings → Keys
   - Generate auth key (reusable recommended)
3. In UAVcast web interface:
   - Navigate to **VPN** tab
   - Select **Tailscale**
   - Paste your auth key
   - Click **Connect**
4. Install Tailscale on ground station
5. Both devices will appear in your Tailscale admin panel
6. Use Tailscale IPs for telemetry destinations

**Example:**
- Drone IP: `100.x.y.z`
- Ground Station IP: `100.a.b.c`

### WireGuard

1. Set up a WireGuard server (VPS, home server, or cloud instance)
2. Generate client configuration for the Raspberry Pi
3. In UAVcast web interface:
   - Navigate to **VPN** tab
   - Select **WireGuard**
   - Paste the complete client config
   - Click **Connect**
4. Configure your ground station as another WireGuard peer
5. Use WireGuard tunnel IPs for telemetry

**Example config format:**
```
[Interface]
PrivateKey = your_private_key
Address = 10.0.0.2/24

[Peer]
PublicKey = server_public_key
Endpoint = your-server.com:51820
AllowedIPs = 10.0.0.0/24
PersistentKeepalive = 25
```

## Configuration

### Flight Controller Setup

1. **Connect Hardware**:
   - USB: Connect flight controller to Raspberry Pi USB port
   - GPIO: Connect to UART pins (TX/RX)

2. **Configure in Web Interface** (Telemetry tab):
   - **Serial Port**: `/dev/ttyACM0` (USB) or `/dev/ttyAMA0` (GPIO)
   - **Baud Rate**: Match flight controller settings (common: 57600, 115200, 921600)
   - Click **Start** to begin MAVLink routing

3. **Add Telemetry Destinations**:
   - Click **Add** in Telemetry Destinations section
   - **Name**: `QGroundControl`, `Mission Planner`, etc.
   - **Host**: IP address of ground station
   - **Port**: `14550` (QGC), `14551` (MP), or custom
   - **Protocol**: UDP (recommended) or TCP
   - Ground station will receive full bidirectional MAVLink

### Video Streaming Setup

1. **Detect Camera** (Video tab):
   - Click refresh icon to detect cameras
   - Select camera device

2. **Configure Stream**:
   - **Camera Type**: USB Camera or Raspberry Pi Camera
   - **Device**: `/dev/video0`, `/dev/video1`, etc.
   - **Resolution**: 1920x1080, 1280x720, or 640x480
   - **FPS**: 30 (recommended), 60 for high-speed
   - **Bitrate**: 2000 kbps (adjust based on bandwidth)
   - **Protocol**: HLS (for browser preview)

3. **Start Streaming**:
   - Click **Start Streaming**
   - Live preview appears in browser
   - VP8/WebM codec for universal browser compatibility

### Network Configuration

**Modem Management** (Network tab):
- Automatic detection of USB LTE modems
- Signal strength monitoring
- Connection status

**Connectivity Testing**:
- Ping test to verify internet connection
- Default target: `8.8.8.8` (Google DNS)

### Configuration Profiles

**Save Current Configuration** (System tab):
1. Configure all settings (telemetry, video, VPN)
2. Click **Save Current** in Configuration Profiles
3. Enter profile name and description
4. Click **Save Profile**

**Load Profile**:
1. Select saved profile from list
2. Click **Load** icon
3. Page refreshes with loaded configuration

**Use Cases**:
- **Field Operations**: Cellular modem + ZeroTier + 720p video
- **Testing**: Local WiFi + direct UDP + 1080p video
- **Long Range**: Tailscale + 480p video + low bitrate

## Features Explained

### Live Telemetry Display

Shows real-time flight data in organized cards:
- **Flight Data**: Altitude, groundspeed, airspeed, climb rate
- **Navigation**: Heading, throttle
- **Battery**: Voltage, current, remaining %
- **GPS**: Fix type, satellites, coordinates
- **Status**: Armed state, flight mode

Requires MAVLink heartbeat from flight controller.

### Flight Map

- Interactive Leaflet map with OpenStreetMap tiles
- Real-time drone position marker
- Flight path history (last 100 points)
- Auto-centering on drone position
- Requires GPS fix from flight controller

### Toast Notifications

- Success/error/warning messages for all operations
- Start/stop confirmations
- Error details for troubleshooting
- Auto-dismiss after 4 seconds

### Error Handling

- React Error Boundary catches component crashes
- Graceful error messages with stack traces
- Reload and retry options
- Detailed error logging

## Troubleshooting

### MAVLink Connection Issues

**No heartbeat received:**
- Check serial port permissions: `sudo usermod -a -G dialout $USER` (logout required)
- Verify baud rate matches flight controller
- Check cable connection
- Try different USB port

**Parameters not loading:**
- Ensure bidirectional routing is working
- Check destination IP is reachable (ping test)
- Verify firewall allows UDP/TCP on port 14550
- Ground station must be running and configured

### Video Streaming Issues

**Camera not detected:**
- Check USB connection
- Verify camera permissions: `ls -l /dev/video*`
- For Pi Camera: Enable camera in `raspi-config`
- Check if camera is in use: `sudo fuser /dev/video0`

**Stream not playing in browser:**
- Wait 2-4 seconds for WebM buffering
- Check GStreamer is installed: `gst-launch-1.0 --version`
- Check camera works: `gst-launch-1.0 v4l2src device=/dev/video0 ! autovideosink`
- Look for errors in backend logs

**Poor video quality:**
- Reduce resolution (1280x720 or 640x480)
- Lower bitrate (1000-1500 kbps)
- Reduce FPS to 15-20
- Check network bandwidth

### VPN Connection Issues

**ZeroTier:**
- Verify Network ID is correct
- Check device is authorized in ZeroTier admin
- Ensure ZeroTier service is running: `sudo systemctl status zerotier-one`
- Check routes: `sudo zerotier-cli listnetworks`

**Tailscale:**
- Verify auth key is valid and not expired
- Check Tailscale service: `sudo systemctl status tailscaled`
- View status: `sudo tailscale status`
- Check connectivity: `sudo tailscale ping <peer>`

**WireGuard:**
- Verify config format is correct
- Check server endpoint is reachable
- Verify firewall allows UDP on WireGuard port
- Check interface: `sudo wg show`

### Network Issues

**No internet connection:**
- Check modem is detected: `mmcli -L`
- Verify SIM card is inserted and activated
- Check signal strength
- Try manual connection: `nmcli connection up <connection>`

**High latency:**
- Check signal strength (move to better location)
- Test with ping: `ping -c 10 8.8.8.8`
- Consider switching cellular bands
- Check for network congestion

## API Documentation

### REST Endpoints

**Telemetry:**
- `POST /api/telemetry/start` - Start MAVLink routing
- `POST /api/telemetry/stop` - Stop MAVLink routing
- `GET /api/telemetry/status` - Get routing status
- `POST /api/telemetry/destinations` - Add destination
- `DELETE /api/telemetry/destinations/{name}` - Remove destination

**Video:**
- `GET /api/video/cameras` - Detect cameras
- `POST /api/video/start` - Start streaming
- `POST /api/video/stop` - Stop streaming
- `GET /api/video/status` - Get stream status

**VPN:**
- `POST /api/vpn/zerotier/connect` - Connect ZeroTier
- `POST /api/vpn/tailscale/connect` - Connect Tailscale
- `POST /api/vpn/wireguard/connect` - Connect WireGuard
- `POST /api/vpn/disconnect` - Disconnect VPN
- `GET /api/vpn/status` - Get VPN status

**Network:**
- `GET /api/network/interfaces` - List network interfaces
- `GET /api/network/modem` - Detect modem
- `GET /api/network/modem/signal` - Get signal strength
- `GET /api/network/test` - Test connectivity

**Profiles:**
- `GET /api/profiles` - List profiles
- `POST /api/profiles` - Create profile
- `POST /api/profiles/{id}/load` - Load profile
- `DELETE /api/profiles/{id}` - Delete profile

### WebSocket

Connect to `/ws` for real-time updates:
- System stats (CPU, memory, temperature)
- MAVLink status and telemetry
- Network status

## Architecture

```
┌─────────────────┐
│ Flight          │
│ Controller      │
└────────┬────────┘
         │ Serial/USB
         │
┌────────▼────────────────────────────────────┐
│ Raspberry Pi / UAVcast-Free                 │
│                                             │
│  ┌──────────────┐      ┌─────────────────┐ │
│  │ MAVLink      │◄────►│ Backend         │ │
│  │ Router       │      │ (FastAPI)       │ │
│  └──────────────┘      └────────┬────────┘ │
│                                 │          │
│  ┌──────────────┐      ┌────────▼────────┐ │
│  │ Video        │◄────►│ Frontend        │ │
│  │ Streamer     │      │ (React)         │ │
│  └──────────────┘      └─────────────────┘ │
│                                             │
│  ┌──────────────┐      ┌─────────────────┐ │
│  │ VPN Client   │      │ Network         │ │
│  │              │      │ Manager         │ │
│  └──────────────┘      └─────────────────┘ │
└────────┬────────────────────────────────────┘
         │ LTE/WiFi
         │
┌────────▼────────┐
│ Internet        │
│ (via VPN)       │
└────────┬────────┘
         │
┌────────▼────────┐
│ Ground Station  │
└─────────────────┘
```

## Development

### Backend Structure

```
backend/
├── app/
│   ├── api/           # API routes
│   ├── core/          # Config and events
│   ├── models/        # Database models
│   └── services/      # Business logic
├── config/            # Local config files
├── logs/              # Application logs
└── requirements.txt   # Python dependencies
```

### Frontend Structure

```
frontend/
├── src/
│   ├── api/          # API client
│   ├── components/   # React components
│   ├── hooks/        # Custom hooks
│   ├── types/        # TypeScript types
│   └── utils/        # Utilities
└── package.json      # Node dependencies
```

### Running Tests

```bash
# Backend tests (if implemented)
cd backend
pytest

# Frontend tests (if implemented)
cd frontend
npm test
```
