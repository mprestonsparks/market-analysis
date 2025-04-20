"""
Performance tests for the Market Analysis API.
"""
import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from unittest.mock import patch

from src.api.app import app

client = TestClient(app)

def make_request(symbol):
    """Helper function to make an analysis request."""
    return client.post("/analyze", json={
        "symbol": symbol,
        "indicators": ["RSI", "MACD", "BB"],
        "state_analysis": True,
        "num_states": 3
    })

@pytest.mark.performance
def test_concurrent_requests():
    """Test API performance under concurrent load."""
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
    num_requests = 5  
    max_workers = 3   
    
    start_time = time.time()
    successful_requests = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for _ in range(num_requests):
            for symbol in symbols:
                futures.append(executor.submit(make_request, symbol))
        
        for future in as_completed(futures):
            response = future.result()
            if response.status_code == 200:
                successful_requests += 1
    
    end_time = time.time()
    total_time = end_time - start_time
    requests_per_second = successful_requests / total_time
    
    # Performance assertions
    assert successful_requests > 0
    assert requests_per_second >= 0.5  
    assert total_time < 30.0  

@pytest.mark.performance
def test_response_time():
    """Test individual request response time."""
    symbols = ["AAPL", "MSFT", "GOOGL"]
    response_times = []
    
    for symbol in symbols:
        start_time = time.time()
        response = make_request(symbol)
        end_time = time.time()
        
        assert response.status_code == 200
        response_times.append(end_time - start_time)
    
    avg_response_time = sum(response_times) / len(response_times)
    max_response_time = max(response_times)
    
    # Performance assertions
    assert avg_response_time < 2.0  
    assert max_response_time < 3.0  

@pytest.mark.performance
def test_memory_usage():
    """Test memory usage during analysis."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Reduced number of requests
    for _ in range(3):  
        response = make_request("AAPL")
        assert response.status_code == 200
    
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory
    
    # Memory usage assertions
    assert memory_increase < 200  

@pytest.mark.performance
def test_data_volume():
    """Test API performance with different data volumes."""
    end_time = datetime.now()
    time_ranges = [
        timedelta(days=7),    
        timedelta(days=14),   
        timedelta(days=30)    
    ]  
    
    for time_range in time_ranges:
        start_time = end_time - time_range
        
        request_time = time.time()
        response = client.post("/analyze", json={
            "symbol": "AAPL",
            "indicators": ["RSI", "MACD", "BB"],
            "state_analysis": True,
            "num_states": 3,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        })
        response_time = time.time() - request_time
        
        assert response.status_code == 200
        # Adjusted time expectations
        assert response_time < (time_range.days / 7) * 2  

@pytest.mark.performance
def test_indicator_scaling():
    """Test performance scaling with number of indicators."""
    indicator_sets = [
        ["RSI"],
        ["RSI", "MACD"],
        ["RSI", "MACD", "BB"]
    ]  
    
    response_times = []
    for indicators in indicator_sets:
        start_time = time.time()
        response = client.post("/analyze", json={
            "symbol": "AAPL",
            "indicators": indicators,
            "state_analysis": True,
            "num_states": 3
        })
        end_time = time.time()
        
        assert response.status_code == 200
        response_times.append(end_time - start_time)
    
    # Performance should scale roughly linearly with number of indicators
    for i in range(1, len(response_times)):
        ratio = response_times[i] / response_times[0]
        assert ratio < len(indicator_sets[i]) * 2.0  

@pytest.mark.performance
def test_error_response_time():
    """Test performance of error responses."""
    error_cases = [
        {"symbol": "INVALID_SYMBOL"},
        {"symbol": "AAPL", "num_states": 10},
        {"symbol": "AAPL", "indicators": ["INVALID"]},
        {"symbol": "AAPL", "start_time": "invalid_date"}
    ]
    
    for case in error_cases:
        start_time = time.time()
        response = client.post("/analyze", json=case)
        response_time = time.time() - start_time
        
        assert response.status_code in [400, 422]
        assert response_time < 0.5  
