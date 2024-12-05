"""
Detailed tests for rate limiting middleware.
"""
import pytest
from fastapi.testclient import TestClient
import time
from datetime import datetime
from src.api.app import app

@pytest.fixture
def test_client():
    return TestClient(app)

def test_rate_limit_headers(test_client):
    """Test the presence and correctness of rate limit headers."""
    response = test_client.get("/health")
    assert response.status_code == 200
    
    # Check header presence
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers
    
    # Check header values
    assert int(response.headers["X-RateLimit-Limit"]) == 100
    assert int(response.headers["X-RateLimit-Remaining"]) == 99
    assert float(response.headers["X-RateLimit-Reset"]) > time.time()

def test_rate_counter_decrement(test_client):
    """Test that the rate counter properly decrements."""
    # Make 5 requests and check the counter
    remaining_values = []
    for _ in range(5):
        response = test_client.get("/health")
        assert response.status_code == 200
        remaining = int(response.headers["X-RateLimit-Remaining"])
        remaining_values.append(remaining)
    
    # Verify decreasing sequence
    assert remaining_values == [99, 98, 97, 96, 95]

def test_rate_limit_boundary(test_client):
    """Test behavior exactly at the rate limit boundary."""
    # Make exactly 100 requests
    for i in range(100):
        response = test_client.get("/health")
        assert response.status_code == 200
        remaining = int(response.headers["X-RateLimit-Remaining"])
        assert remaining == 99 - i
    
    # The 101st request should fail
    response = test_client.get("/health")
    assert response.status_code == 429
    error_response = response.json()
    assert "error" in error_response
    assert error_response["error"]["type"] == "HTTPException"
    assert "Too many requests" in error_response["error"]["message"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
