"""System monitoring service for CPU, memory, temperature, etc."""

import asyncio
import logging
import psutil
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SystemMonitor:
    """Monitors system resources and health."""

    def __init__(self):
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.current_stats: Dict = {}
        self.update_interval = 2  # seconds

    async def start(self) -> None:
        """Start system monitoring."""
        if self.running:
            return

        self.running = True
        self.task = asyncio.create_task(self._monitor_loop())
        logger.info("System monitor started")

    async def stop(self) -> None:
        """Stop system monitoring."""
        if not self.running:
            return

        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None

        logger.info("System monitor stopped")

    async def _monitor_loop(self) -> None:
        """Monitoring loop."""
        while self.running:
            try:
                self.current_stats = await self.get_stats()
                await asyncio.sleep(self.update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(self.update_interval)

    async def get_stats(self) -> Dict:
        """Get current system statistics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.5)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()

            # Memory usage
            memory = psutil.virtual_memory()

            # Disk usage
            disk = psutil.disk_usage("/")

            # CPU temperature (Raspberry Pi specific)
            temperature = await self._get_cpu_temperature()

            # Network stats
            network = await self._get_network_stats()

            # Uptime
            uptime = await self._get_uptime()

            return {
                "cpu": {
                    "percent": round(cpu_percent, 1),
                    "count": cpu_count,
                    "frequency_mhz": round(cpu_freq.current, 0) if cpu_freq else None,
                },
                "memory": {
                    "total_mb": round(memory.total / (1024 * 1024), 0),
                    "available_mb": round(memory.available / (1024 * 1024), 0),
                    "used_mb": round(memory.used / (1024 * 1024), 0),
                    "percent": round(memory.percent, 1),
                },
                "disk": {
                    "total_gb": round(disk.total / (1024 * 1024 * 1024), 1),
                    "used_gb": round(disk.used / (1024 * 1024 * 1024), 1),
                    "free_gb": round(disk.free / (1024 * 1024 * 1024), 1),
                    "percent": round(disk.percent, 1),
                },
                "temperature": temperature,
                "network": network,
                "uptime_seconds": uptime,
            }

        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {}

    async def _get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature (Raspberry Pi)."""
        try:
            # Try Raspberry Pi temperature file
            temp_file = Path("/sys/class/thermal/thermal_zone0/temp")
            if temp_file.exists():
                with open(temp_file, "r") as f:
                    temp_millicelsius = int(f.read().strip())
                    return round(temp_millicelsius / 1000.0, 1)

            # Try psutil sensors (may not be available)
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    # Try to find CPU temp
                    for name, entries in temps.items():
                        if "cpu" in name.lower():
                            if entries:
                                return round(entries[0].current, 1)

        except Exception as e:
            logger.debug(f"Could not read temperature: {e}")

        return None

    async def _get_network_stats(self) -> Dict:
        """Get network statistics."""
        try:
            net_io = psutil.net_io_counters()

            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "errors_in": net_io.errin,
                "errors_out": net_io.errout,
            }

        except Exception as e:
            logger.error(f"Failed to get network stats: {e}")
            return {}

    async def _get_uptime(self) -> Optional[int]:
        """Get system uptime in seconds."""
        try:
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.read().split()[0])
                return int(uptime_seconds)
        except Exception as e:
            logger.error(f"Failed to get uptime: {e}")
            return None

    def get_current_stats(self) -> Dict:
        """Get cached current stats."""
        return self.current_stats

    async def get_processes(self, sort_by: str = "cpu") -> list:
        """Get list of running processes."""
        try:
            processes = []

            for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                try:
                    pinfo = proc.info
                    processes.append(
                        {
                            "pid": pinfo["pid"],
                            "name": pinfo["name"],
                            "cpu_percent": round(pinfo["cpu_percent"] or 0, 1),
                            "memory_percent": round(pinfo["memory_percent"] or 0, 1),
                        }
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Sort processes
            if sort_by == "cpu":
                processes.sort(key=lambda x: x["cpu_percent"], reverse=True)
            elif sort_by == "memory":
                processes.sort(key=lambda x: x["memory_percent"], reverse=True)

            # Return top 20
            return processes[:20]

        except Exception as e:
            logger.error(f"Failed to get processes: {e}")
            return []

    async def get_disk_io(self) -> Dict:
        """Get disk I/O statistics."""
        try:
            disk_io = psutil.disk_io_counters()

            return {
                "read_bytes": disk_io.read_bytes,
                "write_bytes": disk_io.write_bytes,
                "read_count": disk_io.read_count,
                "write_count": disk_io.write_count,
            }

        except Exception as e:
            logger.error(f"Failed to get disk I/O: {e}")
            return {}
