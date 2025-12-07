"""WebSocket manager for real-time data streaming to HMI"""
import logging
from typing import List, Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
import asyncio

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        """Initialize WebSocket manager"""
        self.active_connections: List[WebSocket] = []
        self.device_subscriptions: Dict[str, Set[WebSocket]] = {}
        self._broadcast_lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, device_id: str = None):
        """
        Accept a WebSocket connection

        Args:
            websocket: WebSocket connection
            device_id: Optional device ID to subscribe to specific device
        """
        await websocket.accept()
        self.active_connections.append(websocket)

        if device_id:
            if device_id not in self.device_subscriptions:
                self.device_subscriptions[device_id] = set()
            self.device_subscriptions[device_id].add(websocket)
            logger.info(f"WebSocket connected and subscribed to device {device_id}")
        else:
            logger.info("WebSocket connected (all devices)")

    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection

        Args:
            websocket: WebSocket connection to remove
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        # Remove from device subscriptions
        for device_id, subscribers in self.device_subscriptions.items():
            if websocket in subscribers:
                subscribers.remove(websocket)

        logger.info("WebSocket disconnected")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Send a message to a specific WebSocket

        Args:
            message: Message to send
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message to WebSocket: {e}")

    async def broadcast(self, message: dict, device_id: str = None):
        """
        Broadcast a message to all connected WebSockets or device-specific subscribers

        Args:
            message: Message to broadcast
            device_id: Optional device ID to send only to subscribers
        """
        async with self._broadcast_lock:
            if device_id and device_id in self.device_subscriptions:
                # Send to device-specific subscribers
                subscribers = list(self.device_subscriptions[device_id])
            else:
                # Send to all connections
                subscribers = list(self.active_connections)

            # Send to all subscribers
            disconnected = []
            for connection in subscribers:
                try:
                    await connection.send_json(message)
                except WebSocketDisconnect:
                    disconnected.append(connection)
                except Exception as e:
                    logger.error(f"Error broadcasting to WebSocket: {e}")
                    disconnected.append(connection)

            # Clean up disconnected clients
            for connection in disconnected:
                self.disconnect(connection)

    async def broadcast_sensor_data(self, device_id: str, data: dict):
        """
        Broadcast sensor data update

        Args:
            device_id: Device ID
            data: Sensor data
        """
        message = {
            "type": "sensor_data",
            "device_id": device_id,
            "data": data
        }
        await self.broadcast(message, device_id)

    async def broadcast_safety_status(self, device_id: str, status: dict):
        """
        Broadcast safety status update

        Args:
            device_id: Device ID
            status: Safety status
        """
        message = {
            "type": "safety_status",
            "device_id": device_id,
            "status": status
        }
        await self.broadcast(message, device_id)

    async def broadcast_ai_analysis(self, device_id: str, analysis: dict):
        """
        Broadcast AI analysis results

        Args:
            device_id: Device ID
            analysis: AI analysis results
        """
        message = {
            "type": "ai_analysis",
            "device_id": device_id,
            "analysis": analysis
        }
        await self.broadcast(message, device_id)

    async def broadcast_system_status(self, status: dict):
        """
        Broadcast system status update

        Args:
            status: System status
        """
        message = {
            "type": "system_status",
            "status": status
        }
        await self.broadcast(message)

    def get_connection_count(self) -> int:
        """Get the number of active WebSocket connections"""
        return len(self.active_connections)

    def get_device_subscriber_count(self, device_id: str) -> int:
        """Get the number of subscribers for a specific device"""
        if device_id in self.device_subscriptions:
            return len(self.device_subscriptions[device_id])
        return 0


# Global WebSocket manager instance
_websocket_manager: WebSocketManager = None


def get_websocket_manager() -> WebSocketManager:
    """Get or create the global WebSocket manager"""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager


def set_websocket_manager(manager: WebSocketManager):
    """Set a custom WebSocket manager (for testing)"""
    global _websocket_manager
    _websocket_manager = manager
