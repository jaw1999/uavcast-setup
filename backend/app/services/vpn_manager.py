"""VPN manager service supporting ZeroTier, Tailscale, and WireGuard."""

import asyncio
import logging
import subprocess
import json
import re
from typing import Dict, Optional
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class VPNProvider(str, Enum):
    """Supported VPN providers."""

    ZEROTIER = "zerotier"
    TAILSCALE = "tailscale"
    WIREGUARD = "wireguard"


class VPNManager:
    """Manages VPN connections."""

    def __init__(self):
        self.provider: Optional[VPNProvider] = None
        self.status = "disconnected"
        self.assigned_ip: Optional[str] = None
        self.network_id: Optional[str] = None  # ZeroTier
        self.auth_key: Optional[str] = None  # Tailscale
        self.config_path = Path("/etc/wireguard/wg0.conf")  # WireGuard

    # ==================== ZeroTier ====================

    async def configure_zerotier(self, network_id: str) -> Dict:
        """Configure and connect to ZeroTier network."""
        try:
            logger.info(f"Configuring ZeroTier with network {network_id}")

            # Ensure ZeroTier is installed
            if not await self._check_zerotier_installed():
                install_result = await self._install_zerotier()
                if install_result.get("status") != "success":
                    return install_result

            # Join network
            result = await self._run_command(
                ["sudo", "zerotier-cli", "join", network_id], timeout=30
            )

            if result["returncode"] != 0:
                return {
                    "status": "error",
                    "message": f"Failed to join network: {result['stderr']}",
                }

            # Wait for IP assignment (with timeout)
            max_attempts = 30
            for attempt in range(max_attempts):
                await asyncio.sleep(2)
                ip = await self._get_zerotier_ip(network_id)
                if ip:
                    self.provider = VPNProvider.ZEROTIER
                    self.status = "connected"
                    self.assigned_ip = ip
                    self.network_id = network_id
                    logger.info(f"ZeroTier connected: {ip}")
                    return {
                        "status": "connected",
                        "provider": "zerotier",
                        "network_id": network_id,
                        "ip_address": ip,
                    }

            return {
                "status": "error",
                "message": "Joined network but no IP assigned. Check network authorization.",
            }

        except Exception as e:
            logger.error(f"ZeroTier configuration failed: {e}")
            return {"status": "error", "message": str(e)}

    async def _check_zerotier_installed(self) -> bool:
        """Check if ZeroTier is installed."""
        result = await self._run_command(["which", "zerotier-cli"])
        return result["returncode"] == 0

    async def _install_zerotier(self) -> Dict:
        """Install ZeroTier."""
        try:
            logger.info("Installing ZeroTier...")
            result = await self._run_command(
                ["curl", "-s", "https://install.zerotier.com", "|", "sudo", "bash"],
                shell=True,
                timeout=120,
            )

            if result["returncode"] == 0:
                logger.info("ZeroTier installed successfully")
                return {"status": "success"}
            else:
                return {
                    "status": "error",
                    "message": f"Installation failed: {result['stderr']}",
                }

        except Exception as e:
            logger.error(f"ZeroTier installation failed: {e}")
            return {"status": "error", "message": str(e)}

    async def _get_zerotier_ip(self, network_id: str) -> Optional[str]:
        """Get ZeroTier assigned IP address."""
        try:
            result = await self._run_command(["sudo", "zerotier-cli", "listnetworks", "-j"])

            if result["returncode"] == 0:
                networks = json.loads(result["stdout"])
                for network in networks:
                    if network.get("id") == network_id:
                        addresses = network.get("assignedAddresses", [])
                        for addr in addresses:
                            # Return first IPv4 address
                            if "/" in addr and ":" not in addr.split("/")[0]:
                                return addr.split("/")[0]
            return None

        except Exception as e:
            logger.error(f"Failed to get ZeroTier IP: {e}")
            return None

    async def disconnect_zerotier(self) -> Dict:
        """Disconnect from ZeroTier network."""
        try:
            if not self.network_id:
                return {"status": "error", "message": "No network to disconnect from"}

            result = await self._run_command(
                ["sudo", "zerotier-cli", "leave", self.network_id]
            )

            if result["returncode"] == 0:
                self.status = "disconnected"
                self.assigned_ip = None
                logger.info("ZeroTier disconnected")
                return {"status": "disconnected"}
            else:
                return {"status": "error", "message": result["stderr"]}

        except Exception as e:
            logger.error(f"ZeroTier disconnect failed: {e}")
            return {"status": "error", "message": str(e)}

    # ==================== Tailscale ====================

    async def configure_tailscale(self, auth_key: str) -> Dict:
        """Configure and connect to Tailscale."""
        try:
            logger.info("Configuring Tailscale")

            # Ensure Tailscale is installed
            if not await self._check_tailscale_installed():
                install_result = await self._install_tailscale()
                if install_result.get("status") != "success":
                    return install_result

            # Authenticate and connect
            result = await self._run_command(
                ["sudo", "tailscale", "up", f"--authkey={auth_key}"], timeout=30
            )

            if result["returncode"] != 0:
                return {
                    "status": "error",
                    "message": f"Failed to connect: {result['stderr']}",
                }

            # Get assigned IP
            await asyncio.sleep(2)
            ip = await self._get_tailscale_ip()

            if ip:
                self.provider = VPNProvider.TAILSCALE
                self.status = "connected"
                self.assigned_ip = ip
                self.auth_key = auth_key
                logger.info(f"Tailscale connected: {ip}")
                return {"status": "connected", "provider": "tailscale", "ip_address": ip}
            else:
                return {"status": "error", "message": "Connected but no IP assigned"}

        except Exception as e:
            logger.error(f"Tailscale configuration failed: {e}")
            return {"status": "error", "message": str(e)}

    async def _check_tailscale_installed(self) -> bool:
        """Check if Tailscale is installed."""
        result = await self._run_command(["which", "tailscale"])
        return result["returncode"] == 0

    async def _install_tailscale(self) -> Dict:
        """Install Tailscale."""
        try:
            logger.info("Installing Tailscale...")
            result = await self._run_command(
                ["curl", "-fsSL", "https://tailscale.com/install.sh", "|", "sh"],
                shell=True,
                timeout=120,
            )

            if result["returncode"] == 0:
                logger.info("Tailscale installed successfully")
                return {"status": "success"}
            else:
                return {
                    "status": "error",
                    "message": f"Installation failed: {result['stderr']}",
                }

        except Exception as e:
            logger.error(f"Tailscale installation failed: {e}")
            return {"status": "error", "message": str(e)}

    async def _get_tailscale_ip(self) -> Optional[str]:
        """Get Tailscale assigned IP address."""
        try:
            result = await self._run_command(["tailscale", "ip", "-4"])

            if result["returncode"] == 0:
                ip = result["stdout"].strip()
                if ip and re.match(r"^\d+\.\d+\.\d+\.\d+$", ip):
                    return ip
            return None

        except Exception as e:
            logger.error(f"Failed to get Tailscale IP: {e}")
            return None

    async def disconnect_tailscale(self) -> Dict:
        """Disconnect from Tailscale."""
        try:
            result = await self._run_command(["sudo", "tailscale", "down"])

            if result["returncode"] == 0:
                self.status = "disconnected"
                self.assigned_ip = None
                logger.info("Tailscale disconnected")
                return {"status": "disconnected"}
            else:
                return {"status": "error", "message": result["stderr"]}

        except Exception as e:
            logger.error(f"Tailscale disconnect failed: {e}")
            return {"status": "error", "message": str(e)}

    # ==================== WireGuard ====================

    async def configure_wireguard(self, config_content: str) -> Dict:
        """Configure and connect to WireGuard."""
        try:
            logger.info("Configuring WireGuard")

            # Ensure WireGuard is installed
            if not await self._check_wireguard_installed():
                install_result = await self._install_wireguard()
                if install_result.get("status") != "success":
                    return install_result

            # Write configuration
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                f.write(config_content)

            # Set proper permissions
            await self._run_command(["sudo", "chmod", "600", str(self.config_path)])

            # Bring up interface
            result = await self._run_command(["sudo", "wg-quick", "up", "wg0"], timeout=30)

            if result["returncode"] != 0:
                return {
                    "status": "error",
                    "message": f"Failed to start WireGuard: {result['stderr']}",
                }

            # Get assigned IP from config
            ip = await self._get_wireguard_ip()

            if ip:
                self.provider = VPNProvider.WIREGUARD
                self.status = "connected"
                self.assigned_ip = ip
                logger.info(f"WireGuard connected: {ip}")
                return {"status": "connected", "provider": "wireguard", "ip_address": ip}
            else:
                return {"status": "error", "message": "Connected but no IP found"}

        except Exception as e:
            logger.error(f"WireGuard configuration failed: {e}")
            return {"status": "error", "message": str(e)}

    async def _check_wireguard_installed(self) -> bool:
        """Check if WireGuard is installed."""
        result = await self._run_command(["which", "wg-quick"])
        return result["returncode"] == 0

    async def _install_wireguard(self) -> Dict:
        """Install WireGuard."""
        try:
            logger.info("Installing WireGuard...")
            result = await self._run_command(
                ["sudo", "apt-get", "update", "&&", "sudo", "apt-get", "install", "-y", "wireguard"],
                shell=True,
                timeout=180,
            )

            if result["returncode"] == 0:
                logger.info("WireGuard installed successfully")
                return {"status": "success"}
            else:
                return {
                    "status": "error",
                    "message": f"Installation failed: {result['stderr']}",
                }

        except Exception as e:
            logger.error(f"WireGuard installation failed: {e}")
            return {"status": "error", "message": str(e)}

    async def _get_wireguard_ip(self) -> Optional[str]:
        """Get WireGuard IP from interface."""
        try:
            # Get IP from wg0 interface
            result = await self._run_command(["ip", "addr", "show", "wg0"])

            if result["returncode"] == 0:
                # Parse IP address from output
                match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", result["stdout"])
                if match:
                    return match.group(1)

            # Fallback: parse from config file
            if self.config_path.exists():
                with open(self.config_path, "r") as f:
                    config = f.read()
                    match = re.search(r"Address\s*=\s*(\d+\.\d+\.\d+\.\d+)", config)
                    if match:
                        return match.group(1)

            return None

        except Exception as e:
            logger.error(f"Failed to get WireGuard IP: {e}")
            return None

    async def disconnect_wireguard(self) -> Dict:
        """Disconnect from WireGuard."""
        try:
            result = await self._run_command(["sudo", "wg-quick", "down", "wg0"])

            if result["returncode"] == 0:
                self.status = "disconnected"
                self.assigned_ip = None
                logger.info("WireGuard disconnected")
                return {"status": "disconnected"}
            else:
                return {"status": "error", "message": result["stderr"]}

        except Exception as e:
            logger.error(f"WireGuard disconnect failed: {e}")
            return {"status": "error", "message": str(e)}

    # ==================== General Methods ====================

    async def disconnect(self) -> Dict:
        """Disconnect from current VPN."""
        if self.provider == VPNProvider.ZEROTIER:
            return await self.disconnect_zerotier()
        elif self.provider == VPNProvider.TAILSCALE:
            return await self.disconnect_tailscale()
        elif self.provider == VPNProvider.WIREGUARD:
            return await self.disconnect_wireguard()
        else:
            return {"status": "error", "message": "No active VPN connection"}

    def get_status(self) -> Dict:
        """Get VPN status."""
        return {
            "provider": self.provider.value if self.provider else None,
            "status": self.status,
            "ip_address": self.assigned_ip,
            "network_id": self.network_id if self.provider == VPNProvider.ZEROTIER else None,
        }

    async def _run_command(
        self, cmd: list, shell: bool = False, timeout: int = 30
    ) -> Dict:
        """Run shell command asynchronously."""
        try:
            if shell:
                # Join command list into string for shell execution
                cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
                process = await asyncio.create_subprocess_shell(
                    cmd_str,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            else:
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
