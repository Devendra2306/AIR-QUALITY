from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from app.config.logging_config import logger
import json
import asyncio
from datetime import datetime


class ConnectionManager:
    """WebSocket connection manager for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.heartbeat_interval = 30
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()
        
        self.active_connections[client_id].add(websocket)
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
        
        # Send welcome message
        await self.send_personal_message(
            {"type": "connected", "message": "Connected to Air Quality Monitor", "timestamp": datetime.now().isoformat()},
            websocket
        )
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        """Remove a WebSocket connection."""
        if client_id in self.active_connections:
            self.active_connections[client_id].discard(websocket)
            
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
        
        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message to client: {str(e)}")
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        disconnected = set()
        
        for client_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to client {client_id}: {str(e)}")
                    disconnected.add((client_id, connection))
        
        # Clean up disconnected clients
        for client_id, connection in disconnected:
            self.disconnect(connection, client_id)
    
    async def broadcast_measurement(self, measurement: dict):
        """Broadcast a new measurement to all clients."""
        message = {
            "type": "measurement",
            "data": measurement,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def broadcast_alert(self, alert: dict):
        """Broadcast an alert to all clients."""
        message = {
            "type": "alert",
            "data": alert,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def start_heartbeat(self):
        """Start heartbeat to keep connections alive."""
        while True:
            await asyncio.sleep(self.heartbeat_interval)
            heartbeat_message = {
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat()
            }
            await self.broadcast(heartbeat_message)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return sum(len(connections) for connections in self.active_connections.values())


# Global connection manager instance
manager = ConnectionManager()
