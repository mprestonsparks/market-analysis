"""
Test WebSocket functionality.
"""
import pytest
import logging
from fastapi.testclient import TestClient
import json
from src.api.app import app
from src.api.queue.queue_manager import QueueManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def test_client():
    app.queue_manager = QueueManager()
    client = TestClient(app)
    return client

def test_market_websocket(test_client):
    """Test WebSocket connection and market data streaming."""
    with test_client.websocket_connect("/ws/market/BTC-USD") as websocket:
        data = websocket.receive_json()
        assert "type" in data
        assert "data" in data

def test_invalid_market_websocket(test_client):
    """Test WebSocket connection with invalid market."""
    with pytest.raises(Exception):  # WebSocket should fail to connect
        with test_client.websocket_connect("/ws/market/INVALID-MARKET"):
            pass

def test_websocket_authentication(test_client):
    """Test WebSocket authentication."""
    # Test without authentication
    with pytest.raises(Exception):
        with test_client.websocket_connect("/ws/market/BTC-USD", headers={}):
            pass
    
    # Test with invalid authentication
    with pytest.raises(Exception):
        with test_client.websocket_connect("/ws/market/BTC-USD", headers={"Authorization": "invalid"}):
            pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
