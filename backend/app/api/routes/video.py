"""Video streaming API routes."""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.services.camera_detector import CameraDetector

router = APIRouter(prefix="/video", tags=["video"])


class VideoConfig(BaseModel):
    """MediaMTX video configuration."""
    camera_type: str  # usb or picamera
    device: str | None = None  # /dev/video0 for USB
    resolution: str = "1280x720"
    fps: int = 30
    bitrate: int = 2000  # kbps
    path_name: str = "uav-camera"

    # Protocol enablement
    rtsp_enabled: bool = True
    hls_enabled: bool = True
    webrtc_enabled: bool = True
    rtmp_enabled: bool = False

    # Authentication
    auth_enabled: bool = False
    username: str | None = None
    password: str | None = None

    # Recording
    record_enabled: bool = False
    record_path: str | None = None
    record_format: str = "mp4"

    # Advanced
    run_on_demand: bool = True
    source_on_demand_start_timeout: str = "10s"
    source_on_demand_close_after: str = "10s"


class CameraTest(BaseModel):
    device: str
    camera_type: str


@router.get("/cameras")
async def detect_cameras():
    """Detect available cameras."""
    cameras = await CameraDetector.detect_all()
    return {"cameras": cameras}


@router.post("/cameras/test")
async def test_camera(test_config: CameraTest):
    """Test camera accessibility."""
    result = await CameraDetector.test_camera(
        device=test_config.device, camera_type=test_config.camera_type
    )
    return result


@router.post("/start")
async def start_streaming(config: VideoConfig, request: Request):
    """Start MediaMTX video streaming."""
    mediamtx_manager = request.app.state.mediamtx_manager
    result = await mediamtx_manager.start(config.model_dump())
    return result


@router.post("/stop")
async def stop_streaming(request: Request):
    """Stop MediaMTX video streaming."""
    mediamtx_manager = request.app.state.mediamtx_manager
    result = await mediamtx_manager.stop()
    return result


@router.post("/restart")
async def restart_streaming(request: Request):
    """Restart MediaMTX video streaming."""
    mediamtx_manager = request.app.state.mediamtx_manager
    result = await mediamtx_manager.restart()
    return result


@router.get("/status")
async def get_streaming_status(request: Request):
    """Get MediaMTX streaming status."""
    mediamtx_manager = request.app.state.mediamtx_manager
    return mediamtx_manager.get_status()


@router.get("/api-status")
async def get_api_status(request: Request):
    """Get detailed status from MediaMTX API."""
    mediamtx_manager = request.app.state.mediamtx_manager
    api_status = await mediamtx_manager.get_api_status()
    return {"api_status": api_status}


@router.get("/logs")
async def get_stream_logs(request: Request):
    """Get MediaMTX log output."""
    mediamtx_manager = request.app.state.mediamtx_manager
    logs = await mediamtx_manager.get_logs()
    return {"logs": logs}
