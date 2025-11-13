"""MAVLink router service for forwarding telemetry data."""

import asyncio
import logging
import socket
from typing import Dict, List, Optional
from pymavlink import mavutil

logger = logging.getLogger(__name__)


class TelemetryDestination:
    """Represents a telemetry destination."""

    def __init__(self, name: str, host: str, port: int, protocol: str = "udp"):
        self.name = name
        self.host = host
        self.port = port
        self.protocol = protocol.lower()
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.listen_task: Optional[asyncio.Task] = None

    def connect(self) -> bool:
        """Establish connection to destination."""
        try:
            if self.protocol == "udp":
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.socket.setblocking(False)  # Non-blocking for async recv
                # Bind to receive data back from ground station
                self.socket.bind(('0.0.0.0', 0))  # Bind to any available port
                self.connected = True
                logger.info(f"Connected to {self.name} via UDP at {self.host}:{self.port}")
                return True
            elif self.protocol == "tcp":
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.host, self.port))
                self.socket.setblocking(False)  # Non-blocking for async recv
                self.connected = True
                logger.info(f"Connected to {self.name} via TCP at {self.host}:{self.port}")
                return True
            else:
                logger.error(f"Unknown protocol: {self.protocol}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to {self.name}: {e}")
            self.connected = False
            return False

    def send(self, data: bytes) -> bool:
        """Send data to destination."""
        if not self.connected or not self.socket:
            return False

        try:
            if self.protocol == "udp":
                self.socket.sendto(data, (self.host, self.port))
            elif self.protocol == "tcp":
                self.socket.send(data)
            return True
        except Exception as e:
            logger.error(f"Failed to send to {self.name}: {e}")
            self.connected = False
            return False

    def recv(self, bufsize: int = 4096) -> Optional[bytes]:
        """Receive data from destination (non-blocking)."""
        if not self.connected or not self.socket:
            return None

        try:
            if self.protocol == "udp":
                data, _ = self.socket.recvfrom(bufsize)
                return data
            elif self.protocol == "tcp":
                data = self.socket.recv(bufsize)
                return data if data else None
        except BlockingIOError:
            # No data available
            return None
        except Exception as e:
            logger.error(f"Failed to receive from {self.name}: {e}")
            self.connected = False
            return None

    def close(self) -> None:
        """Close connection."""
        if self.socket:
            self.socket.close()
            self.socket = None
        self.connected = False


