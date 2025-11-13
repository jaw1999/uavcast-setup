"""Video streaming API routes."""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.services.camera_detector import CameraDetector

router = APIRouter(prefix="/video", tags=["video"])


class VideoConfig(BaseModel):
    camera_type: str
    device: str | None = None
    resolution: str = "1280x720"
    fps: int = 30
    bitrate: int = 2000
    destination: str | None = None
    protocol: str = "udp"
    custom_pipeline: str | None = None


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
    """Start video streaming."""
    video_streamer = request.app.state.video_streamer
    result = await video_streamer.start(config.model_dump())
    return result


@router.post("/stop")
async def stop_streaming(request: Request):
    """Stop video streaming."""
    video_streamer = request.app.state.video_streamer
    result = await video_streamer.stop()
    return result


@router.get("/status")
async def get_streaming_status(request: Request):
    """Get streaming status."""
    video_streamer = request.app.state.video_streamer
    return video_streamer.get_status()


@router.get("/errors")
async def get_stream_errors(request: Request):
    """Get GStreamer error output."""
    video_streamer = request.app.state.video_streamer
    errors = await video_streamer.get_stream_errors()
    return {"errors": errors}
