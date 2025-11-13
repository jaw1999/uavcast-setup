"""Configuration API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel

from app.core.database import get_db
from app.models.config import (
    FlightControllerConfig,
    TelemetryDestination,
    VPNConfig,
    VideoConfig,
    NetworkConfig,
    SystemSettings,
)

router = APIRouter(prefix="/config", tags=["config"])


# ==================== Pydantic Models ====================


class FlightControllerConfigCreate(BaseModel):
    serial_port: str
    baud_rate: int
    protocol: str = "mavlink2"
    enabled: bool = False


class TelemetryDestinationCreate(BaseModel):
    name: str
    host: str
    port: int
    protocol: str = "udp"
    enabled: bool = True


class VPNConfigCreate(BaseModel):
    provider: str
    network_id: str | None = None
    auth_key: str | None = None
    config_content: str | None = None
    enabled: bool = False


class VideoConfigCreate(BaseModel):
    camera_type: str
    device: str | None = None
    resolution: str = "1280x720"
    fps: int = 30
    bitrate: int = 2000
    destination: str | None = None
    protocol: str = "udp"
    enabled: bool = False
    custom_pipeline: str | None = None


# ==================== Flight Controller ====================


@router.get("/flight-controller")
async def get_flight_controller_config(db: AsyncSession = Depends(get_db)):
    """Get flight controller configuration."""
    result = await db.execute(select(FlightControllerConfig))
    config = result.scalar_one_or_none()
    return config


@router.post("/flight-controller")
async def create_flight_controller_config(
    config: FlightControllerConfigCreate, db: AsyncSession = Depends(get_db)
):
    """Create or update flight controller configuration."""
    # Check if config exists
    result = await db.execute(select(FlightControllerConfig))
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing
        for key, value in config.model_dump().items():
            setattr(existing, key, value)
        db_config = existing
    else:
        # Create new
        db_config = FlightControllerConfig(**config.model_dump())
        db.add(db_config)

    await db.commit()
    await db.refresh(db_config)
    return db_config


# ==================== Telemetry Destinations ====================


@router.get("/telemetry-destinations")
async def get_telemetry_destinations(db: AsyncSession = Depends(get_db)):
    """Get all telemetry destinations."""
    result = await db.execute(select(TelemetryDestination))
    destinations = result.scalars().all()
    return destinations


@router.post("/telemetry-destinations")
async def create_telemetry_destination(
    destination: TelemetryDestinationCreate, db: AsyncSession = Depends(get_db)
):
    """Create telemetry destination."""
    db_destination = TelemetryDestination(**destination.model_dump())
    db.add(db_destination)
    await db.commit()
    await db.refresh(db_destination)
    return db_destination


@router.delete("/telemetry-destinations/{destination_id}")
async def delete_telemetry_destination(destination_id: int, db: AsyncSession = Depends(get_db)):
    """Delete telemetry destination."""
    result = await db.execute(
        select(TelemetryDestination).where(TelemetryDestination.id == destination_id)
    )
    destination = result.scalar_one_or_none()

    if not destination:
        raise HTTPException(status_code=404, detail="Destination not found")

    await db.delete(destination)
    await db.commit()
    return {"status": "deleted"}


# ==================== VPN ====================


@router.get("/vpn")
async def get_vpn_config(db: AsyncSession = Depends(get_db)):
    """Get VPN configuration."""
    result = await db.execute(select(VPNConfig))
    config = result.scalar_one_or_none()
    return config


@router.post("/vpn")
async def create_vpn_config(config: VPNConfigCreate, db: AsyncSession = Depends(get_db)):
    """Create or update VPN configuration."""
    result = await db.execute(select(VPNConfig))
    existing = result.scalar_one_or_none()

    if existing:
        for key, value in config.model_dump().items():
            setattr(existing, key, value)
        db_config = existing
    else:
        db_config = VPNConfig(**config.model_dump())
        db.add(db_config)

    await db.commit()
    await db.refresh(db_config)
    return db_config


# ==================== Video ====================


@router.get("/video")
async def get_video_config(db: AsyncSession = Depends(get_db)):
    """Get video configuration."""
    result = await db.execute(select(VideoConfig))
    config = result.scalar_one_or_none()
    return config


@router.post("/video")
async def create_video_config(config: VideoConfigCreate, db: AsyncSession = Depends(get_db)):
    """Create or update video configuration."""
    result = await db.execute(select(VideoConfig))
    existing = result.scalar_one_or_none()

    if existing:
        for key, value in config.model_dump().items():
            setattr(existing, key, value)
        db_config = existing
    else:
        db_config = VideoConfig(**config.model_dump())
        db.add(db_config)

    await db.commit()
    await db.refresh(db_config)
    return db_config
