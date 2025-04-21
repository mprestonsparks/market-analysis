"""
Tests for the Market Analysis API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import json
from decimal import Decimal

from src.api.app import app
from src.api.models.analysis import (
    AnalysisRequest,
    AnalysisResult,
    SignalThresholds,
    TechnicalIndicator,
    MarketState,
    TradingSignal
)

client = TestClient(app)

@pytest.fixture
def valid_analysis_request():
    """Fixture for a valid analysis request."""
    return {
        "symbol": "AAPL",
        "indicators": ["RSI", "MACD", "BB"],
        "state_analysis": True,
        "num_states": 3,
        "thresholds": {
            "rsi_oversold": 30.0,
            "rsi_overbought": 70.0,
            "rsi_weight": 0.4,
            "macd_threshold_std": 1.5,
            "macd_weight": 0.4,
            "stoch_oversold": 20.0,
            "stoch_overbought": 80.0,
            "stoch_weight": 0.2,
            "min_signal_strength": 0.1,
            "min_confidence": 0.5
        }
    }

def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"

def test_readiness_check():
    """Test the readiness check endpoint."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "system" in data["checks"]
    assert "dependencies" in data["checks"]

def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Market Analysis API"
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"

def test_analyze_valid_request(valid_analysis_request):
    """Test the analyze endpoint with a valid request."""
    response = client.post("/analyze", json=valid_analysis_request)
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "symbol" in data
    assert "timestamp" in data
    assert "current_price" in data
    assert "technical_indicators" in data
    assert "market_state" in data
    
    # Verify technical indicators
    indicators = data["technical_indicators"]
    assert len(indicators) > 0
    for indicator in indicators:
        assert "name" in indicator
        assert "value" in indicator
        assert isinstance(indicator["value"], (int, float))

def test_analyze_invalid_symbol():
    """Test the analyze endpoint with an invalid symbol."""
    request = {
        "symbol": "INVALID_SYMBOL",
        "indicators": ["RSI"],
        "state_analysis": True,
        "num_states": 3
    }
    response = client.post("/analyze", json=request)
    assert response.status_code == 400
    assert "No data available for symbol" in response.json()["detail"]

def test_analyze_invalid_num_states():
    """Test the analyze endpoint with invalid number of states."""
    request = {
        "symbol": "AAPL",
        "indicators": ["RSI"],
        "state_analysis": True,
        "num_states": 10  # More than allowed
    }
    response = client.post("/analyze", json=request)
    assert response.status_code == 422  # Validation error

def test_analyze_custom_thresholds(valid_analysis_request):
    """Test the analyze endpoint with custom thresholds."""
    # Modify thresholds
    valid_analysis_request["thresholds"]["rsi_oversold"] = 25.0
    valid_analysis_request["thresholds"]["rsi_overbought"] = 75.0
    
    response = client.post("/analyze", json=valid_analysis_request)
    assert response.status_code == 200
    data = response.json()
    
    # Find RSI indicator
    rsi_indicator = next(
        (i for i in data["technical_indicators"] if i["name"] == "RSI"),
        None
    )
    if rsi_indicator:
        assert rsi_indicator["lower_threshold"] == 25.0
        assert rsi_indicator["upper_threshold"] == 75.0

def test_analyze_date_range(valid_analysis_request):
    """Test the analyze endpoint with custom date range."""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    valid_analysis_request["start_time"] = start_time.isoformat()
    valid_analysis_request["end_time"] = end_time.isoformat()
    
    response = client.post("/analyze", json=valid_analysis_request)
    assert response.status_code == 200

def test_analyze_state_characteristics(valid_analysis_request):
    """Test market state characteristics in analysis response."""
    response = client.post("/analyze", json=valid_analysis_request)
    assert response.status_code == 200
    data = response.json()
    
    state = data["market_state"]
    assert state is not None
    assert "state_id" in state
    assert "characteristics" in state
    
    chars = state["characteristics"]
    assert "volatility" in chars
    assert "trend_strength" in chars
    assert "volume" in chars
    assert "return_dispersion" in chars
    
    # Verify characteristic values are within expected ranges
    assert 0 <= chars["volatility"] <= 1
    assert isinstance(chars["trend_strength"], (int, float))
    assert chars["volume"] >= 0
    assert chars["return_dispersion"] >= 0

def test_analyze_signal_generation(valid_analysis_request):
    """Test trading signal generation in analysis response."""
    response = client.post("/analyze", json=valid_analysis_request)
    assert response.status_code == 200
    data = response.json()
    
    if data["latest_signal"]:
        signal = data["latest_signal"]
        assert "timestamp" in signal
        assert signal["signal_type"] in ["BUY", "SELL"]
        assert 0 <= signal["confidence"] <= 1
        assert len(signal["indicators"]) > 0

def test_analyze_performance():
    """Test API endpoint performance."""
    request = {
        "symbol": "AAPL",
        "indicators": ["RSI", "MACD", "BB"],
        "state_analysis": True,
        "num_states": 3
    }
    
    import time
    start_time = time.time()
    
    response = client.post("/analyze", json=request)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    assert response.status_code == 200
    assert elapsed_time < 5.0  # Response should be under 5 seconds

def test_error_handling():
    """Test various error scenarios."""
    # Test missing required field
    response = client.post("/analyze", json={})
    assert response.status_code == 422
    
    # Test invalid indicator
    response = client.post("/analyze", json={
        "symbol": "AAPL",
        "indicators": ["INVALID_INDICATOR"],
        "state_analysis": True
    })
    assert response.status_code == 400
    
    # Test invalid date range
    future_date = (datetime.now() + timedelta(days=365)).isoformat()
    response = client.post("/analyze", json={
        "symbol": "AAPL",
        "start_time": future_date,
        "end_time": future_date
    })
    assert response.status_code == 400
