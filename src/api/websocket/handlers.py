"""
WebSocket event handlers for market data streaming.
"""
import logging
import json
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect
from .connection import manager
from ..queue.queue_manager import QueueManager

logger = logging.getLogger(__name__)

async def handle_market_subscription(
    websocket: WebSocket,
    client_id: str,
    market_id: str,
    queue_manager: QueueManager
):
    """
    Handle a market data subscription WebSocket connection.
    
    Args:
        websocket (WebSocket): The WebSocket connection
        client_id (str): Unique identifier for the client
        market_id (str): Market identifier for the subscription
        queue_manager (QueueManager): Queue manager instance for message handling
    """
    try:
        await manager.connect(websocket, client_id, market_id)
        
        # Subscribe to market updates from Redis
        pubsub = await queue_manager.redis_client.subscribe_to_market(market_id)
        
        try:
            while True:
                # Wait for message from Redis
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message is not None:
                    try:
                        data = json.loads(message['data'])
                        await manager.broadcast(data, market_id)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode message: {str(e)}")
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}")
                
                # Check if client is still connected
                if websocket.client_state != WebSocket.client_state.CONNECTED:
                    break
                
        finally:
            # Unsubscribe and cleanup
            await queue_manager.redis_client.unsubscribe_from_market(market_id)
            await manager.disconnect(websocket, market_id)
            
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected from market {market_id}")
        await manager.disconnect(websocket, market_id)
    except Exception as e:
        logger.error(f"Error in market subscription handler: {str(e)}")
        await manager.disconnect(websocket, market_id)
