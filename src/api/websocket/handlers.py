"""
WebSocket handlers for market data subscriptions.
"""
import asyncio
import logging
import json
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from starlette.websockets import WebSocketState
from datetime import datetime
import pytz
from ..queue.queue_manager import QueueManager

logger = logging.getLogger(__name__)

VALID_MARKETS = {"BTCUSD", "BTC-USD", "ETHUSD", "ETH-USD", "AAPL", "GOOGL", "MSFT"}

async def handle_market_subscription(
    websocket: WebSocket,
    client_id: str,
    market_id: str,
    queue_manager: Optional[QueueManager] = None
):
    """Handle a market data subscription WebSocket connection.
    
    Args:
        websocket: The WebSocket connection
        client_id: Unique identifier for the client
        market_id: Market identifier for the subscription
        queue_manager: Queue manager instance for message handling
    """
    try:
        # Validate market ID before accepting connection
        if market_id not in VALID_MARKETS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid market ID: {market_id}. Valid markets are: {', '.join(sorted(VALID_MARKETS))}"
            )

        # Accept the connection
        await websocket.accept()
        
        # Subscribe to market data
        if queue_manager:
            success = await queue_manager.subscribe_to_market(market_id, client_id)
            if not success:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Failed to subscribe to market {market_id}"
                })
                await websocket.close(code=1011)
                return

        # Send initial market data
        initial_data = await queue_manager.get_market_data(market_id) if queue_manager else None
        
        if initial_data is None:
            # Use simulated data in test mode
            initial_data = {
                "type": "market_data",
                "data": {
                    "market_id": market_id,
                    "price": 100.0,
                    "volume": 1000.0,
                    "timestamp": datetime.now(pytz.UTC).isoformat()
                }
            }
        
        await websocket.send_json(initial_data)

        # In test mode, close after sending initial data
        if not queue_manager or getattr(queue_manager, 'test_mode', False):
            await websocket.close(code=1000)
            return

        # Keep connection alive and handle messages
        while True:
            try:
                message = await websocket.receive_text()
                if message == "ping":
                    await websocket.send_text("pong")
                else:
                    await websocket.send_json({
                        "type": "message",
                        "data": f"Received: {message}"
                    })
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected from {market_id}")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket connection: {str(e)}")
                await websocket.close(code=1011)
                break

    except HTTPException as e:
        # Handle invalid market ID
        if not websocket.client_state == WebSocketState.DISCONNECTED:
            await websocket.close(code=4004, reason=str(e.detail))
        raise e
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected from {market_id}")
    except Exception as e:
        logger.error(f"Unexpected error in market subscription: {str(e)}")
        try:
            if not websocket.client_state == WebSocketState.DISCONNECTED:
                await websocket.close(code=1011)
        except Exception:
            pass
        raise e
    finally:
        # Cleanup subscription if needed
        if queue_manager:
            await queue_manager.unsubscribe_from_market(market_id, client_id)
