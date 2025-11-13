"""Video streaming service using GStreamer."""

import asyncio
import logging
import subprocess
from typing import Dict, Optional
from enum import Enum
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class CameraType(str, Enum):
    """Camera types."""

    USB = "usb"
    PI_CAMERA = "picamera"


class StreamProtocol(str, Enum):
    """Streaming protocols."""

    UDP = "udp"
    TCP = "tcp"
    HLS = "hls"


class VideoStreamer:
    """Manages video streaming via GStreamer."""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.camera_type: Optional[CameraType] = None
        self.protocol: Optional[StreamProtocol] = None
        self.running = False
        self.config: Dict = {}
        self.hls_dir = settings.hls_dir
        self.watchdog_task: Optional[asyncio.Task] = None
        self.auto_retry = True
        self.max_retries = 5
        self.retry_delay = 5  # seconds
        self.retry_count = 0

    def _parse_destination(self, destination: Optional[str] = None) -> tuple[str, str]:
        """Parse destination string into host and port."""
        dest = destination or self.config.get("destination", "127.0.0.1:5600")
        if ":" in dest:
            parts = dest.split(":", 1)
            return parts[0], parts[1]
        else:
            # If no port specified, assume it's just a host and use default port 5600
            logger.info(f"No port specified in destination '{dest}', using default port 5600")
            return dest, "5600"

    async def start(self, config: Dict) -> Dict:
        """Start video streaming."""
        try:
            if self.running:
                return {"status": "error", "message": "Already streaming"}

            # Clean up old HLS segments
            if self.hls_dir.exists():
                import shutil
                shutil.rmtree(self.hls_dir, ignore_errors=True)
            self.hls_dir.mkdir(parents=True, exist_ok=True)

            # Validate configuration
            camera_type = config.get("camera_type")
            if not camera_type:
                return {"status": "error", "message": "Camera type not specified"}

            self.camera_type = CameraType(camera_type)
            self.protocol = StreamProtocol(config.get("protocol", "udp"))
            self.config = config

            # Build GStreamer pipeline
            pipeline = await self._build_pipeline()
            if not pipeline:
                return {"status": "error", "message": "Failed to build pipeline"}

            # Start GStreamer process
            logger.info(f"Starting video stream: {pipeline if len(pipeline) <= 3 else pipeline[2]}")
            try:
                # For shell commands (like rpicam-vid pipeline), we need shell=True
                if pipeline[0] == "sh" and pipeline[1] == "-c":
                    # Execute the shell command directly
                    # IMPORTANT: Don't capture stdout/stderr for shell pipelines
                    # as it breaks the pipe between commands
                    self.process = subprocess.Popen(
                        pipeline[2],
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                else:
                    self.process = subprocess.Popen(
                        pipeline,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
                    )
            except FileNotFoundError:
                return {
                    "status": "error",
                    "message": "GStreamer not found. Please install: sudo apt-get install gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad",
                }

            # Check if process started successfully
            await asyncio.sleep(2)
            poll_result = self.process.poll()
            if poll_result is not None:
                error_msg = f"Process failed to start (exit code {poll_result})"
                if self.process.stderr:
                    stderr = self.process.stderr.read()
                    stdout = self.process.stdout.read() if self.process.stdout else ""
                    logger.error(f"GStreamer failed to start. Exit code: {poll_result}")
                    logger.error(f"STDERR: {stderr}")
                    logger.error(f"STDOUT: {stdout}")
                    error_msg = f"GStreamer failed to start (exit code {poll_result}): {stderr[:500]}"
                else:
                    logger.error(f"Video pipeline failed to start. Exit code: {poll_result}")

                self.process = None
                return {
                    "status": "error",
                    "message": error_msg,
                }

            self.running = True
            self.retry_count = 0  # Reset retry count on successful start
            logger.info(f"Video streaming started successfully (PID: {self.process.pid})")

            # Start watchdog task to monitor process health
            if self.auto_retry:
                self.watchdog_task = asyncio.create_task(self._watchdog())

            return {
                "status": "streaming",
                "camera_type": self.camera_type.value,
                "protocol": self.protocol.value,
                "pipeline": " ".join(pipeline),
            }

        except Exception as e:
            logger.error(f"Failed to start video streaming: {e}")
            return {"status": "error", "message": str(e)}

    async def stop(self) -> Dict:
        """Stop video streaming."""
        try:
            if not self.running or not self.process:
                return {"status": "error", "message": "Not streaming"}

            logger.info("Stopping video stream...")

            # Cancel watchdog task
            if self.watchdog_task:
                self.watchdog_task.cancel()
                try:
                    await self.watchdog_task
                except asyncio.CancelledError:
                    pass
                self.watchdog_task = None

            # Terminate process
            self.process.terminate()

            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("GStreamer didn't stop gracefully, killing...")
                self.process.kill()
                self.process.wait()

            self.process = None
            self.running = False
            self.retry_count = 0

            logger.info("Video streaming stopped")
            return {"status": "stopped"}

        except Exception as e:
            logger.error(f"Failed to stop video streaming: {e}")
            return {"status": "error", "message": str(e)}

    async def _watchdog(self) -> None:
        """Monitor GStreamer process and auto-restart on failure."""
        logger.info("Video streaming watchdog started")

        while self.running:
            try:
                await asyncio.sleep(2)  # Check every 2 seconds

                # Check if process is still running
                if self.process and self.process.poll() is not None:
                    exit_code = self.process.poll()
                    logger.error(f"Video streaming process died (exit code: {exit_code})")
                    if self.process.stderr:
                        stderr = self.process.stderr.read()
                        logger.error(f"STDERR: {stderr[:500]}")

                    # Attempt restart if within retry limit
                    if self.retry_count < self.max_retries:
                        self.retry_count += 1
                        logger.warning(f"Attempting restart {self.retry_count}/{self.max_retries} in {self.retry_delay}s...")
                        await asyncio.sleep(self.retry_delay)

                        # Attempt restart
                        await self._restart()
                    else:
                        logger.error(f"Max retries ({self.max_retries}) exceeded, giving up")
                        self.running = False
                        self.process = None
                        break

            except asyncio.CancelledError:
                logger.info("Video streaming watchdog cancelled")
                break
            except Exception as e:
                logger.error(f"Error in watchdog: {e}")
                await asyncio.sleep(5)

        logger.info("Video streaming watchdog stopped")

    async def _restart(self) -> None:
        """Attempt to restart video streaming."""
        try:
            logger.info("Restarting video stream...")

            # Clean up old process
            if self.process:
                try:
                    self.process.kill()
                    self.process.wait()
                except:
                    pass
                self.process = None

            # Clean up old HLS segments
            if self.hls_dir.exists():
                import shutil
                shutil.rmtree(self.hls_dir, ignore_errors=True)
            self.hls_dir.mkdir(parents=True, exist_ok=True)

            # Rebuild pipeline with existing config
            pipeline = await self._build_pipeline()
            if not pipeline:
                logger.error("Failed to rebuild pipeline during restart")
                return

            # Start new GStreamer process
            logger.info(f"Restarting with pipeline: {' '.join(pipeline)}")
            self.process = subprocess.Popen(
                pipeline,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            # Check if restart succeeded
            await asyncio.sleep(2)
            if self.process.poll() is None:
                logger.info(f"Video stream restarted successfully (PID: {self.process.pid})")
                self.retry_count = 0  # Reset on successful restart
            else:
                logger.error("Video stream failed to restart")

        except Exception as e:
            logger.error(f"Failed to restart video stream: {e}")

    async def _build_pipeline(self) -> Optional[list]:
        """Build GStreamer pipeline based on configuration."""
        try:
            if self.camera_type == CameraType.USB:
                return await self._build_usb_pipeline()
            elif self.camera_type == CameraType.PI_CAMERA:
                return await self._build_picamera_pipeline()
            else:
                logger.error(f"Unknown camera type: {self.camera_type}")
                return None

        except Exception as e:
            logger.error(f"Failed to build pipeline: {e}")
            return None

    async def _build_usb_pipeline(self) -> list:
        """Build GStreamer pipeline for USB camera."""
        device = self.config.get("device", "/dev/video0")
        resolution = self.config.get("resolution") or "1280x720"
        fps = self.config.get("fps") or 30
        bitrate = self.config.get("bitrate") or 2000

        logger.info(f"Building USB pipeline: device={device}, resolution={resolution}, fps={fps}, bitrate={bitrate}")

        width, height = resolution.split("x")

        # Base pipeline: source → decode (if needed) → convert → scale → encode
        # Optimized for low latency and maximum performance
        pipeline = [
            "gst-launch-1.0",
            "-v",
            "v4l2src",
            f"device={device}",
            "io-mode=2",  # Use mmap for better performance
            "!",
            "decodebin",  # Auto-decode any compressed format (MJPEG, H264, etc.)
            "!",
            "videoconvert",  # Convert to a format we can work with
            "n-threads=0",  # Auto-detect number of threads
            "!",
            "videoscale",  # Scale to target resolution
            "method=0",  # Nearest neighbor (fastest scaling)
            "!",
            f"video/x-raw,width={width},height={height},framerate={fps}/1",
            "!",
            "x264enc",
            f"bitrate={bitrate}",  # x264enc uses kbits/sec
            "tune=zerolatency",  # Optimize for low latency
            "speed-preset=ultrafast",  # Fast encoding
            "key-int-max=30",  # Keyframe every 1 second at 30fps
            "threads=0",  # Auto-detect number of threads
            "!",
            "h264parse",  # Parse H264 stream
            "!",
        ]

        # Add protocol-specific sink
        if self.protocol == StreamProtocol.UDP:
            host, port = self._parse_destination()
            pipeline.extend(
                [
                    "rtph264pay",
                    "config-interval=1",
                    "pt=96",
                    "!",
                    "udpsink",
                    f"host={host}",
                    f"port={port}",
                ]
            )

        elif self.protocol == StreamProtocol.TCP:
            host, port = self._parse_destination()
            pipeline.extend(
                [
                    "rtph264pay",
                    "config-interval=1",
                    "pt=96",
                    "!",
                    "tcpserversink",
                    f"host={host}",
                    f"port={port}",
                ]
            )

        elif self.protocol == StreamProtocol.HLS:
            # Create HLS directory
            self.hls_dir.mkdir(parents=True, exist_ok=True)
            # H264 goes into MP4 container for HLS
            mp4_file = self.hls_dir / "stream.mp4"
            pipeline.extend(
                [
                    "mp4mux",
                    "!",
                    "filesink",
                    f"location={mp4_file}",
                ]
            )

        return pipeline

    async def _build_picamera_pipeline(self) -> list:
        """Build GStreamer pipeline for Raspberry Pi Camera."""
        resolution = self.config.get("resolution") or "1280x720"
        fps = self.config.get("fps") or 30
        bitrate = self.config.get("bitrate") or 2000

        logger.info(f"Building Pi Camera pipeline: resolution={resolution}, fps={fps}, bitrate={bitrate}")

        width, height = resolution.split("x")

        # Determine which camera command to use
        camera_cmd = self.config.get("device")

        # If no device specified or it contains rpicam/libcamera command, assume Pi Camera with rpicam-vid
        # Default to rpicam-vid for Pi 5
        if not camera_cmd or (isinstance(camera_cmd, str) and ("rpicam" in camera_cmd or "libcamera" in camera_cmd)):
            logger.info("Using rpicam-vid pipeline for Pi 5")
            host, port = self._parse_destination()

            # Build as shell command with pipe
            # Note: --libav-format is required when piping to stdout via subprocess
            pipeline = [
                "sh",
                "-c",
                f"rpicam-vid --nopreview -t 0 --width {width} --height {height} --framerate {fps} --bitrate {bitrate * 1000} --codec h264 --inline --flush --libav-format h264 -o - | gst-launch-1.0 fdsrc ! h264parse ! rtph264pay config-interval=1 pt=96 ! udpsink host={host} port={port}"
            ]
            return pipeline

        # Fallback: Use libcamerasrc for older Pi models (if available)
        logger.info("Using libcamerasrc pipeline")
        pipeline = [
            "gst-launch-1.0",
            "-v",
            "libcamerasrc",
            "!",
            f"video/x-raw,width={width},height={height},framerate={fps}/1",
            "!",
            "videoconvert",
            "n-threads=0",  # Auto-detect number of threads
            "!",
            "x264enc",
            f"bitrate={bitrate}",
            "tune=zerolatency",
            "speed-preset=ultrafast",
            "key-int-max=30",
            "!",
            "h264parse",
            "!",
        ]

        # Add protocol-specific sink
        if self.protocol == StreamProtocol.UDP:
            host, port = self._parse_destination()
            pipeline.extend(
                [
                    "rtph264pay",
                    "config-interval=1",
                    "pt=96",
                    "!",
                    "udpsink",
                    f"host={host}",
                    f"port={port}",
                ]
            )

        elif self.protocol == StreamProtocol.TCP:
            host, port = self._parse_destination()
            pipeline.extend(
                [
                    "rtph264pay",
                    "config-interval=1",
                    "pt=96",
                    "!",
                    "tcpserversink",
                    f"host={host}",
                    f"port={port}",
                ]
            )

        elif self.protocol == StreamProtocol.HLS:
            # Create HLS directory
            self.hls_dir.mkdir(parents=True, exist_ok=True)
            # H264 goes into MP4 container for HLS
            mp4_file = self.hls_dir / "stream.mp4"
            pipeline.extend(
                [
                    "mp4mux",
                    "!",
                    "filesink",
                    f"location={mp4_file}",
                ]
            )

        return pipeline

    def get_status(self) -> Dict:
        """Get streaming status."""
        # Check if process is actually still running
        if self.running and self.process:
            if self.process.poll() is not None:
                logger.warning("GStreamer process died unexpectedly")
                # Don't set running to False here - let watchdog handle it
                # self.running = False
                # self.process = None

        return {
            "running": self.running,
            "camera_type": self.camera_type.value if self.camera_type else None,
            "protocol": self.protocol.value if self.protocol else None,
            "config": self.config if self.running else None,
            "pid": self.process.pid if self.process else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "auto_retry": self.auto_retry,
        }

    async def get_stream_errors(self) -> Optional[str]:
        """Get GStreamer error output."""
        if self.process and self.process.stderr:
            return self.process.stderr.read()
        return None
