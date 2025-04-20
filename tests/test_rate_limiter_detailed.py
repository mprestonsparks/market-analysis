"""Detailed tests for rate limiter functionality."""
import pytest
import time
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api.middleware import RateLimiter

@pytest.fixture
def test_app():
    """Create test FastAPI app with rate limiter."""
    app = FastAPI()
    rate_limiter = RateLimiter(app, requests_per_minute=100, test_mode=True)
    app.add_middleware(RateLimiter)
    
    @app.get("/test")
    def test_endpoint():
        return {"status": "ok"}
        
    return app, rate_limiter

@pytest.fixture
def test_client(test_app):
    """Create test client with rate limiter."""
    app, rate_limiter = test_app
    client = TestClient(app)
    # Reset rate limiter before each test
    rate_limiter.reset()
    return client

def test_rate_limit_headers(test_client):
    """Test the presence and correctness of rate limit headers."""
    response = test_client.get("/test")
    assert response.status_code == 200
    
    # Check headers
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers
    
    # Verify values
    assert int(response.headers["X-RateLimit-Limit"]) == 100
    assert int(response.headers["X-RateLimit-Remaining"]) == 99
    assert int(response.headers["X-RateLimit-Reset"]) > 0

def test_rate_counter_decrement(test_client, test_app):
    """Test that rate counter decrements after window expiry."""
    app, rate_limiter = test_app
    
    # Make initial request
    response = test_client.get("/test")
    assert response.status_code == 200
    initial_remaining = int(response.headers["X-RateLimit-Remaining"])
    
    # Make another request
    response = test_client.get("/test")
    assert response.status_code == 200
    assert int(response.headers["X-RateLimit-Remaining"]) == initial_remaining - 1

def test_rate_limit_boundary(test_client, test_app):
    """Test behavior at rate limit boundary."""
    app, rate_limiter = test_app
    
    # Make exactly 100 requests
    responses = []
    for _ in range(100):
        response = test_client.get("/test")
        responses.append(response)
        assert response.status_code == 200
    
    # Verify all succeeded
    assert all(r.status_code == 200 for r in responses)
    
    # Next request should fail
    response = test_client.get("/test")
    assert response.status_code == 429
    assert response.headers["Content-Type"] == "application/json"
    assert "Retry-After" in response.headers
    
    error_response = response.json()
    assert error_response["error"] == "Rate limit exceeded"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
