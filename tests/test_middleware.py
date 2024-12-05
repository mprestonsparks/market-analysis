"""
Test middleware functionality.
"""
import pytest
from fastapi.testclient import TestClient
import json

@pytest.fixture
async def test_client():
    from src.api.app import app
    async with TestClient(app) as client:
        yield client

@pytest.mark.asyncio
async def test_rate_limiting(test_client):
    """Test rate limiting middleware."""
    # Test normal request
    response = await test_client.get("/health")
    assert response.status_code == 200
    
    # Verify rate limit headers
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers
    
    # Test rate limiting by making many requests
    responses = []
    for _ in range(110):  # Over our 100 req/min limit
        responses.append(await test_client.get("/health"))
    
    # Verify some requests were rate limited
    assert any(r.status_code == 429 for r in responses)
    
    # Verify error response format
    rate_limited = next(r for r in responses if r.status_code == 429)
    error_response = rate_limited.json()
    assert "error" in error_response
    assert error_response["error"]["type"] == "HTTPException"
    assert "Too many requests" in error_response["error"]["message"]

@pytest.mark.asyncio
async def test_error_handling(test_client):
    """Test error handling middleware."""
    # Test validation error
    response = await test_client.post("/analyze", json={
        "invalid_field": "invalid_value"
    })
    assert response.status_code == 422
    error = response.json()
    assert "error" in error
    assert error["error"]["type"] == "ValidationError"
    
    # Test non-existent endpoint
    response = await test_client.get("/non_existent")
    assert response.status_code == 404
    error = response.json()
    assert "error" in error
    assert error["error"]["type"] == "HTTPException"
    
    # Test malformed JSON
    response = await test_client.post(
        "/analyze",
        headers={"Content-Type": "application/json"},
        data="invalid json"
    )
    assert response.status_code == 400
    error = response.json()
    assert "error" in error
    assert "type" in error["error"]

@pytest.mark.asyncio
async def test_websocket_error_handling(test_client):
    """Test WebSocket error handling."""
    # Test invalid market ID
    with pytest.raises(Exception) as exc_info:
        async with test_client.websocket_connect("/ws/market/invalid-market") as websocket:
            pass
    
    # Test disconnection handling
    async with test_client.websocket_connect("/ws/market/BTC-USD") as websocket:
        # Close connection abruptly
        await websocket.close()
        
        # Try to send after close
        with pytest.raises(Exception):
            await websocket.send_json({"type": "test"})

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
