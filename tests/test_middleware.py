"""
Test middleware functionality.
"""
import pytest
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from src.api.middleware import RateLimiter
from src.api.websocket.handlers import handle_market_subscription

@pytest.fixture
def test_app():
    """Create test FastAPI app with middleware."""
    app = FastAPI()
    rate_limiter = RateLimiter(app, requests_per_minute=100, test_mode=True)
    app.add_middleware(RateLimiter)
    
    @app.get("/test")
    def test_endpoint():
        return {"status": "ok"}
    
    @app.websocket("/ws/market/{market_id}")
    async def websocket_endpoint(websocket: WebSocket, market_id: str):
        await handle_market_subscription(websocket, "test-client", market_id, None)
        
    return app, rate_limiter

@pytest.fixture
def test_client(test_app):
    """Create test client."""
    app, rate_limiter = test_app
    client = TestClient(app)
    # Reset rate limiter before each test
    rate_limiter.reset()
    return client

def test_rate_limiting(test_client, test_app):
    """Test rate limiting middleware."""
    app, rate_limiter = test_app
    
    # Test normal request
    response = test_client.get("/test")
    assert response.status_code == 200
    
    # Verify rate limit headers
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers
    
    # Test rate limiting by making many requests
    responses = []
    for _ in range(110):  # Over our 100 req/min limit
        responses.append(test_client.get("/test"))
    
    # Verify some requests were rate limited
    assert any(r.status_code == 429 for r in responses)
    
    # Verify error response format
    rate_limited = next(r for r in responses if r.status_code == 429)
    error_response = rate_limited.json()
    assert "error" in error_response
    assert error_response["error"] == "Rate limit exceeded"

def test_error_handling(test_client, test_app):
    """Test error handling middleware."""
    app, rate_limiter = test_app
    rate_limiter.reset()
    
    # Test validation error
    response = test_client.post("/test", json={
        "invalid_field": "invalid_value"
    })
    assert response.status_code == 405  # Method not allowed
    
    # Test rate limit error
    for _ in range(110):  # Over our 100 req/min limit
        test_client.get("/test")
    
    response = test_client.get("/test")
    assert response.status_code == 429
    assert response.headers["Content-Type"] == "application/json"
    assert "X-RateLimit-Reset" in response.headers
    assert "Retry-After" in response.headers

def test_websocket_error_handling(test_client, test_app):
    """Test WebSocket error handling."""
    app, rate_limiter = test_app
    rate_limiter.reset()
    
    # Test invalid market ID
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with test_client.websocket_connect("/ws/market/invalid-market"):
            pass
    assert exc_info.value.code == 4004

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
