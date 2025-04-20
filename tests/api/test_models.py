"""
Tests for API models.
"""
import pytest
from datetime import datetime
from decimal import Decimal
from pydantic import ValidationError

from src.api.models.analysis import (
    TimeWindowConfig, StateAnalysisConfig, SignalGenerationConfig,
    SignalThresholds, TechnicalIndicator, MarketState, TradingSignal,
    AnalysisRequest, AnalysisResult
)

def test_time_window_config():
    """Test TimeWindowConfig model validation."""
    # Test valid configuration
    config = TimeWindowConfig(
        rsi_window=14,
        macd_fast_period=12,
        macd_slow_period=26,
        macd_signal_period=9,
        stoch_k_period=14,
        stoch_d_period=3,
        bb_window=20,
        bb_num_std=2.0
    )
    assert config.rsi_window == 14
    assert config.bb_num_std == 2.0

    # Test default values
    default_config = TimeWindowConfig()
    assert default_config.rsi_window == 14
    assert default_config.macd_fast_period == 12

    # Test invalid values
    with pytest.raises(ValidationError):
        TimeWindowConfig(rsi_window=-1)
    with pytest.raises(ValidationError):
        TimeWindowConfig(bb_num_std=0)

def test_state_analysis_config():
    """Test StateAnalysisConfig model validation."""
    # Test valid configuration
    config = StateAnalysisConfig(
        volatility_weight=1.0,
        trend_weight=1.0,
        volume_weight=1.0,
        volatility_scale=0.5,
        trend_scale=0.3,
        volume_scale=0.2
    )
    assert config.volatility_weight == 1.0
    assert config.trend_scale == 0.3

    # Test weight normalization
    total_scale = config.volatility_scale + config.trend_scale + config.volume_scale
    assert abs(total_scale - 1.0) < 0.001

    # Test invalid values
    with pytest.raises(ValidationError):
        StateAnalysisConfig(volatility_weight=-1.0)
    with pytest.raises(ValidationError):
        StateAnalysisConfig(trend_scale=1.5)

def test_signal_generation_config():
    """Test SignalGenerationConfig model validation."""
    # Test valid configuration
    config = SignalGenerationConfig(
        historical_window=100,
        volume_impact=0.2,
        smoothing_window=1,
        combination_method="weighted"
    )
    assert config.historical_window == 100
    assert config.combination_method == "weighted"

    # Test invalid values
    with pytest.raises(ValidationError):
        SignalGenerationConfig(historical_window=0)
    with pytest.raises(ValidationError):
        SignalGenerationConfig(combination_method="invalid")

def test_signal_thresholds():
    """Test SignalThresholds model validation."""
    # Test valid configuration
    config = SignalThresholds(
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
    )
    assert config.rsi_oversold == 30.0
    assert config.macd_weight == 0.4

    # Test weight normalization
    total_weight = config.rsi_weight + config.macd_weight + config.stoch_weight
    assert abs(total_weight - 1.0) < 0.001

    # Test invalid values
    with pytest.raises(ValidationError):
        SignalThresholds(rsi_oversold=80.0, rsi_overbought=20.0)
    with pytest.raises(ValidationError):
        SignalThresholds(min_confidence=1.5)

def test_technical_indicator():
    """Test TechnicalIndicator model validation."""
    # Test valid indicator
    indicator = TechnicalIndicator(
        name="RSI",
        value=65.5,
        upper_threshold=70.0,
        lower_threshold=30.0
    )
    assert indicator.name == "RSI"
    assert indicator.value == 65.5

    # Test optional thresholds
    indicator_no_thresholds = TechnicalIndicator(
        name="Custom",
        value=1.0
    )
    assert indicator_no_thresholds.upper_threshold is None

    # Test invalid values
    with pytest.raises(ValidationError):
        TechnicalIndicator(name="", value=65.5)
    with pytest.raises(ValidationError):
        TechnicalIndicator(name="RSI", value="invalid")

def test_market_state():
    """Test MarketState model validation."""
    # Test valid state
    state = MarketState(
        state_id=1,
        description="Bullish",
        characteristics={
            "volatility": 0.1,
            "trend": 0.8,
            "volume": 0.6
        },
        confidence=0.85
    )
    assert state.state_id == 1
    assert state.confidence == 0.85

    # Test optional fields
    state_minimal = MarketState(
        state_id=1,
        description="Minimal"
    )
    assert state_minimal.characteristics == {}

def test_trading_signal():
    """Test TradingSignal model validation."""
    # Test valid signal
    signal = TradingSignal(
        timestamp=datetime.now(),
        signal_type="BUY",
        confidence=0.75,
        indicators=["RSI", "MACD"]
    )
    assert signal.signal_type == "BUY"
    assert signal.confidence == 0.75

    # Test with state context
    state = MarketState(
        state_id=1,
        description="Bullish",
        characteristics={"volatility": 0.1},
        confidence=0.8
    )
    signal_with_state = TradingSignal(
        timestamp=datetime.now(),
        signal_type="BUY",
        confidence=0.75,
        indicators=["RSI"],
        state_context=state
    )
    assert signal_with_state.state_context.state_id == 1

    # Test invalid values
    with pytest.raises(ValidationError):
        TradingSignal(
            timestamp=datetime.now(),
            signal_type="INVALID",
            confidence=0.75,
            indicators=["RSI"]
        )
    with pytest.raises(ValidationError):
        TradingSignal(
            timestamp=datetime.now(),
            signal_type="BUY",
            confidence=1.5,
            indicators=["RSI"]
        )

def test_analysis_request():
    """Test AnalysisRequest model validation."""
    # Test valid request
    request = AnalysisRequest(
        symbol="AAPL",
        indicators=["RSI", "MACD"],
        state_analysis=True,
        num_states=3
    )
    assert request.symbol == "AAPL"
    assert len(request.indicators) == 2

    # Test with thresholds
    request_with_thresholds = AnalysisRequest(
        symbol="AAPL",
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
        )
    )
    assert request_with_thresholds.thresholds.rsi_oversold == 30.0

    # Test invalid values
    with pytest.raises(ValidationError):
        AnalysisRequest(symbol="")
    with pytest.raises(ValidationError):
        AnalysisRequest(symbol="AAPL", num_states=0)

def test_analysis_result():
    """Test AnalysisResult model validation."""
    # Test valid result
    result = AnalysisResult(
        symbol="AAPL",
        timestamp=datetime.now(),
        current_price=Decimal("150.25"),
        technical_indicators=[
            TechnicalIndicator(
                name="RSI",
                value=65.5,
                upper_threshold=70.0,
                lower_threshold=30.0
            )
        ],
        market_state=MarketState(
            state_id=1,
            description="Bullish",
            characteristics={"volatility": 0.1},
            confidence=0.8
        ),
        latest_signal=TradingSignal(
            timestamp=datetime.now(),
            signal_type="BUY",
            confidence=0.75,
            indicators=["RSI"]
        ),
        historical_signals=[]
    )
    assert result.symbol == "AAPL"
    assert len(result.technical_indicators) == 1
    assert result.market_state.state_id == 1

    # Test invalid values
    with pytest.raises(ValidationError):
        AnalysisResult(
            symbol="AAPL",
            timestamp=datetime.now(),
            current_price=Decimal("-1.0"),
            technical_indicators=[]
        )
