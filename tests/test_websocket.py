"""
Test WebSocket functionality for market data streaming.
"""
import asyncio
import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
import websockets
import json
import logging

from src.api.app import app
from src.api.models import MarketDataRequest
from src.api.queue.queue_manager import QueueManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_market_websocket():
    """Test WebSocket connection and market data streaming."""
    async with websockets.connect('ws://localhost:8000/ws/market/BTC-USD') as websocket:
        # Subscribe to market updates
        await websocket.send(json.dumps({
            'action': 'subscribe',
            'market_id': 'BTC-USD'
        }))

        # Send a market analysis request
        async with TestClient(app) as client:
            response = await client.post(
                '/analyze',
                json={
                    'market_id': 'BTC-USD',
                    'timeframe': '1h',
                    'data': {
                        'prices': [100, 101, 102, 103, 104],
                        'volumes': [1000, 1100, 900, 1200, 1000]
                    }
                }
            )
            assert response.status_code == 200

        # Wait for the WebSocket message
        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(message)
            
            # Verify the message structure
            assert 'market_id' in data
            assert data['market_id'] == 'BTC-USD'
            assert 'timestamp' in data
            assert 'analysis' in data
            
            logger.info(f"Received market update: {data}")
            
        except asyncio.TimeoutError:
            pytest.fail("Timeout waiting for WebSocket message")
        except Exception as e:
            pytest.fail(f"Error in WebSocket test: {str(e)}")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
