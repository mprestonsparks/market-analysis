"""
WebSocket handlers for market data subscriptions.
"""
import asyncio
import logging
import json
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from ..queue.queue_manager import QueueManager
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

VALID_MARKETS = {"BTCUSD", "BTC-USD", "ETHUSD", "ETH-USD"}

async def handle_market_subscription(
    websocket: WebSocket,
    client_id: str,
    market_id: str,
    queue_manager: Optional[QueueManager] = None
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
        # Validate market ID before accepting connection
        if market_id not in VALID_MARKETS:
            await websocket.accept()
            await websocket.send_json({
                "type": "error",
                "message": f"Invalid market ID: {market_id}. Valid markets are: {', '.join(sorted(VALID_MARKETS))}"
            })
            await websocket.close(code=4004)
            return

        # Accept the connection
        await websocket.accept()

        # Subscribe to market data
        if queue_manager:
            try:
                success = await queue_manager.subscribe_to_market(market_id, client_id)
                if not success:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Failed to subscribe to market {market_id}"
                    })
                    await websocket.close(code=1011)
                    return
            except Exception as e:
                logger.error(f"Error subscribing to market: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Internal server error"
                })
                await websocket.close(code=1011)
                return

        # Send initial market data
        await websocket.send_json({
            "type": "market_data",
            "market_id": market_id,
            "timestamp": datetime.now(pytz.utc).isoformat(),
            "data": {
                "price": 50000.0,  # Test data
                "volume": 100.0
            }
        })

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

    except Exception as e:
        logger.error(f"Unexpected error in market subscription: {str(e)}")
        try:
            if not websocket.client_state == WebSocketState.DISCONNECTED:
                await websocket.accept()
                await websocket.send_json({
                    "type": "error",
                    "message": "Internal server error"
                })
                await websocket.close(code=1011)
        except Exception:
            pass

    finally:
        # Clean up subscription
        if queue_manager:
            try:
                await queue_manager.unsubscribe_from_market(market_id, client_id)
            except Exception as e:
                logger.error(f"Error unsubscribing from market: {str(e)}")
