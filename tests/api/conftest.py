"""
Test fixtures for the Market Analysis API.
"""
import pytest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from decimal import Decimal
from src.api.models import (
    TimeWindowConfig, StateAnalysisConfig, SignalGenerationConfig,
    SignalThresholds, TechnicalIndicator, MarketState, TradingSignal,
    AnalysisRequest, AnalysisResult
)

@pytest.fixture
def mock_market_data():
    """Mock market data for testing."""
    dates = pd.date_range(start='2024-01-01', end='2024-01-30', freq='D')
    data = pd.DataFrame({
        'Close': np.random.uniform(100, 200, len(dates)),
        'Open': np.random.uniform(100, 200, len(dates)),
        'High': np.random.uniform(100, 200, len(dates)),
        'Low': np.random.uniform(100, 200, len(dates)),
        'Volume': np.random.uniform(1000000, 2000000, len(dates))
    }, index=dates)
    return data

@pytest.fixture
def mock_technical_indicators():
    """Mock technical indicators for testing."""
    return {
        'rsi': pd.Series([65.5] * 30),
        'macd': pd.Series([0.5] * 30),
        'macd_signal': pd.Series([0.2] * 30),
        'macd_hist': pd.Series([0.3] * 30),
        'bb_middle': pd.Series([155.0] * 30),
        'bb_upper': pd.Series([160.0] * 30),
        'bb_lower': pd.Series([150.0] * 30)
    }

@pytest.fixture
def mock_market_analyzer(mock_market_data, mock_technical_indicators):
    """Mock MarketAnalyzer for testing."""
    with patch('src.market_analysis.MarketAnalyzer') as MockAnalyzer:
        instance = MockAnalyzer.return_value
        instance.data = mock_market_data
        instance.technical_indicators = mock_technical_indicators
        instance.current_state = 1
        instance.state_description = "Bullish Trend"
        instance.state_characteristics = {
            1: {
                'volatility': 0.15,
                'trend_strength': 0.8,
                'volume': 0.6,
                'return_dispersion': 0.05
            }
        }
        instance.fetch_data.return_value = mock_market_data
        yield instance

@pytest.fixture
def valid_analysis_request():
    """Valid analysis request fixture."""
    return AnalysisRequest(
        symbol="AAPL",
        indicators=["RSI", "MACD", "BB"],
        state_analysis=True,
        num_states=3,
        thresholds=SignalThresholds(
            rsi_oversold=30.0,
            rsi_overbought=70.0,
            rsi_weight=0.4,
            macd_threshold_std=1.5,
            macd_weight=0.4,
            stoch_oversold=20.0,
            stoch_overbought=80.0,
            stoch_weight=0.2,
            min_signal_strength=0.1,
            min_confidence=0.5
        ),
        start_time=(datetime.now() - timedelta(days=7)).isoformat(),
        end_time=datetime.now().isoformat()
    )

@pytest.fixture
def mock_market_state():
    """Mock market state for testing."""
    return MarketState(
        state_id=1,
        description="Bullish Trend",
        characteristics={
            "volatility": 0.15,
            "trend": 0.8,
            "volume": 0.6
        },
        confidence=0.85
    )

@pytest.fixture
def mock_trading_signal():
    """Mock trading signal for testing."""
    return TradingSignal(
        timestamp=datetime.now(),
        signal_type="BUY",
        confidence=0.75,
        indicators=["RSI", "MACD"],
        state_context=MarketState(
            state_id=1,
            description="Bullish",
            characteristics={"volatility": 0.1},
            confidence=0.8
        )
    )

@pytest.fixture
def mock_analysis_result(mock_technical_indicators, mock_market_state, mock_trading_signal):
    """Mock analysis result for testing."""
    return AnalysisResult(
        symbol="AAPL",
        timestamp=datetime.now(),
        current_price=Decimal("150.25"),
        technical_indicators=[
            TechnicalIndicator(name="RSI", value=65.5),
            TechnicalIndicator(name="MACD", value=0.5),
            TechnicalIndicator(name="BB", value=155.0)
        ],
        market_state=mock_market_state,
        latest_signal=mock_trading_signal,
        historical_signals=[mock_trading_signal]
    )
