"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import settings
from app.core.events import startup_event, shutdown_event
from app.api.routes import config, telemetry, video, vpn, network, system, profiles
from app.api.websocket import websocket_handler, broadcast_system_stats, broadcast_mavlink_stats
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await startup_event(app)

    # Start background tasks for WebSocket broadcasting
    app.state.broadcast_tasks = [
        asyncio.create_task(broadcast_system_stats(app)),
        asyncio.create_task(broadcast_mavlink_stats(app)),
    ]

    yield

    # Shutdown
    # Cancel background tasks
    for task in app.state.broadcast_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    await shutdown_event(app)


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(config.router, prefix="/api")
app.include_router(telemetry.router, prefix="/api")
app.include_router(video.router, prefix="/api")
app.include_router(vpn.router, prefix="/api")
app.include_router(network.router, prefix="/api")
app.include_router(system.router, prefix="/api")
app.include_router(profiles.router, prefix="/api")


# WebSocket endpoints
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket_handler(websocket, app)


@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    """WebSocket endpoint for telemetry updates (alias for /ws)."""
    await websocket_handler(websocket, app)


# Serve HLS video files
hls_dir = settings.hls_dir
if hls_dir.exists():
    app.mount("/hls", StaticFiles(directory=str(hls_dir)), name="hls")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )
