"""Application lifecycle events."""

import logging
from fastapi import FastAPI
from app.core.database import init_db, close_db
from app.services.system_monitor import SystemMonitor
from app.services.mavlink_router import MAVLinkRouter
from app.services.mediamtx_manager import MediaMTXManager
from app.services.vpn_manager import VPNManager

logger = logging.getLogger(__name__)


async def startup_event(app: FastAPI) -> None:
    """Execute on application startup."""
    logger.info("Starting UAVcast-Free application...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize service managers (stored in app state)
    app.state.system_monitor = SystemMonitor()
    app.state.mavlink_router = MAVLinkRouter()
    app.state.mediamtx_manager = MediaMTXManager()
    app.state.vpn_manager = VPNManager()

    # Start system monitoring
    await app.state.system_monitor.start()
    logger.info("System monitor started")

    logger.info("UAVcast-Free application started successfully")


async def shutdown_event(app: FastAPI) -> None:
    """Execute on application shutdown."""
    logger.info("Shutting down UAVcast-Free application...")

    # Stop all services
    if hasattr(app.state, "mavlink_router"):
        await app.state.mavlink_router.stop()

    if hasattr(app.state, "mediamtx_manager"):
        await app.state.mediamtx_manager.stop()

    if hasattr(app.state, "vpn_manager"):
        await app.state.vpn_manager.disconnect()

    if hasattr(app.state, "system_monitor"):
        await app.state.system_monitor.stop()

    # Close database
    await close_db()
    logger.info("Database connection closed")

    logger.info("UAVcast-Free application shut down successfully")
