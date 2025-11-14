"""MediaMTX streaming server manager."""

import asyncio
import logging
import subprocess
import yaml
from typing import Dict, Optional
from enum import Enum
from pathlib import Path
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class CameraType(str, Enum):
    """Camera types."""

    USB = "usb"
    PI_CAMERA = "picamera"


class MediaMTXManager:
    """Manages MediaMTX streaming server."""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.running = False
        self.config: Dict = {}

        # Paths
        self.config_dir = Path("/opt/uavcast/config")
        self.config_file = self.config_dir / "mediamtx.yml"
        self.default_config_file = self.config_dir / "mediamtx.default.yml"
        self.binary_path = Path("/usr/local/bin/mediamtx")

        # MediaMTX API
        self.api_address = "127.0.0.1:9997"
        self.api_base_url = f"http://{self.api_address}/v3"

        # Server ports
        self.rtsp_port = 8554
        self.hls_port = 8888
        self.webrtc_port = 8889
        self.rtmp_port = 1935

        # Watchdog
        self.watchdog_task: Optional[asyncio.Task] = None

    async def start(self, config: Dict) -> Dict:
        """Start MediaMTX server with given configuration."""
        try:
            if self.running:
                return {"status": "error", "message": "MediaMTX already running"}

            if not self.binary_path.exists():
                return {
                    "status": "error",
                    "message": f"MediaMTX binary not found at {self.binary_path}. Please run deployment script to install it.",
                }

            # Store config
            self.config = config

            # Determine path name based on camera type (must match _generate_config logic)
            camera_type = CameraType(config.get("camera_type", "usb"))
            if camera_type == CameraType.PI_CAMERA:
                path_name = "cam"
            else:
                path_name = config.get("path_name", "uav-camera")

            # Generate MediaMTX config file
            await self._generate_config()

            # Start MediaMTX process
            logger.info(f"Starting MediaMTX with config: {self.config_file}")

            # Log the actual generated config for debugging
            try:
                with open(self.config_file, "r") as f:
                    config_content = f.read()
                    logger.info(f"MediaMTX config content:\n{config_content}")
            except Exception as e:
                logger.warning(f"Could not read config file for logging: {e}")

            try:
                # Use stdout=None to let MediaMTX output go directly to our logs
                self.process = subprocess.Popen(
                    [str(self.binary_path), str(self.config_file)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # Merge stderr into stdout
                    universal_newlines=True,
                    bufsize=1,  # Line buffered
                )
            except FileNotFoundError:
                return {
                    "status": "error",
                    "message": f"MediaMTX binary not found at {self.binary_path}",
                }

            # Wait for startup and capture initial output
            await asyncio.sleep(2)

            # Check if process started successfully
            poll_result = self.process.poll()
            if poll_result is not None:
                error_msg = f"MediaMTX failed to start (exit code {poll_result})"
                if self.process.stdout:
                    output = self.process.stdout.read()
                    logger.error(f"MediaMTX OUTPUT: {output}")
                    error_msg = f"{error_msg}: {output[:500]}"

                self.process = None
                return {"status": "error", "message": error_msg}

            # Skip reading initial output to avoid blocking
            # MediaMTX logs will be available via the logs endpoint
            logger.debug("MediaMTX process started, skipping initial output read")

            # Don't wait for API during start to avoid blocking the response
            # The watchdog will verify API availability in the background
            logger.debug("MediaMTX process started, API check will happen in background")

            self.running = True
            logger.info(f"MediaMTX started successfully (PID: {self.process.pid})")

            # Start watchdog
            self.watchdog_task = asyncio.create_task(self._watchdog())

            # Get stream URLs (pass the actual path_name used)
            stream_urls = self._get_stream_urls(path_name)

            return {
                "status": "success",
                "running": True,
                "pid": self.process.pid,
                "camera_type": config.get("camera_type"),
                "path_name": path_name,  # Return the actual path name used
                "urls": stream_urls,
            }

        except Exception as e:
            logger.error(f"Failed to start MediaMTX: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def stop(self) -> Dict:
        """Stop MediaMTX server."""
        try:
            if not self.running or not self.process:
                return {"status": "error", "message": "MediaMTX not running"}

            logger.info("Stopping MediaMTX...")

            # Cancel watchdog
            if self.watchdog_task:
                self.watchdog_task.cancel()
                try:
                    await self.watchdog_task
                except asyncio.CancelledError:
                    pass
                self.watchdog_task = None

            # Terminate process gracefully
            self.process.terminate()

            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("MediaMTX didn't stop gracefully, killing...")
                self.process.kill()
                self.process.wait()

            self.process = None
            self.running = False

            logger.info("MediaMTX stopped")
            return {"status": "success", "running": False}

        except Exception as e:
            logger.error(f"Failed to stop MediaMTX: {e}")
            return {"status": "error", "message": str(e)}

    async def restart(self) -> Dict:
        """Restart MediaMTX server."""
        logger.info("Restarting MediaMTX...")
        await self.stop()
        await asyncio.sleep(1)
        return await self.start(self.config)

    async def _generate_config(self) -> None:
        """Generate MediaMTX configuration file using default config as base."""
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load default MediaMTX config if available
        mediamtx_config = {}
        if self.default_config_file.exists():
            logger.info(f"Loading default MediaMTX config from {self.default_config_file}")
            with open(self.default_config_file, "r") as f:
                mediamtx_config = yaml.safe_load(f) or {}
        else:
            logger.warning(f"Default config not found at {self.default_config_file}, creating minimal config")

        # Extract config values
        camera_type = CameraType(self.config.get("camera_type", "usb"))
        device = self.config.get("device", "/dev/video0")
        resolution = self.config.get("resolution", "1280x720")
        fps = self.config.get("fps", 30)
        bitrate = self.config.get("bitrate", 2000)

        # For Pi Camera, always use "cam" as path name per MediaMTX docs
        # For USB, use custom path name
        if camera_type == CameraType.PI_CAMERA:
            path_name = "cam"
        else:
            path_name = self.config.get("path_name", "uav-camera")

        # For Pi Camera, use minimal config modifications to preserve MediaMTX defaults
        if camera_type == CameraType.PI_CAMERA:
            # Only enable API for management
            mediamtx_config["api"] = True
            mediamtx_config["apiAddress"] = self.api_address

            # Disable authentication globally
            mediamtx_config["authMethod"] = "internal"

            # Initialize paths if not exists
            if "paths" not in mediamtx_config:
                mediamtx_config["paths"] = {}

            # Configure Pi Camera path with minimal settings as per MediaMTX documentation
            # Use "cam" as the path name for consistency with MediaMTX examples
            path_config = {
                "source": "rpiCamera",
            }

            # Only add camera parameters if they differ from defaults
            # This allows MediaMTX to use its built-in defaults for optimal Pi Camera support
            width, height = resolution.split("x")
            if width != "1920" or height != "1080":  # Only override if not default
                path_config["rpiCameraWidth"] = int(width)
                path_config["rpiCameraHeight"] = int(height)

            if fps != 30:  # Only override if not default
                path_config["rpiCameraFPS"] = fps

            if bitrate != 1000:  # Only override if not default (1000 kbps)
                bitrate_bps = bitrate * 1000  # Convert kbps to bps
                path_config["rpiCameraBitrate"] = bitrate_bps

            # Set the path - no authentication
            mediamtx_config["paths"][path_name] = path_config

            logger.info(f"Using default MediaMTX config with Pi Camera at path '/cam' (no authentication)")

        else:
            # For USB cameras, use custom configuration with all settings
            # Protocol settings
            rtsp_enabled = self.config.get("rtsp_enabled", True)
            hls_enabled = self.config.get("hls_enabled", True)
            webrtc_enabled = self.config.get("webrtc_enabled", True)
            rtmp_enabled = self.config.get("rtmp_enabled", False)

            # Authentication
            auth_enabled = self.config.get("auth_enabled", False)
            username = self.config.get("username")
            password = self.config.get("password")

            # Recording
            record_enabled = self.config.get("record_enabled", False)
            record_path = self.config.get("record_path", "/opt/uavcast/recordings")
            record_format = self.config.get("record_format", "mp4")

            # Advanced
            run_on_demand = self.config.get("run_on_demand", True)
            source_on_demand_start_timeout = self.config.get("source_on_demand_start_timeout", "10s")
            source_on_demand_close_after = self.config.get("source_on_demand_close_after", "10s")

            # Override API settings
            mediamtx_config["api"] = True
            mediamtx_config["apiAddress"] = self.api_address

            # Override protocol settings
            mediamtx_config["rtspDisable"] = not rtsp_enabled
            if "hlsDisable" in mediamtx_config or hls_enabled:
                mediamtx_config["hlsDisable"] = not hls_enabled
            if "webrtcDisable" in mediamtx_config or webrtc_enabled:
                mediamtx_config["webrtcDisable"] = not webrtc_enabled
            if "rtmpDisable" in mediamtx_config or rtmp_enabled:
                mediamtx_config["rtmpDisable"] = not rtmp_enabled

            # Build source command based on camera type
            width, height = resolution.split("x")
            bitrate_bps = bitrate * 1000  # Convert kbps to bps

            # Initialize paths if not exists
            if "paths" not in mediamtx_config:
                mediamtx_config["paths"] = {}

            # Configure camera path
            path_config = {
                "sourceOnDemand": run_on_demand,
                "sourceOnDemandStartTimeout": source_on_demand_start_timeout,
                "sourceOnDemandCloseAfter": source_on_demand_close_after,
            }

            # Use ffmpeg for USB cameras
            path_config["source"] = (
                f"ffmpeg -f v4l2 -input_format mjpeg -video_size {resolution} "
                f"-framerate {fps} -i {device} "
                f"-c:v libx264 -preset ultrafast -tune zerolatency "
                f"-b:v {bitrate}k -maxrate {bitrate}k -bufsize {bitrate * 2}k "
                f"-g {fps} -keyint_min {fps} "
                f"-f rtsp rtsp://localhost:$RTSP_PORT/{path_name}"
            )

            # Add authentication if enabled
            if auth_enabled and username and password:
                path_config["readUser"] = username
                path_config["readPass"] = password
                path_config["publishUser"] = username
                path_config["publishPass"] = password

            # Add recording if enabled
            if record_enabled:
                Path(record_path).mkdir(parents=True, exist_ok=True)
                path_config["record"] = True
                path_config["recordPath"] = f"{record_path}/%path/%Y-%m-%d_%H-%M-%S.{record_format}"
                path_config["recordFormat"] = record_format

            # Set the path
            mediamtx_config["paths"][path_name] = path_config

        # Write config file
        logger.info(f"Writing MediaMTX config to {self.config_file}")
        with open(self.config_file, "w") as f:
            yaml.dump(mediamtx_config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"MediaMTX config generated for path '{path_name}' with camera type '{camera_type}'")

    async def _wait_for_api(self, timeout: int = 10) -> bool:
        """Wait for MediaMTX API to become available."""
        async with httpx.AsyncClient() as client:
            for _ in range(timeout):
                try:
                    response = await client.get(f"{self.api_base_url}/config/global/get")
                    if response.status_code == 200:
                        logger.info("MediaMTX API is ready")
                        return True
                except:
                    pass
                await asyncio.sleep(1)

        logger.warning("MediaMTX API did not become ready in time")
        return False

    async def _watchdog(self) -> None:
        """Monitor MediaMTX process and log if it dies."""
        logger.info("MediaMTX watchdog started")

        while self.running:
            try:
                await asyncio.sleep(5)

                # Check if process is still running
                if self.process and self.process.poll() is not None:
                    exit_code = self.process.poll()
                    logger.error(f"MediaMTX process died (exit code: {exit_code})")

                    if self.process.stderr:
                        stderr = self.process.stderr.read()
                        logger.error(f"MediaMTX STDERR: {stderr[:1000]}")

                    self.running = False
                    self.process = None
                    break

            except asyncio.CancelledError:
                logger.info("MediaMTX watchdog cancelled")
                break
            except Exception as e:
                logger.error(f"Error in MediaMTX watchdog: {e}")
                await asyncio.sleep(5)

        logger.info("MediaMTX watchdog stopped")

    def get_status(self) -> Dict:
        """Get MediaMTX server status."""
        is_running = self.running and self.process and self.process.poll() is None

        # Determine the actual path name used (cam for Pi Camera, otherwise from config)
        camera_type = CameraType(self.config.get("camera_type", "usb")) if is_running else None
        if is_running and camera_type == CameraType.PI_CAMERA:
            path_name = "cam"
        else:
            path_name = self.config.get("path_name", "uav-camera") if is_running else None

        status = {
            "running": is_running,
            "pid": self.process.pid if self.process else None,
            "camera_type": self.config.get("camera_type") if is_running else None,
            "path_name": path_name,
            "config": self.config if is_running else None,
        }

        if is_running:
            status["urls"] = self._get_stream_urls(path_name)

        return status

    async def get_api_status(self) -> Optional[Dict]:
        """Get status from MediaMTX API."""
        if not self.running:
            return None

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Get paths status
                response = await client.get(f"{self.api_base_url}/paths/list")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Failed to get MediaMTX API status: {e}")

        return None

    def _get_stream_urls(self, path_name: str) -> Dict[str, str]:
        """Generate stream URLs for all enabled protocols."""
        # Get server's IP (you might want to make this configurable)
        # For now, we'll use a placeholder that the frontend can replace
        host = "{{SERVER_IP}}"

        urls = {}

        if self.config.get("rtsp_enabled", True):
            urls["rtsp"] = f"rtsp://{host}:{self.rtsp_port}/{path_name}"

        if self.config.get("hls_enabled", True):
            urls["hls"] = f"http://{host}:{self.hls_port}/{path_name}"

        if self.config.get("webrtc_enabled", True):
            urls["webrtc"] = f"http://{host}:{self.webrtc_port}/{path_name}"

        if self.config.get("rtmp_enabled", False):
            urls["rtmp"] = f"rtmp://{host}:{self.rtmp_port}/{path_name}"

        return urls

    async def get_logs(self) -> Optional[str]:
        """Get MediaMTX stdout/stderr output."""
        if self.process and self.process.stdout:
            try:
                # Try to read available output without blocking
                import select
                if select.select([self.process.stdout], [], [], 0)[0]:
                    output = self.process.stdout.read(8192)
                    return output if output else "No output available"
                else:
                    return "No new output (buffer empty)"
            except Exception as e:
                return f"Error reading logs: {str(e)}"
        return "MediaMTX not running or no output buffer"
