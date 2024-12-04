"""
Test error handling and rate limiting middleware.
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from src.api.app import app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_rate_limiting():
    """Test rate limiting middleware."""
    with TestClient(app) as client:
        # Test normal request
        response = client.get("/health")
        assert response.status_code == 200
        
        # Verify rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        
        # Test rate limiting by making many requests
        responses = []
        for _ in range(110):  # Over our 100 req/min limit
            responses.append(client.get("/health"))
        
        # Verify some requests were rate limited
        assert any(r.status_code == 429 for r in responses)
        
        # Check error response format
        rate_limited = next(r for r in responses if r.status_code == 429)
        error_response = rate_limited.json()
        assert "error" in error_response
        assert error_response["error"]["type"] == "HTTPException"
        assert "Too many requests" in error_response["error"]["message"]

def test_error_handling():
    """Test error handling middleware."""
    with TestClient(app) as client:
        # Test validation error
        response = client.post("/analyze", json={
            "invalid_field": "invalid_value"
        })
        assert response.status_code == 422
        error = response.json()
        assert "error" in error
        assert error["error"]["type"] == "ValidationError"
        
        # Test non-existent endpoint
        response = client.get("/non_existent")
        assert response.status_code == 404
        error = response.json()
        assert "error" in error
        assert error["error"]["type"] == "HTTPException"
        
        # Test malformed JSON
        response = client.post(
            "/analyze",
            headers={"Content-Type": "application/json"},
            data="invalid json"
        )
        assert response.status_code == 422
        error = response.json()
        assert "error" in error
        assert "type" in error["error"]

@pytest.mark.asyncio
async def test_websocket_error_handling():
    """Test WebSocket error handling."""
    with TestClient(app) as client:
        # Test invalid market ID
        with pytest.raises(Exception) as exc_info:
            with client.websocket_connect("/ws/market/invalid-market") as websocket:
                pass
        
        # Test disconnection handling
        with client.websocket_connect("/ws/market/BTC-USD") as websocket:
            # Close connection abruptly
            await websocket.close()
            
            # Try to send after close
            with pytest.raises(Exception):
                await websocket.send_json({"type": "test"})

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
