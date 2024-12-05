from datetime import datetime, timezone
from decimal import Decimal
import pytest
from pydantic import ValidationError

from src.api.models.analysis import (
    TechnicalIndicator,
    MarketState,
    IndicatorValue,
    CompositeSignal,
    AnalysisRequest,
    AnalysisResult
)


def test_indicator_value_valid():
    """Test creating a valid IndicatorValue instance."""
    data = {
        "name": TechnicalIndicator.RSI,
        "value": 65.5,
        "upper_band": 70.0,
        "lower_band": 30.0,
        "configuration": {
            "period": 14,
            "weight": 0.4,
            "threshold_percentile": 80
        }
    }
    indicator = IndicatorValue(**data)
    assert indicator.name == TechnicalIndicator.RSI
    assert indicator.value == 65.5
    assert indicator.upper_band == 70.0
    assert indicator.lower_band == 30.0


def test_market_state_valid():
    """Test creating a valid MarketState instance."""
    data = {
        "state_id": 1,
        "description": "Low volatility uptrend",
        "characteristics": {
            "volatility": 0.2,
            "trend": 0.8
        }
    }
    state = MarketState(**data)
    assert state.state_id == 1
    assert state.description == "Low volatility uptrend"
    assert state.characteristics["volatility"] == 0.2


def test_composite_signal_valid():
    """Test creating a valid CompositeSignal instance."""
    data = {
        "timestamp": datetime.now(timezone.utc),
        "value": 0.75,
        "confidence": 0.85,
        "volume_scale": 1.2,
        "component_signals": {
            TechnicalIndicator.RSI: 0.8,
            TechnicalIndicator.MACD: 0.7,
            TechnicalIndicator.STOCHASTIC: 0.75
        },
        "market_state": {
            "state_id": 1,
            "description": "Low volatility uptrend",
            "characteristics": {
                "volatility": 0.2,
                "trend": 0.8
            }
        }
    }
    signal = CompositeSignal(**data)
    assert signal.value == 0.75
    assert signal.confidence == 0.85
    assert signal.volume_scale == 1.2


def test_composite_signal_invalid_value():
    """Test that invalid signal values are rejected."""
    data = {
        "timestamp": datetime.now(timezone.utc),
        "value": 1.5,  # Should be <= 1
        "confidence": 0.85,
        "volume_scale": 1.2,
        "component_signals": {
            TechnicalIndicator.RSI: 0.8
        },
        "market_state": {
            "state_id": 1,
            "description": "Low volatility uptrend",
            "characteristics": {
                "volatility": 0.2,
                "trend": 0.8
            }
        }
    }
    with pytest.raises(ValidationError):
        CompositeSignal(**data)


def test_analysis_request_valid():
    """Test creating a valid AnalysisRequest instance."""
    data = {
        "symbol": "BTC-USD",
        "indicators": [TechnicalIndicator.RSI, TechnicalIndicator.MACD],
        "start_time": datetime.now(timezone.utc),
        "end_time": datetime.now(timezone.utc),
        "state_analysis": True,
        "num_states": 3
    }
    request = AnalysisRequest(**data)
    assert request.symbol == "BTC-USD"
    assert len(request.indicators) == 2
    assert request.num_states == 3


def test_analysis_request_default_indicators():
    """Test that empty indicators list uses all indicators."""
    data = {
        "symbol": "BTC-USD",
        "indicators": []
    }
    request = AnalysisRequest(**data)
    assert len(request.indicators) == len(TechnicalIndicator)


def test_analysis_result_valid():
    """Test creating a valid AnalysisResult instance."""
    data = {
        "symbol": "BTC-USD",
        "timestamp": datetime.now(timezone.utc),
        "market_state": {
            "state_id": 1,
            "description": "Low volatility uptrend",
            "characteristics": {
                "volatility": 0.2,
                "trend": 0.8
            }
        },
        "indicators": {
            TechnicalIndicator.RSI: {
                "name": TechnicalIndicator.RSI,
                "value": 65.5,
                "upper_band": 70.0,
                "lower_band": 30.0,
                "configuration": {
                    "period": 14,
                    "weight": 0.4,
                    "threshold_percentile": 80
                }
            }
        },
        "signals": [],
        "configuration": {
            "rsi": {
                "period": 14,
                "weight": 0.4,
                "threshold_percentile": 80
            }
        }
    }
    result = AnalysisResult(**data)
    assert result.symbol == "BTC-USD"
    assert len(result.indicators) == 1
    assert TechnicalIndicator.RSI in result.indicators
