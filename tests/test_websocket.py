"""
Test WebSocket functionality.
"""
import asyncio
import pytest
from fastapi.testclient import TestClient
import json
from src.api.app import app
from src.api.queue.queue_manager import QueueManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture(scope="module")
async def test_client():
    # Initialize queue manager and connections before tests
    app.queue_manager = QueueManager()
    await app.queue_manager.initialize_rabbitmq()
    yield TestClient(app)
    await app.queue_manager.cleanup()

@pytest.mark.asyncio
async def test_market_websocket(test_client):
    """Test WebSocket connection and market data streaming."""
    async with test_client.websocket_connect("/ws/market/BTC-USD") as websocket:
        # Test initial connection
        data = await websocket.receive_json()
        assert "status" in data
        assert data["status"] == "connected"
        
        # Test market data subscription
        await websocket.send_json({"action": "subscribe"})
        data = await websocket.receive_json()
        assert "type" in data
        assert data["type"] == "market_data"
        
        # Test market data format
        assert "symbol" in data
        assert "price" in data
        assert "timestamp" in data

        # Test unsubscribe
        await websocket.send_json({"action": "unsubscribe"})
        data = await websocket.receive_json()
        assert data["status"] == "unsubscribed"

        # Send a market analysis request
        response = await test_client.post(
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
            message = await asyncio.wait_for(websocket.receive(), timeout=5.0)
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

@pytest.mark.asyncio
async def test_invalid_market_websocket(test_client):
    """Test WebSocket connection with invalid market."""
    with pytest.raises(Exception):
        async with test_client.websocket_connect("/ws/market/INVALID") as websocket:
            pass

@pytest.mark.asyncio
async def test_websocket_authentication(test_client):
    """Test WebSocket authentication."""
    async with test_client.websocket_connect(
        "/ws/market/BTC-USD",
        headers={"Authorization": "Bearer invalid_token"}
    ) as websocket:
        data = await websocket.receive_json()
        assert "error" in data
        assert data["error"]["type"] == "AuthenticationError"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
