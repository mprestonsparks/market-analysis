from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union, Literal, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from decimal import Decimal
import math
from datetime import timezone

class TimeWindowConfig(BaseModel):
    """Configuration for time windows of different indicators"""
    rsi_window: int = Field(default=14, ge=1, description="RSI calculation window")
    macd_fast_period: int = Field(default=12, ge=1, description="MACD fast period")
    macd_slow_period: int = Field(default=26, ge=1, description="MACD slow period")
    macd_signal_period: int = Field(default=9, ge=1, description="MACD signal line period")
    stoch_k_period: int = Field(default=14, ge=1, description="Stochastic %K period")
    stoch_d_period: int = Field(default=3, ge=1, description="Stochastic %D period")
    bb_window: int = Field(default=20, ge=1, description="Bollinger Bands window")
    bb_num_std: float = Field(default=2.0, ge=0.1, description="Bollinger Bands number of standard deviations")

    @field_validator('macd_fast_period', 'macd_slow_period')
    def validate_periods(cls, v, info):
        if info.field_name == 'macd_fast_period' and 'macd_slow_period' in info.data:
            if info.data['macd_slow_period'] <= v:
                raise ValueError("MACD fast period must be less than slow period")
        return v

class StateAnalysisConfig(BaseModel):
    """Configuration for market state analysis"""
    volatility_weight: float = Field(default=1.0, ge=0.0, description="Weight of volatility in state analysis")
    trend_weight: float = Field(default=1.0, ge=0.0, description="Weight of trend strength in state analysis")
    volume_weight: float = Field(default=1.0, ge=0.0, description="Weight of volume in state analysis")
    volatility_scale: float = Field(default=0.5, ge=0.0, le=1.0, description="Scaling factor for volatility impact")
    trend_scale: float = Field(default=0.3, ge=0.0, le=1.0, description="Scaling factor for trend impact")
    volume_scale: float = Field(default=0.2, ge=0.0, le=1.0, description="Scaling factor for volume impact")

    @model_validator(mode='after')
    def validate_scales(cls, values):
        total_scale = values.volatility_scale + values.trend_scale + values.volume_scale
        if abs(total_scale - 1.0) > 0.001:
            raise ValueError("Scale factors must sum to 1.0")
        return values

class SignalGenerationConfig(BaseModel):
    """Configuration for signal generation process"""
    historical_window: int = Field(default=100, ge=1, description="Historical window for calculations")
    volume_impact: float = Field(default=0.2, ge=0.0, le=1.0, description="Volume impact on signal confidence")
    smoothing_window: int = Field(default=1, ge=1, description="Window for signal smoothing")
    combination_method: str = Field(
        default="weighted",
        description="Method to combine signals: weighted, voting, or consensus"
    )

    @field_validator('combination_method')
    def validate_method(cls, v):
        allowed_methods = {'weighted', 'voting', 'consensus'}
        if v not in allowed_methods:
            raise ValueError(f"Combination method must be one of {allowed_methods}")
        return v

class SignalThresholds(BaseModel):
    """Model for configurable signal thresholds"""
    # RSI thresholds (0-100 range)
    rsi_overbought: float = Field(default=70.0, ge=0.0, le=100.0)
    rsi_oversold: float = Field(default=30.0, ge=0.0, le=100.0)
    rsi_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    
    # MACD threshold in standard deviations (positive value)
    macd_threshold_std: float = Field(default=1.5, ge=0.0, description="MACD threshold in standard deviations")
    macd_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    
    # Stochastic thresholds (0-100 range)
    stoch_overbought: float = Field(default=80.0, ge=0.0, le=100.0)
    stoch_oversold: float = Field(default=20.0, ge=0.0, le=100.0)
    stoch_weight: float = Field(default=0.2, ge=0.0, le=1.0)
    
    # Signal generation parameters
    min_signal_strength: float = Field(default=0.1, ge=0.0, le=1.0)
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    @model_validator(mode='after')
    def validate_thresholds(cls, values):
        """Validate threshold relationships"""
        # Validate RSI thresholds relationship
        if values.rsi_oversold >= values.rsi_overbought:
            raise ValueError("RSI oversold threshold must be less than overbought threshold")
        
        # Validate Stochastic thresholds relationship
        if values.stoch_oversold >= values.stoch_overbought:
            raise ValueError("Stochastic oversold threshold must be less than overbought threshold")
        
        return values

