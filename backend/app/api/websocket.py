"""WebSocket handler for real-time updates."""

import asyncio
import json
import logging
from fastapi import WebSocket, WebSocketDisconnect
from typing import Set

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept and track new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        self.active_connections.discard(websocket)
        logger.info(
            f"WebSocket disconnected. Total connections: {len(self.active_connections)}"
        )

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return

        # Convert message to JSON
        message_json = json.dumps(message)

        # Send to all connections
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()


async def websocket_handler(websocket: WebSocket, app):
    """Handle WebSocket connections."""
    await manager.connect(websocket)

    try:
        # Keep connection alive and handle incoming messages
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()

            # Parse message
            try:
                message = json.loads(data)
                message_type = message.get("type")

                # Handle different message types
                if message_type == "ping":
                    await websocket.send_json({"type": "pong"})

                elif message_type == "subscribe":
                    # Client subscribes to updates
                    await websocket.send_json(
                        {"type": "subscribed", "topics": message.get("topics", [])}
                    )

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def broadcast_system_stats(app):
    """Background task to broadcast system stats."""
    while True:
        try:
            # Get current stats
            system_monitor = app.state.system_monitor
            stats = system_monitor.get_current_stats()

            if stats:
                # Broadcast to all connected clients
                await manager.broadcast({"type": "system", "data": stats})

            # Wait before next broadcast
            await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"Error broadcasting system stats: {e}")
            await asyncio.sleep(5)


async def broadcast_mavlink_stats(app):
    """Background task to broadcast MAVLink stats."""
    while True:
        try:
            # Get MAVLink status
            mavlink_router = app.state.mavlink_router
            status = mavlink_router.get_status()

            if status.get("running"):
                # Broadcast to all connected clients
                await manager.broadcast({"type": "mavlink", "data": status})

            # Wait before next broadcast
            await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error broadcasting MAVLink stats: {e}")
            await asyncio.sleep(5)
