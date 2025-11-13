"""Configuration profiles API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.models.config import (
    ConfigProfile,
    FlightControllerConfig,
    VideoConfig,
    VPNConfig,
)

router = APIRouter(prefix="/config/profiles", tags=["profiles"])


class ProfileCreate(BaseModel):
    name: str
    description: str | None = None


class ProfileResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: str
    updated_at: str | None

    class Config:
        from_attributes = True


@router.get("")
async def list_profiles(db: AsyncSession = Depends(get_db)):
    """List all configuration profiles."""
    result = await db.execute(select(ConfigProfile))
    profiles = result.scalars().all()
    return {"profiles": profiles}


@router.post("")
async def create_profile(profile: ProfileCreate, db: AsyncSession = Depends(get_db)):
    """Save current configuration as a profile."""
    # Gather current configuration
    fc_result = await db.execute(select(FlightControllerConfig))
    fc_config = fc_result.scalar_one_or_none()

    video_result = await db.execute(select(VideoConfig))
    video_config = video_result.scalar_one_or_none()

    vpn_result = await db.execute(select(VPNConfig))
    vpn_config = vpn_result.scalar_one_or_none()

    # Build config data
    config_data = {
        "flight_controller": {
            "serial_port": fc_config.serial_port if fc_config else None,
            "baud_rate": fc_config.baud_rate if fc_config else None,
            "protocol": fc_config.protocol if fc_config else None,
        } if fc_config else None,
        "video": {
            "camera_type": video_config.camera_type if video_config else None,
            "device": video_config.device if video_config else None,
            "resolution": video_config.resolution if video_config else None,
            "fps": video_config.fps if video_config else None,
            "bitrate": video_config.bitrate if video_config else None,
            "destination": video_config.destination if video_config else None,
            "protocol": video_config.protocol if video_config else None,
        } if video_config else None,
        "vpn": {
            "provider": vpn_config.provider if vpn_config else None,
            "network_id": vpn_config.network_id if vpn_config else None,
        } if vpn_config else None,
    }

    # Create profile
    db_profile = ConfigProfile(
        name=profile.name,
        description=profile.description,
        config_data=config_data,
    )

    db.add(db_profile)
    await db.commit()
    await db.refresh(db_profile)

    return db_profile


@router.post("/{profile_id}/load")
async def load_profile(profile_id: int, db: AsyncSession = Depends(get_db)):
    """Load a configuration profile."""
    # Get profile
    result = await db.execute(select(ConfigProfile).where(ConfigProfile.id == profile_id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    config_data = profile.config_data

    # Apply flight controller config
    if config_data.get("flight_controller"):
        fc_result = await db.execute(select(FlightControllerConfig))
        fc_config = fc_result.scalar_one_or_none()

        fc_data = config_data["flight_controller"]
        if fc_config:
            fc_config.serial_port = fc_data.get("serial_port")
            fc_config.baud_rate = fc_data.get("baud_rate")
            fc_config.protocol = fc_data.get("protocol")
        else:
            fc_config = FlightControllerConfig(**fc_data)
            db.add(fc_config)

    # Apply video config
    if config_data.get("video"):
        video_result = await db.execute(select(VideoConfig))
        video_config = video_result.scalar_one_or_none()

        video_data = config_data["video"]
        if video_config:
            for key, value in video_data.items():
                if value is not None:
                    setattr(video_config, key, value)
        else:
            video_config = VideoConfig(**video_data)
            db.add(video_config)

    # Apply VPN config
    if config_data.get("vpn"):
        vpn_result = await db.execute(select(VPNConfig))
        vpn_config = vpn_result.scalar_one_or_none()

        vpn_data = config_data["vpn"]
        if vpn_config:
            vpn_config.provider = vpn_data.get("provider")
            vpn_config.network_id = vpn_data.get("network_id")
        else:
            vpn_config = VPNConfig(**vpn_data)
            db.add(vpn_config)

    await db.commit()

    return {"status": "loaded", "profile": profile.name}


@router.delete("/{profile_id}")
async def delete_profile(profile_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a configuration profile."""
    result = await db.execute(select(ConfigProfile).where(ConfigProfile.id == profile_id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    await db.delete(profile)
    await db.commit()

    return {"status": "deleted"}
