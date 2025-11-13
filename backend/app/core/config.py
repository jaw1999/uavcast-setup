"""Application configuration."""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""

    # App info
    app_name: str = "UAVcast-Free"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./uavcast.db"

    # Paths (use local dirs in development, system dirs in production)
    config_dir: Path = Path("./config")
    log_dir: Path = Path("./logs")
    hls_dir: Path = Path("./tmp/hls")

    # CORS
    cors_origins: list = ["*"]

    # MAVLink defaults
    default_serial_port: str = "/dev/ttyACM0"
    default_baud_rate: int = 57600
    default_telemetry_port: int = 14550

    # Video defaults
    default_video_port: int = 5600
    default_video_resolution: str = "1280x720"
    default_video_fps: int = 30
    default_video_bitrate: int = 2000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Create directories if they don't exist
settings.config_dir.mkdir(parents=True, exist_ok=True)
settings.log_dir.mkdir(parents=True, exist_ok=True)
settings.hls_dir.mkdir(parents=True, exist_ok=True)
