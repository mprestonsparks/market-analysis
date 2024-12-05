from datetime import datetime
from typing import List, Dict, Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from decimal import Decimal

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

    @model_validator(mode='after')
    def validate_periods(cls, values):
        if values.macd_fast_period >= values.macd_slow_period:
            raise ValueError("MACD fast period must be less than slow period")
        return values

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
    @classmethod
    def validate_method(cls, v):
        allowed_methods = {'weighted', 'voting', 'consensus'}
        if v not in allowed_methods:
            raise ValueError(f"Combination method must be one of {allowed_methods}")
        return v

class SignalThresholds(BaseModel):
    """Configuration for signal generation thresholds"""
    rsi_oversold: float = Field(default=30.0, ge=0.0, le=100.0, description="RSI oversold threshold")
    rsi_overbought: float = Field(default=70.0, ge=0.0, le=100.0, description="RSI overbought threshold")
    rsi_weight: float = Field(default=0.4, ge=0.0, le=1.0, description="Weight of RSI in composite signal")
    macd_threshold_std: float = Field(default=1.5, ge=0.0, description="MACD threshold in standard deviations")
    macd_weight: float = Field(default=0.4, ge=0.0, le=1.0, description="Weight of MACD in composite signal")
    stoch_oversold: float = Field(default=20.0, ge=0.0, le=100.0, description="Stochastic oversold threshold")
    stoch_overbought: float = Field(default=80.0, ge=0.0, le=100.0, description="Stochastic overbought threshold")
    stoch_weight: float = Field(default=0.2, ge=0.0, le=1.0, description="Weight of Stochastic in composite signal")
    min_signal_strength: float = Field(default=0.1, ge=0.0, le=1.0, description="Minimum signal strength threshold")
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum confidence threshold")

    @model_validator(mode='after')
    def validate_thresholds(cls, values):
        if values.rsi_oversold >= values.rsi_overbought:
            raise ValueError("RSI oversold must be less than overbought threshold")
        if values.stoch_oversold >= values.stoch_overbought:
            raise ValueError("Stochastic oversold must be less than overbought threshold")
        total_weight = values.rsi_weight + values.macd_weight + values.stoch_weight
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError("Weights must sum to 1.0")
        return values

class TechnicalIndicator(BaseModel):
    """Model for technical indicator values"""
    name: str = Field(..., min_length=1, description="Name of the technical indicator")
    value: float = Field(..., description="Current value of the indicator")
    upper_threshold: Optional[float] = Field(None, description="Upper threshold for signal generation")
    lower_threshold: Optional[float] = Field(None, description="Lower threshold for signal generation")

class MarketState(BaseModel):
    """Model for market state information"""
    state_id: int = Field(..., ge=1, description="Identifier for the market state")
    description: str = Field(..., min_length=1, description="Description of the market state")
    characteristics: Dict[str, float] = Field(
        default_factory=dict,
        description="Key characteristics of the state"
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Confidence level of state identification"
    )

class TradingSignal(BaseModel):
    """Model for trading signals"""
    timestamp: datetime = Field(..., description="Timestamp of the signal")
    signal_type: str = Field(..., description="Type of signal (buy/sell/hold)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level of the signal")
    indicators: List[str] = Field(..., min_length=1, description="Indicators contributing to the signal")
    state_context: Optional[MarketState] = Field(None, description="Market state context for the signal")

    @field_validator('signal_type')
    @classmethod
    def validate_signal_type(cls, v):
        allowed_types = {'BUY', 'SELL', 'HOLD'}
        if v.upper() not in allowed_types:
            raise ValueError(f"Signal type must be one of {allowed_types}")
        return v.upper()

class AnalysisRequest(BaseModel):
    """Model for market analysis request"""
    symbol: str = Field(..., min_length=1, description="Trading symbol to analyze")
    start_time: Optional[datetime] = Field(None, description="Start time for analysis")
    end_time: Optional[datetime] = Field(None, description="End time for analysis")
    indicators: List[str] = Field(
        default=["RSI", "MACD", "BB"],
        min_length=1,
        description="List of technical indicators to include"
    )
    state_analysis: bool = Field(
        default=True,
        description="Whether to perform market state analysis"
    )
    num_states: int = Field(
        default=3,
        ge=2,
        le=5,
        description="Number of market states to identify"
    )
    thresholds: Optional[SignalThresholds] = Field(None, description="Signal generation thresholds")

    @field_validator('indicators')
    @classmethod
    def validate_indicators(cls, v):
        allowed_indicators = {'RSI', 'MACD', 'BB', 'STOCH'}
        invalid_indicators = [ind for ind in v if ind.upper() not in allowed_indicators]
        if invalid_indicators:
            raise ValueError(f"Invalid indicators: {invalid_indicators}. Must be one of {allowed_indicators}")
        return [ind.upper() for ind in v]

    @model_validator(mode='after')
    def validate_dates(cls, values):
        if values.start_time and values.end_time and values.start_time >= values.end_time:
            raise ValueError("Start time must be before end time")
        return values

class AnalysisResult(BaseModel):
    """Model for market analysis results"""
    symbol: str = Field(..., min_length=1, description="Trading symbol analyzed")
    timestamp: datetime = Field(..., description="Timestamp of analysis")
    current_price: Decimal = Field(..., gt=Decimal('0'), description="Current price of the asset")
    technical_indicators: List[TechnicalIndicator] = Field(..., min_length=1, description="Current technical indicator values")
    market_state: Optional[MarketState] = Field(None, description="Current market state")
    latest_signal: Optional[TradingSignal] = Field(None, description="Latest trading signal")
    historical_signals: List[TradingSignal] = Field(
        default_factory=list,
        description="Historical trading signals"
    )
