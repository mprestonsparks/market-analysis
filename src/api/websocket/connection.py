"""
WebSocket connection management module.
"""
import logging
from typing import Dict, Set
from fastapi import WebSocket
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""
    
    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.logger = logging.getLogger(__name__)
    
    async def connect(self, websocket: WebSocket, client_id: str, market_id: str):
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket (WebSocket): The WebSocket connection
            client_id (str): Unique identifier for the client
            market_id (str): Market identifier for the subscription
        """
        await websocket.accept()
        if market_id not in self.active_connections:
            self.active_connections[market_id] = set()
        self.active_connections[market_id].add(websocket)
        self.logger.info(f"Client {client_id} connected to market {market_id}")
    
    async def disconnect(self, websocket: WebSocket, market_id: str):
        """
        Remove a WebSocket connection.
        
        Args:
            websocket (WebSocket): The WebSocket connection to remove
            market_id (str): Market identifier for the subscription
        """
        if market_id in self.active_connections:
            self.active_connections[market_id].discard(websocket)
            if not self.active_connections[market_id]:
                del self.active_connections[market_id]
    
    async def broadcast(self, message: dict, market_id: str):
        """
        Broadcast a message to all connected clients for a specific market.
        
        Args:
            message (dict): The message to broadcast
            market_id (str): Market identifier for the broadcast
        """
        if market_id not in self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections[market_id]:
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_json(message)
            except Exception as e:
                self.logger.error(f"Error broadcasting to client: {str(e)}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            await self.disconnect(connection, market_id)

# Global connection manager instance
manager = ConnectionManager()
