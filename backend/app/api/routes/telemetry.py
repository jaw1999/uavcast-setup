"""Telemetry/MAVLink API routes."""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/telemetry", tags=["mavlink", "telemetry"])


class MAVLinkConfig(BaseModel):
    serial_port: str
    baud_rate: int


class TelemetryDest(BaseModel):
    name: str
    host: str
    port: int
    protocol: str = "udp"


@router.post("/start")
async def start_mavlink(config: MAVLinkConfig, request: Request):
    """Start MAVLink routing."""
    mavlink_router = request.app.state.mavlink_router

    # Configure router
    await mavlink_router.configure(config.model_dump())

    # Start routing
    result = await mavlink_router.start()
    return result


@router.post("/stop")
async def stop_mavlink(request: Request):
    """Stop MAVLink routing."""
    mavlink_router = request.app.state.mavlink_router
    result = await mavlink_router.stop()
    return result


@router.get("/status")
async def get_mavlink_status(request: Request):
    """Get MAVLink router status."""
    mavlink_router = request.app.state.mavlink_router
    return mavlink_router.get_status()


@router.post("/destinations")
async def add_destination(destination: TelemetryDest, request: Request):
    """Add telemetry destination."""
    mavlink_router = request.app.state.mavlink_router
    result = await mavlink_router.add_destination(
        name=destination.name,
        host=destination.host,
        port=destination.port,
        protocol=destination.protocol,
    )
    return result


@router.delete("/destinations/{name}")
async def remove_destination(name: str, request: Request):
    """Remove telemetry destination."""
    mavlink_router = request.app.state.mavlink_router
    result = await mavlink_router.remove_destination(name)
    return result