class MAVLinkRouter:
    """MAVLink router for forwarding telemetry data."""

    def __init__(self):
        self.serial_port: Optional[str] = None
        self.baud_rate: int = 57600
        self.connection: Optional[mavutil.mavlink_connection] = None
        self.destinations: List[TelemetryDestination] = []
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.heartbeat_received = False
        self.auto_retry = True
        self.max_retries = 10
        self.retry_delay = 5  # seconds
        self.retry_count = 0
        self.heartbeat_timeout = 10  # seconds without heartbeat before reconnect
        self.stats = {
            "messages_received": 0,
            "messages_forwarded": 0,
            "errors": 0,
            "last_heartbeat": None,
        }
        self.telemetry = {
            "altitude": None,
            "groundspeed": None,
            "airspeed": None,
            "heading": None,
            "battery_voltage": None,
            "battery_current": None,
            "battery_remaining": None,
            "latitude": None,
            "longitude": None,
            "gps_fix_type": None,
            "gps_satellites": None,
            "mode": None,
            "armed": False,
            "throttle": None,
            "climb_rate": None,
        }

    async def configure(self, config: Dict) -> Dict:
        """Configure MAVLink router."""
        try:
            self.serial_port = config.get("serial_port", "/dev/ttyACM0")
            self.baud_rate = config.get("baud_rate", 57600)
            logger.info(f"Configured MAVLink router: {self.serial_port} @ {self.baud_rate}")
            return {"status": "configured", "serial_port": self.serial_port, "baud_rate": self.baud_rate}
        except Exception as e:
            logger.error(f"Failed to configure MAVLink router: {e}")
            return {"status": "error", "message": str(e)}

    async def add_destination(self, name: str, host: str, port: int, protocol: str = "udp") -> Dict:
        """Add telemetry destination."""
        try:
            # Check if destination already exists
            for dest in self.destinations:
                if dest.name == name:
                    return {"status": "error", "message": f"Destination '{name}' already exists"}

            dest = TelemetryDestination(name, host, port, protocol)
            if dest.connect():
                self.destinations.append(dest)

                # If routing is already running, start listen task for this destination
                if self.running:
                    dest.listen_task = asyncio.create_task(self._listen_from_destination(dest))
                    logger.info(f"Added destination: {name} ({host}:{port}) - bidirectional enabled")
                else:
                    logger.info(f"Added destination: {name} ({host}:{port})")

                return {"status": "added", "destination": name}
            else:
                return {"status": "error", "message": "Failed to connect to destination"}
        except Exception as e:
            logger.error(f"Failed to add destination: {e}")
            return {"status": "error", "message": str(e)}

    async def remove_destination(self, name: str) -> Dict:
        """Remove telemetry destination."""
        try:
            for dest in self.destinations:
                if dest.name == name:
                    # Cancel listen task if running
                    if dest.listen_task:
                        dest.listen_task.cancel()
                        try:
                            await dest.listen_task
                        except asyncio.CancelledError:
                            pass
                        dest.listen_task = None

                    dest.close()
                    self.destinations.remove(dest)
                    logger.info(f"Removed destination: {name}")
                    return {"status": "removed", "destination": name}

            return {"status": "error", "message": f"Destination '{name}' not found"}
        except Exception as e:
            logger.error(f"Failed to remove destination: {e}")
            return {"status": "error", "message": str(e)}

    async def start(self) -> Dict:
        """Start MAVLink routing."""
        if self.running:
            return {"status": "error", "message": "Already running"}

        if not self.serial_port:
            return {"status": "error", "message": "Serial port not configured"}

        try:
            # Connect to flight controller
            logger.info(f"Connecting to flight controller on {self.serial_port}...")
            self.connection = mavutil.mavlink_connection(
                self.serial_port, baud=self.baud_rate
            )

            # Wait for heartbeat (non-blocking with timeout)
            logger.info("Waiting for heartbeat...")
            heartbeat_timeout = 10  # seconds
            start_time = asyncio.get_event_loop().time()

            while not self.heartbeat_received:
                msg = self.connection.recv_match(type="HEARTBEAT", blocking=False)
                if msg:
                    self.heartbeat_received = True
                    self.stats["last_heartbeat"] = asyncio.get_event_loop().time()
                    logger.info(
                        f"Heartbeat received from system {self.connection.target_system}"
                    )
                    break

                if asyncio.get_event_loop().time() - start_time > heartbeat_timeout:
                    raise TimeoutError("No heartbeat received within timeout period")

                await asyncio.sleep(0.1)

            # Reconnect all destinations and start bidirectional tasks
            for dest in self.destinations:
                if not dest.connected:
                    dest.connect()
                # Start listening task for bidirectional communication
                dest.listen_task = asyncio.create_task(self._listen_from_destination(dest))

            # Start routing task
            self.running = True
            self.retry_count = 0  # Reset retry count on successful start
            self.task = asyncio.create_task(self._route_messages())

            logger.info("MAVLink routing started (bidirectional)")
            return {"status": "started", "target_system": self.connection.target_system}

        except Exception as e:
            logger.error(f"Failed to start MAVLink routing: {e}")
            self.running = False
            if self.connection:
                self.connection.close()
                self.connection = None
            return {"status": "error", "message": str(e)}

    async def stop(self) -> Dict:
        """Stop MAVLink routing."""
        if not self.running:
            return {"status": "error", "message": "Not running"}

        try:
            self.running = False

            # Cancel routing task
            if self.task:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
                self.task = None

            # Close connection to flight controller
            if self.connection:
                self.connection.close()
                self.connection = None

            # Cancel listen tasks and close all destination connections
            for dest in self.destinations:
                if dest.listen_task:
                    dest.listen_task.cancel()
                    try:
                        await dest.listen_task
                    except asyncio.CancelledError:
                        pass
                    dest.listen_task = None
                dest.close()

            self.heartbeat_received = False
            logger.info("MAVLink routing stopped")
            return {"status": "stopped"}

        except Exception as e:
            logger.error(f"Failed to stop MAVLink routing: {e}")
            return {"status": "error", "message": str(e)}

    async def _reconnect(self) -> bool:
        """Attempt to reconnect to flight controller."""
        try:
            logger.info("Attempting to reconnect to flight controller...")

            # Close old connection
            if self.connection:
                try:
                    self.connection.close()
                except:
                    pass
                self.connection = None

            # Cancel and restart all destination listen tasks
            for dest in self.destinations:
                if dest.listen_task:
                    dest.listen_task.cancel()
                    try:
                        await dest.listen_task
                    except asyncio.CancelledError:
                        pass
                    dest.listen_task = None

            # Wait a moment for serial port to be released
            await asyncio.sleep(1)

            # Try to reconnect
            logger.info(f"Reconnecting to {self.serial_port}...")
            self.connection = mavutil.mavlink_connection(
                self.serial_port, baud=self.baud_rate
            )

            # Wait for heartbeat with timeout
            logger.info("Waiting for heartbeat after reconnection...")
            heartbeat_timeout = 10  # seconds
            start_time = asyncio.get_event_loop().time()
            heartbeat_found = False

            while asyncio.get_event_loop().time() - start_time < heartbeat_timeout:
                msg = self.connection.recv_match(type="HEARTBEAT", blocking=False)
                if msg:
                    heartbeat_found = True
                    self.heartbeat_received = True
                    self.stats["last_heartbeat"] = asyncio.get_event_loop().time()
                    logger.info(f"Heartbeat received from system {self.connection.target_system}")
                    break
                await asyncio.sleep(0.1)

            if not heartbeat_found:
                logger.error("No heartbeat received after reconnection attempt")
                if self.connection:
                    self.connection.close()
                    self.connection = None
                return False

            # Reconnect all destinations and restart listen tasks
            for dest in self.destinations:
                if not dest.connected:
                    dest.connect()
                dest.listen_task = asyncio.create_task(self._listen_from_destination(dest))

            logger.info("Reconnection successful")
            return True

        except Exception as e:
            logger.error(f"Failed to reconnect: {e}")
            if self.connection:
                try:
                    self.connection.close()
                except:
                    pass
                self.connection = None
            return False

    async def _route_messages(self) -> None:
        """Route MAVLink messages to destinations."""
        logger.info("Starting message routing loop...")

        # Performance optimization: batch process messages
        message_batch = []
        batch_size = 10  # Process up to 10 messages before yielding
        idle_count = 0

        while self.running:
            try:
                # Check for heartbeat timeout (only check every 100 iterations when active)
                if self.auto_retry and self.stats["last_heartbeat"] and idle_count == 0:
                    time_since_heartbeat = asyncio.get_event_loop().time() - self.stats["last_heartbeat"]
                    if time_since_heartbeat > self.heartbeat_timeout:
                        logger.warning(f"No heartbeat for {time_since_heartbeat:.1f}s, connection may be lost")

                        # Attempt reconnection if within retry limit
                        if self.retry_count < self.max_retries:
                            self.retry_count += 1
                            logger.warning(f"Attempting reconnection {self.retry_count}/{self.max_retries}...")

                            # Attempt to reconnect
                            reconnected = await self._reconnect()
                            if reconnected:
                                logger.info("Successfully reconnected to flight controller")
                                self.retry_count = 0  # Reset on successful reconnection
                                continue
                            else:
                                logger.error(f"Reconnection attempt {self.retry_count} failed, waiting {self.retry_delay}s...")
                                await asyncio.sleep(self.retry_delay)
                                continue
                        else:
                            logger.error(f"Max reconnection attempts ({self.max_retries}) exceeded, stopping")
                            self.running = False
                            break

                # Try to receive multiple messages in one iteration for better throughput
                messages_processed = 0
                while messages_processed < batch_size:
                    msg = self.connection.recv_match(blocking=False)
                    if not msg:
                        break

                    messages_processed += 1
                    idle_count = 0  # Reset idle count when we have messages
                    self.stats["messages_received"] += 1

                    # Parse telemetry data
                    self._parse_telemetry(msg)

                    # Update last heartbeat time
                    if msg.get_type() == "HEARTBEAT":
                        self.stats["last_heartbeat"] = asyncio.get_event_loop().time()

                    # Forward to all destinations (batch the buffer)
                    msg_buf = msg.get_msgbuf()
                    for dest in self.destinations:
                        if dest.send(msg_buf):
                            self.stats["messages_forwarded"] += 1
                        else:
                            self.stats["errors"] += 1
                            # Try to reconnect destination
                            dest.connect()

                # Adaptive sleep: shorter when processing messages, longer when idle
                if messages_processed > 0:
                    # Very short sleep when actively processing
                    await asyncio.sleep(0.0001)
                else:
                    # Longer sleep when idle to reduce CPU usage
                    idle_count += 1
                    await asyncio.sleep(0.001 if idle_count < 100 else 0.01)

            except Exception as e:
                logger.error(f"Error in routing loop: {e}")
                self.stats["errors"] += 1

                # If error might be connection-related, try to reconnect
                if self.auto_retry and self.retry_count < self.max_retries:
                    self.retry_count += 1
                    logger.warning(f"Error in routing, attempting reconnection {self.retry_count}/{self.max_retries}...")
                    await asyncio.sleep(self.retry_delay)
                    reconnected = await self._reconnect()
                    if not reconnected:
                        logger.error("Reconnection after error failed")
                else:
                    await asyncio.sleep(0.1)

        logger.info("Message routing loop stopped")

    async def _listen_from_destination(self, dest: TelemetryDestination) -> None:
        """Listen for messages from ground station and forward to flight controller."""
        logger.info(f"Starting listen task for {dest.name}...")

        while self.running:
            try:
                # Receive data from ground station
                data = dest.recv()

                if data and self.connection:
                    # Forward to flight controller
                    self.connection.write(data)
                    logger.debug(f"Forwarded {len(data)} bytes from {dest.name} to flight controller")

                # Small sleep to prevent busy loop
                await asyncio.sleep(0.001)

            except Exception as e:
                logger.error(f"Error listening from {dest.name}: {e}")
                await asyncio.sleep(0.1)

        logger.info(f"Listen task for {dest.name} stopped")

    def _parse_telemetry(self, msg) -> None:
        """Parse MAVLink message and extract telemetry data."""
        msg_type = msg.get_type()

        try:
            if msg_type == "GLOBAL_POSITION_INT":
                self.telemetry["latitude"] = msg.lat / 1e7
                self.telemetry["longitude"] = msg.lon / 1e7
                self.telemetry["altitude"] = msg.alt / 1000.0  # Convert to meters
                self.telemetry["heading"] = msg.hdg / 100.0  # Convert to degrees

            elif msg_type == "VFR_HUD":
                self.telemetry["groundspeed"] = msg.groundspeed
                self.telemetry["airspeed"] = msg.airspeed
                self.telemetry["heading"] = msg.heading
                self.telemetry["throttle"] = msg.throttle
                self.telemetry["climb_rate"] = msg.climb

            elif msg_type == "SYS_STATUS":
                self.telemetry["battery_voltage"] = msg.voltage_battery / 1000.0  # mV to V
                self.telemetry["battery_current"] = msg.current_battery / 100.0  # cA to A
                self.telemetry["battery_remaining"] = msg.battery_remaining

            elif msg_type == "GPS_RAW_INT":
                self.telemetry["gps_fix_type"] = msg.fix_type
                self.telemetry["gps_satellites"] = msg.satellites_visible

            elif msg_type == "HEARTBEAT":
                # Extract mode and armed status
                self.telemetry["armed"] = bool(msg.base_mode & 128)  # MAV_MODE_FLAG_SAFETY_ARMED
                self.telemetry["mode"] = msg.custom_mode

        except Exception as e:
            logger.debug(f"Error parsing {msg_type}: {e}")

    def get_status(self) -> Dict:
        """Get router status."""
        return {
            "running": self.running,
            "connected": self.connection is not None,
            "heartbeat_received": self.heartbeat_received,
            "serial_port": self.serial_port,
            "baud_rate": self.baud_rate,
            "destinations": [
                {
                    "name": dest.name,
                    "host": dest.host,
                    "port": dest.port,
                    "protocol": dest.protocol,
                    "connected": dest.connected,
                }
                for dest in self.destinations
            ],
            "stats": self.stats,
            "telemetry": self.telemetry,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "auto_retry": self.auto_retry,
        }
