"""
Detailed tests for rate limiting middleware.
"""
import pytest
from fastapi.testclient import TestClient
import time
from datetime import datetime

@pytest.mark.asyncio
async def test_rate_limit_headers(test_client: TestClient):
    """Test the presence and correctness of rate limit headers."""
    client = await test_client
    response = client.get("/health")
    assert response.status_code == 200
    
    # Check header presence
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers
    
    # Check header values
    assert int(response.headers["X-RateLimit-Limit"]) == 100
    assert int(response.headers["X-RateLimit-Remaining"]) == 99
    assert float(response.headers["X-RateLimit-Reset"]) > time.time()

@pytest.mark.asyncio
async def test_rate_counter_decrement(test_client: TestClient):
    """Test that the rate counter properly decrements."""
    client = await test_client
    # Make 5 requests and check the counter
    remaining_values = []
    for _ in range(5):
        response = client.get("/health")
        assert response.status_code == 200
        remaining = int(response.headers["X-RateLimit-Remaining"])
        remaining_values.append(remaining)
    
    # Verify decreasing sequence
    assert remaining_values == [99, 98, 97, 96, 95]

@pytest.mark.asyncio
async def test_rate_limit_boundary(test_client: TestClient):
    """Test behavior exactly at the rate limit boundary."""
    client = await test_client
    # Make exactly 100 requests
    for i in range(100):
        response = client.get("/health")
        assert response.status_code == 200
        remaining = int(response.headers["X-RateLimit-Remaining"])
        assert remaining == 99 - i
    
    # The 101st request should fail
    response = client.get("/health")
    assert response.status_code == 429
    error_response = response.json()
    assert "error" in error_response
    assert error_response["error"]["type"] == "HTTPException"
    assert "Too many requests" in error_response["error"]["message"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
