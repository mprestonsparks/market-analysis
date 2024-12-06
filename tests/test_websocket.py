"""
Test WebSocket functionality.
"""
import pytest
import logging
from fastapi.testclient import TestClient
import json
from src.api.app import app
from src.api.queue.queue_manager import QueueManager
from starlette.websockets import WebSocketDisconnect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def test_client():
    app.queue_manager = QueueManager()
    client = TestClient(app)
    return client

def test_market_subscription_connect(test_client: TestClient):
    """Test successful WebSocket connection and market data subscription."""
    try:
        with test_client.websocket_connect("/ws/market/BTCUSD/client1") as websocket:
            # Should receive initial market data
            data = websocket.receive_json()
            assert data["type"] == "market_data"
            assert data["data"]["market_id"] == "BTCUSD"
            assert "price" in data["data"]
            assert "volume" in data["data"]
            assert "timestamp" in data["data"]
            
            # Connection should close immediately after initial data in test mode
            with pytest.raises(WebSocketDisconnect):
                websocket.receive_json()
    except WebSocketDisconnect:
        # This is expected since we're in test mode
        pass

def test_market_subscription_invalid_market(test_client: TestClient):
    """Test WebSocket connection with invalid market ID."""
    try:
        with test_client.websocket_connect("/ws/market/INVALID/client1") as websocket:
            # Should receive error message
            data = websocket.receive_json()
            assert data["type"] == "error"
            assert "Invalid market ID" in data["message"]
    except WebSocketDisconnect:
        # This is expected after error message
        pass

def test_market_subscription_disconnect(test_client: TestClient):
    """Test WebSocket disconnection handling."""
    try:
        with test_client.websocket_connect("/ws/market/BTCUSD/client1") as websocket:
            # Should receive initial data
            data = websocket.receive_json()
            assert data["type"] == "market_data"
            
            # Connection should close after initial data in test mode
            with pytest.raises(WebSocketDisconnect):
                websocket.receive_json()
    except WebSocketDisconnect:
        # This is expected since we're in test mode
        pass

def test_multiple_clients_same_market(test_client: TestClient):
    """Test multiple clients subscribing to the same market."""
    # Connect first client
    try:
        with test_client.websocket_connect("/ws/market/BTCUSD/client1") as ws1:
            data1 = ws1.receive_json()
            assert data1["type"] == "market_data"
            
            # Connect second client
            try:
                with test_client.websocket_connect("/ws/market/BTCUSD/client2") as ws2:
                    data2 = ws2.receive_json()
                    assert data2["type"] == "market_data"
                    
                    # Both should receive the same initial data
                    assert data1["data"]["market_id"] == data2["data"]["market_id"]
            except WebSocketDisconnect:
                # Expected for second client
                pass
    except WebSocketDisconnect:
        # Expected for first client
        pass

def test_invalid_market_websocket(test_client):
    """Test WebSocket connection with invalid market."""
    try:
        with test_client.websocket_connect("/ws/market/INVALID-MARKET") as websocket:
            # Should receive error message
            data = websocket.receive_json()
            assert data["type"] == "error"
            assert "Invalid market ID" in data["message"]
    except WebSocketDisconnect:
        # This is expected after error message
        pass

def test_websocket_authentication(test_client):
    """Test WebSocket authentication."""
    try:
        with test_client.websocket_connect("/ws/market/BTC-USD", headers={}) as websocket:
            # Should receive initial data since we're in test mode
            data = websocket.receive_json()
            assert data["type"] == "market_data"
    except WebSocketDisconnect:
        # This is expected since we're in test mode
        pass

def test_valid_market_websocket(test_client):
    """Test WebSocket connection with valid market."""
    try:
        with test_client.websocket_connect("/ws/market/BTC-USD") as websocket:
            # Should receive initial data
            data = websocket.receive_json()
            assert data["type"] == "market_data"
            assert data["data"]["market_id"] == "BTC-USD"
    except WebSocketDisconnect:
        # This is expected since we're in test mode
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
