"""Network and modem management service."""

import asyncio
import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class NetworkManager:
    """Manages network interfaces and modems."""

    def __init__(self):
        self.interfaces: Dict[str, Dict] = {}
        self.modem_info: Optional[Dict] = None

    async def get_interfaces(self) -> List[Dict]:
        """Get all network interfaces."""
        try:
            result = await self._run_command(["ip", "-j", "addr", "show"])

            if result["returncode"] == 0:
                import json

                interfaces = json.loads(result["stdout"])

                interface_list = []
                for iface in interfaces:
                    # Skip loopback
                    if iface["ifname"] == "lo":
                        continue

                    # Determine interface type
                    iface_type = self._determine_interface_type(iface["ifname"])

                    # Get IP addresses
                    ip_addresses = []
                    for addr in iface.get("addr_info", []):
                        if addr.get("family") in ["inet", "inet6"]:
                            ip_addresses.append(
                                {
                                    "family": addr["family"],
                                    "address": addr["local"],
                                    "prefix": addr.get("prefixlen"),
                                }
                            )

                    interface_list.append(
                        {
                            "name": iface["ifname"],
                            "type": iface_type,
                            "state": iface.get("operstate", "unknown"),
                            "mac": iface.get("address"),
                            "mtu": iface.get("mtu"),
                            "ip_addresses": ip_addresses,
                        }
                    )

                return interface_list

        except Exception as e:
            logger.error(f"Failed to get interfaces: {e}")

        return []

    def _determine_interface_type(self, ifname: str) -> str:
        """Determine interface type from name."""
        if ifname.startswith("wlan") or ifname.startswith("wlp"):
            return "wifi"
        elif ifname.startswith("eth") or ifname.startswith("enp"):
            return "ethernet"
        elif ifname.startswith("wwan") or ifname.startswith("usb"):
            return "cellular"
        elif ifname.startswith("zt"):
            return "zerotier"
        elif ifname.startswith("tailscale"):
            return "tailscale"
        elif ifname.startswith("wg"):
            return "wireguard"
        else:
            return "unknown"

    async def detect_modem(self) -> Optional[Dict]:
        """Detect LTE/4G modem."""
        try:
            # Try ModemManager first
            mm_result = await self._detect_modem_manager()
            if mm_result:
                self.modem_info = mm_result
                return mm_result

            # Try to detect USB modem devices
            usb_result = await self._detect_usb_modem()
            if usb_result:
                self.modem_info = usb_result
                return usb_result

            logger.info("No modem detected")
            return None

        except Exception as e:
            logger.error(f"Modem detection failed: {e}")
            return None

    async def _detect_modem_manager(self) -> Optional[Dict]:
        """Detect modem using ModemManager."""
        try:
            # Check if ModemManager is available
            which_result = await self._run_command(["which", "mmcli"])
            if which_result["returncode"] != 0:
                return None

            # List modems
            result = await self._run_command(["mmcli", "-L"])

            if result["returncode"] == 0 and "/org/freedesktop/ModemManager" in result["stdout"]:
                # Parse modem path
                match = re.search(r"/org/freedesktop/ModemManager\d+/Modem/(\d+)", result["stdout"])
                if match:
                    modem_id = match.group(1)

                    # Get modem details
                    details_result = await self._run_command(["mmcli", "-m", modem_id])

                    if details_result["returncode"] == 0:
                        details = details_result["stdout"]

                        # Parse modem information
                        manufacturer = self._extract_field(details, "manufacturer")
                        model = self._extract_field(details, "model")
                        signal = self._extract_field(details, "signal quality")

                        logger.info(f"Detected modem via ModemManager: {manufacturer} {model}")

                        return {
                            "type": "modemmanager",
                            "id": modem_id,
                            "manufacturer": manufacturer,
                            "model": model,
                            "signal_quality": signal,
                        }

        except Exception as e:
            logger.error(f"ModemManager detection failed: {e}")

        return None

    async def _detect_usb_modem(self) -> Optional[Dict]:
        """Detect USB modem devices."""
        try:
            result = await self._run_command(["lsusb"])

            if result["returncode"] == 0:
                # Look for common modem manufacturers
                modem_keywords = ["Huawei", "ZTE", "Sierra", "Qualcomm", "Telit", "Quectel"]

                for line in result["stdout"].split("\n"):
                    for keyword in modem_keywords:
                        if keyword.lower() in line.lower():
                            logger.info(f"Detected USB modem: {line}")
                            return {
                                "type": "usb",
                                "description": line.strip(),
                                "manufacturer": keyword,
                            }

        except Exception as e:
            logger.error(f"USB modem detection failed: {e}")

        return None

    def _extract_field(self, text: str, field_name: str) -> Optional[str]:
        """Extract field value from mmcli output."""
        pattern = rf"{field_name}:\s*(.+?)(?:\n|$)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            # Remove trailing pipe characters
            value = value.rstrip("|").strip()
            return value
        return None

    async def get_signal_strength(self) -> Optional[Dict]:
        """Get cellular signal strength."""
        if not self.modem_info:
            return None

        try:
            if self.modem_info["type"] == "modemmanager":
                modem_id = self.modem_info["id"]
                result = await self._run_command(
                    ["mmcli", "-m", modem_id, "--signal-get"]
                )

                if result["returncode"] == 0:
                    output = result["stdout"]

                    # Parse signal information
                    rssi = self._extract_field(output, "rssi")
                    rsrp = self._extract_field(output, "rsrp")
                    rsrq = self._extract_field(output, "rsrq")

                    return {
                        "rssi": rssi,
                        "rsrp": rsrp,
                        "rsrq": rsrq,
                    }

        except Exception as e:
            logger.error(f"Failed to get signal strength: {e}")

        return None

    async def get_connection_status(self) -> Dict:
        """Get network connection status."""
        try:
            # Get default route
            route_result = await self._run_command(["ip", "route", "show", "default"])

            if route_result["returncode"] == 0 and route_result["stdout"]:
                # Parse default interface
                match = re.search(r"dev\s+(\S+)", route_result["stdout"])
                if match:
                    default_interface = match.group(1)
                    interface_type = self._determine_interface_type(default_interface)

                    return {
                        "connected": True,
                        "interface": default_interface,
                        "type": interface_type,
                    }

            return {"connected": False, "interface": None, "type": None}

        except Exception as e:
            logger.error(f"Failed to get connection status: {e}")
            return {"connected": False, "interface": None, "type": None, "error": str(e)}

    async def test_connectivity(self, host: str = "8.8.8.8") -> Dict:
        """Test internet connectivity."""
        try:
            result = await self._run_command(["ping", "-c", "3", "-W", "5", host], timeout=15)

            if result["returncode"] == 0:
                # Parse ping statistics
                match = re.search(r"(\d+)% packet loss", result["stdout"])
                packet_loss = int(match.group(1)) if match else 100

                # Parse average RTT
                match = re.search(r"min/avg/max/mdev = [\d.]+/([\d.]+)", result["stdout"])
                avg_rtt = float(match.group(1)) if match else None

                return {
                    "status": "online",
                    "packet_loss": packet_loss,
                    "avg_rtt_ms": avg_rtt,
                }
            else:
                return {"status": "offline", "packet_loss": 100, "avg_rtt_ms": None}

        except Exception as e:
            logger.error(f"Connectivity test failed: {e}")
            return {"status": "error", "message": str(e)}

    async def _run_command(self, cmd: list, timeout: int = 10) -> Dict:
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
