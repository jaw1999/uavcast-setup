"""Camera detection service."""

import asyncio
import logging
import re
import subprocess
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class CameraDetector:
    """Detects available cameras (USB and Raspberry Pi Camera)."""

    @staticmethod
    async def detect_all() -> List[Dict]:
        """Detect all available cameras."""
        cameras = []

        # Detect USB cameras
        usb_cameras = await CameraDetector.detect_usb_cameras()
        cameras.extend(usb_cameras)

        # Detect Raspberry Pi Camera
        pi_camera = await CameraDetector.detect_pi_camera()
        if pi_camera:
            cameras.append(pi_camera)

        logger.info(f"Detected {len(cameras)} camera(s)")
        return cameras

    @staticmethod
    async def detect_usb_cameras() -> List[Dict]:
        """Detect USB cameras via V4L2."""
        cameras = []

        try:
            # Check if v4l2-ctl is available
            which_result = await CameraDetector._run_command(["which", "v4l2-ctl"])
            if which_result["returncode"] != 0:
                logger.warning("v4l2-ctl not found, skipping USB camera detection")
                return cameras

            # List devices
            result = await CameraDetector._run_command(["v4l2-ctl", "--list-devices"])

            if result["returncode"] != 0:
                logger.warning("Failed to list V4L2 devices")
                return cameras

            # Parse output
            lines = result["stdout"].split("\n")
            current_camera = None

            for line in lines:
                if line and not line.startswith("\t") and not line.startswith(" "):
                    # Camera name line
                    current_camera = line.strip().rstrip(":")
                elif line.strip().startswith("/dev/video"):
                    # Device path line
                    device = line.strip()

                    # Skip internal Raspberry Pi devices (not actual USB cameras)
                    if current_camera and any(x in current_camera.lower() for x in [
                        "pispbe", "rp1-cfe", "rpi-hevc", "bcm2835", "unicam"
                    ]):
                        logger.debug(f"Skipping internal Pi device: {current_camera} at {device}")
                        continue

                    # Only include devices that support video capture
                    caps = await CameraDetector._get_device_capabilities(device)
                    if "video capture" in caps.lower():
                        # Get supported formats
                        formats = await CameraDetector._get_camera_formats(device)

                        cameras.append(
                            {
                                "name": current_camera or "Unknown USB Camera",
                                "device": device,
                                "type": "usb",
                                "formats": formats,
                            }
                        )
                        logger.info(f"Found USB camera: {current_camera} at {device}")

        except Exception as e:
            logger.error(f"Error detecting USB cameras: {e}")

        return cameras

    @staticmethod
    async def detect_pi_camera() -> Optional[Dict]:
        """Detect Raspberry Pi Camera via libcamera/rpicam."""
        try:
            # Check for rpicam-hello (Pi 5) or libcamera-hello (older Pi models)
            camera_cmd = None
            for cmd in ["rpicam-hello", "libcamera-hello"]:
                which_result = await CameraDetector._run_command(["which", cmd])
                if which_result["returncode"] == 0:
                    camera_cmd = cmd
                    break

            if not camera_cmd:
                logger.debug("rpicam-hello/libcamera-hello not found, skipping Pi Camera detection")
                return None

            # List cameras
            result = await CameraDetector._run_command(
                [camera_cmd, "--list-cameras"], timeout=5
            )

            if result["returncode"] == 0 and "Available cameras" in result["stdout"]:
                # Parse camera info
                camera_info = result["stdout"]

                # Extract camera name if available
                name_match = re.search(r"\d+\s*:\s*(.+?)\s*\[", camera_info)
                camera_name = (
                    name_match.group(1) if name_match else "Raspberry Pi Camera"
                )

                # Common Pi Camera formats
                formats = [
                    "1920x1080",
                    "1640x1232",
                    "1280x720",
                    "640x480",
                ]

                logger.info(f"Found Pi Camera: {camera_name}")
                return {
                    "name": camera_name,
                    "device": camera_cmd,  # Store which command to use
                    "type": "picamera",
                    "formats": formats,
                }

        except Exception as e:
            logger.error(f"Error detecting Pi Camera: {e}")

        return None

    @staticmethod
    async def _get_device_capabilities(device: str) -> str:
        """Get device capabilities."""
        try:
            result = await CameraDetector._run_command(
                ["v4l2-ctl", "-d", device, "--all"]
            )
            return result["stdout"]
        except Exception as e:
            logger.error(f"Error getting device capabilities: {e}")
            return ""

    @staticmethod
    async def _get_camera_formats(device: str) -> List[str]:
        """Get supported resolutions for a camera."""
        formats = []

        try:
            result = await CameraDetector._run_command(
                ["v4l2-ctl", "-d", device, "--list-formats-ext"]
            )

            if result["returncode"] == 0:
                # Parse resolutions from output
                for line in result["stdout"].split("\n"):
                    match = re.search(r"Size: Discrete (\d+)x(\d+)", line)
                    if match:
                        width = match.group(1)
                        height = match.group(2)
                        formats.append(f"{width}x{height}")

                # Remove duplicates and sort by resolution (largest first)
                formats = sorted(
                    list(set(formats)),
                    key=lambda x: int(x.split("x")[0]),
                    reverse=True,
                )

        except Exception as e:
            logger.error(f"Error getting camera formats: {e}")

        # Return common formats if none found
        if not formats:
            formats = ["1920x1080", "1280x720", "640x480"]

        return formats

    @staticmethod
    async def test_camera(device: str, camera_type: str) -> Dict:
        """Test if camera is accessible."""
        try:
            if camera_type == "usb":
                # Test V4L2 device
                result = await CameraDetector._run_command(
                    ["v4l2-ctl", "-d", device, "--all"], timeout=5
                )
                success = result["returncode"] == 0

            elif camera_type == "picamera":
                # Test rpicam/libcamera
                camera_cmd = None
                for cmd in ["rpicam-hello", "libcamera-hello"]:
                    which_result = await CameraDetector._run_command(["which", cmd])
                    if which_result["returncode"] == 0:
                        camera_cmd = cmd
                        break

                if not camera_cmd:
                    return {"status": "error", "message": "rpicam-hello/libcamera-hello not found"}

                result = await CameraDetector._run_command(
                    [camera_cmd, "--list-cameras"], timeout=5
                )
                success = result["returncode"] == 0

            else:
                return {"status": "error", "message": "Unknown camera type"}

            if success:
                return {"status": "success", "message": "Camera is accessible"}
            else:
                return {
                    "status": "error",
                    "message": f"Camera test failed: {result['stderr']}",
                }

        except Exception as e:
            logger.error(f"Camera test failed: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    async def _run_command(cmd: list, timeout: int = 10) -> Dict:
        """Run shell command asynchronously."""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            return {
                "returncode": process.returncode,
                "stdout": stdout.decode().strip() if stdout else "",
                "stderr": stderr.decode().strip() if stderr else "",
            }

        except asyncio.TimeoutError:
            logger.error(f"Command timed out: {cmd}")
            return {"returncode": -1, "stdout": "", "stderr": "Command timed out"}
        except Exception as e:
            logger.error(f"Command failed: {cmd} - {e}")
            return {"returncode": -1, "stdout": "", "stderr": str(e)}
