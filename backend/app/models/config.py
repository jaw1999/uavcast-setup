"""Configuration database models."""

from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class FlightControllerConfig(Base):
    """Flight controller configuration."""

    __tablename__ = "flight_controller_config"

    id = Column(Integer, primary_key=True, index=True)
    serial_port = Column(String, default="/dev/ttyACM0")
    baud_rate = Column(Integer, default=57600)
    protocol = Column(String, default="mavlink2")
    enabled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TelemetryDestination(Base):
    """Telemetry destination configuration."""

    __tablename__ = "telemetry_destinations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    protocol = Column(String, default="udp")  # udp or tcp
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class VPNConfig(Base):
    """VPN configuration."""

    __tablename__ = "vpn_config"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=False)  # zerotier, tailscale, wireguard
    network_id = Column(String, nullable=True)  # For ZeroTier
    auth_key = Column(String, nullable=True)  # For Tailscale
    config_content = Column(String, nullable=True)  # For WireGuard
    enabled = Column(Boolean, default=False)
    status = Column(String, default="disconnected")
    assigned_ip = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class VideoConfig(Base):
    """Video streaming configuration."""

    __tablename__ = "video_config"

    id = Column(Integer, primary_key=True, index=True)
    camera_type = Column(String, nullable=False)  # usb or picamera
    device = Column(String, nullable=True)  # /dev/video0 or libcamera
    resolution = Column(String, default="1280x720")
    fps = Column(Integer, default=30)
    bitrate = Column(Integer, default=2000)
    destination = Column(String, nullable=True)  # host:port
    protocol = Column(String, default="udp")  # udp, tcp, or hls
    enabled = Column(Boolean, default=False)
    custom_pipeline = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class NetworkConfig(Base):
    """Network configuration."""

    __tablename__ = "network_config"

    id = Column(Integer, primary_key=True, index=True)
    interface_type = Column(String, nullable=False)  # wifi, ethernet, cellular
    priority = Column(Integer, default=0)  # Lower number = higher priority
    auto_connect = Column(Boolean, default=True)
    failover_enabled = Column(Boolean, default=True)
    settings = Column(JSON, nullable=True)  # Interface-specific settings
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SystemSettings(Base):
    """System-wide settings."""

    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ConfigProfile(Base):
    """Configuration profile for saving/loading settings."""

    __tablename__ = "config_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    config_data = Column(JSON, nullable=False)  # Stores all configuration as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