class TechnicalIndicator(BaseModel):
    """Model for technical indicator values"""
    name: str = Field(..., min_length=1, description="Name of the technical indicator")
    value: float = Field(..., description="Current value of the indicator")
    upper_threshold: Optional[float] = Field(None, description="Upper threshold for signal generation")
    lower_threshold: Optional[float] = Field(None, description="Lower threshold for signal generation")
    signal: Optional[str] = None

    @field_validator('name')
    def validate_name(cls, v):
        """Validate indicator name is not empty"""
        if not v.strip():
            raise ValueError("Indicator name cannot be empty")
        return v

class MarketState(BaseModel):
    """Market state representation."""
    state_id: int
    description: str
    characteristics: Dict[str, float] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

class TradingSignal(BaseModel):
    """Model for trading signals"""
    timestamp: datetime = Field(..., description="Timestamp of the signal")
    signal_type: str = Field(..., description="Type of signal (BUY/SELL/HOLD)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level of the signal")
    indicators: List[str] = Field(..., min_items=1, description="Indicators contributing to the signal")
    state_context: Optional[MarketState] = Field(None, description="Market state context for the signal")

    @field_validator('signal_type')
    def validate_signal_type(cls, v):
        allowed_types = {'BUY', 'SELL', 'HOLD'}
        if v.upper() not in allowed_types:
            raise ValueError(f"Signal type must be one of {allowed_types}")
        return v.upper()

class AnalysisRequest(BaseModel):
    """Market analysis request model."""
    symbol: str = Field(..., min_length=1, description="Trading symbol (e.g., AAPL)")
    indicators: List[str] = Field(default=['RSI', 'MACD', 'BB'], description="List of technical indicators to calculate")
    state_analysis: bool = Field(default=True, description="Whether to perform state analysis")
    num_states: Optional[int] = Field(default=3, ge=1, le=10, description="Number of market states to identify")
    start_time: Optional[datetime] = Field(default=None, description="Analysis start time")
    end_time: Optional[datetime] = Field(default=None, description="Analysis end time")
    thresholds: Optional[SignalThresholds] = Field(default=None, description="Custom signal thresholds")

    @field_validator('symbol')
    def validate_symbol(cls, v):
        """Validate trading symbol is not empty"""
        if not v.strip():
            raise ValueError("Trading symbol cannot be empty")
        return v.upper()

    @field_validator('indicators')
    def validate_indicators(cls, v: List[str]) -> List[str]:
        """Validate technical indicators."""
        supported_indicators = {'RSI', 'MACD', 'STOCH', 'BB'}  # Include BB for test compatibility
        unsupported = set(v) - supported_indicators
        if unsupported:
            raise ValueError(f"Unsupported indicators: {', '.join(sorted(unsupported))}. "
                           f"Supported indicators are: {', '.join(sorted(supported_indicators))}")
        return v

    @model_validator(mode='after')
    def validate_times(cls, values):
        """Validate time range."""
        start_time = values.start_time
        end_time = values.end_time

        # If either time is not provided, skip validation
        if not start_time or not end_time:
            return values

        # Ensure both times have timezone info
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)

        if end_time <= start_time:
            raise ValueError("End time must be after start time")

        values.start_time = start_time
        values.end_time = end_time
        return values

class AnalysisResult(BaseModel):
    """Result of market analysis."""
    symbol: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_price: float = Field(..., gt=0)
    technical_indicators: List[TechnicalIndicator] = Field(default_factory=list)
    market_state: Optional[MarketState] = None
    latest_signal: Optional[TradingSignal] = None
    historical_signals: List[TradingSignal] = Field(default_factory=list)

    @field_validator('timestamp')
    def ensure_timezone(cls, v):
        """Ensure timestamp has timezone information."""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
