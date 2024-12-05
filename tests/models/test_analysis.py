from datetime import datetime, timezone
from decimal import Decimal
import pytest
from pydantic import ValidationError

from src.api.models.analysis import (
    TechnicalIndicator,
    MarketState,
    TradingSignal,
    AnalysisRequest,
    AnalysisResult
)


def test_technical_indicator_valid():
    """Test creating a valid TechnicalIndicator instance."""
    data = {
        "name": "RSI",
        "value": 65.5,
        "upper_threshold": 70.0,
        "lower_threshold": 30.0
    }
    indicator = TechnicalIndicator(**data)
    assert indicator.name == data["name"]
    assert indicator.value == data["value"]
    assert indicator.upper_threshold == data["upper_threshold"]
    assert indicator.lower_threshold == data["lower_threshold"]


def test_market_state_valid():
    """Test creating a valid MarketState instance."""
    data = {
        "state_id": 1,
        "description": "Bullish Trend",
        "characteristics": {
            "volatility": 0.15,
            "trend_strength": 0.8,
            "volume": 1.2
        },
        "confidence": 0.85
    }
    state = MarketState(**data)
    assert state.state_id == data["state_id"]
    assert state.description == data["description"]
    assert state.characteristics == data["characteristics"]
    assert state.confidence == data["confidence"]


def test_analysis_request_valid():
    """Test creating a valid AnalysisRequest instance."""
    now = datetime.now(timezone.utc)
    data = {
        "symbol": "AAPL",
        "start_time": now,
        "end_time": now,
        "indicators": ["RSI", "MACD"],
        "state_analysis": True,
        "num_states": 3
    }
    request = AnalysisRequest(**data)
    assert request.symbol == data["symbol"]
    assert request.indicators == data["indicators"]
    assert request.state_analysis == data["state_analysis"]
    assert request.num_states == data["num_states"]


def test_analysis_request_default_indicators():
    """Test that default indicators are set correctly."""
    request = AnalysisRequest(symbol="AAPL")
    assert len(request.indicators) > 0
    assert "RSI" in request.indicators


def test_analysis_result_valid():
    """Test creating a valid AnalysisResult instance."""
    now = datetime.now(timezone.utc)
    
    # Create test data
    technical_indicators = [
        TechnicalIndicator(
            name="RSI",
            value=65.5,
            upper_threshold=70.0,
            lower_threshold=30.0
        )
    ]
    
    market_state = MarketState(
        state_id=1,
        description="Bullish Trend",
        characteristics={
            "volatility": 0.15,
            "trend_strength": 0.8,
            "volume": 1.2
        },
        confidence=0.85
    )
    
    trading_signal = TradingSignal(
        timestamp=now,
        signal_type="BUY",
        confidence=0.8,
        indicators=["RSI", "MACD"],
        state_context=market_state
    )
    
    data = {
        "symbol": "AAPL",
        "timestamp": now,
        "current_price": Decimal("150.50"),
        "technical_indicators": technical_indicators,
        "market_state": market_state,
        "latest_signal": trading_signal,
        "historical_signals": [trading_signal]
    }
    
    result = AnalysisResult(**data)
    assert result.symbol == data["symbol"]
    assert result.timestamp == data["timestamp"]
    assert result.current_price == data["current_price"]
    assert len(result.technical_indicators) == len(data["technical_indicators"])
    assert result.market_state == data["market_state"]
    assert result.latest_signal == data["latest_signal"]
    assert len(result.historical_signals) == len(data["historical_signals"])
