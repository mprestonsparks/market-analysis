from datetime import datetime
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field
from decimal import Decimal

class TimeWindowConfig(BaseModel):
    """Configuration for time windows of different indicators"""
    rsi_window: int = Field(default=14, description="RSI calculation window")
    macd_fast_period: int = Field(default=12, description="MACD fast period")
    macd_slow_period: int = Field(default=26, description="MACD slow period")
    macd_signal_period: int = Field(default=9, description="MACD signal line period")
    stoch_k_period: int = Field(default=14, description="Stochastic %K period")
    stoch_d_period: int = Field(default=3, description="Stochastic %D period")
    bb_window: int = Field(default=20, description="Bollinger Bands window")
    bb_num_std: float = Field(default=2.0, description="Bollinger Bands number of standard deviations")

class StateAnalysisConfig(BaseModel):
    """Configuration for market state analysis"""
    volatility_weight: float = Field(default=1.0, description="Weight of volatility in state analysis")
    trend_weight: float = Field(default=1.0, description="Weight of trend strength in state analysis")
    volume_weight: float = Field(default=1.0, description="Weight of volume in state analysis")
    volatility_scale: float = Field(default=0.5, description="Scaling factor for volatility impact")
    trend_scale: float = Field(default=0.3, description="Scaling factor for trend impact")
    volume_scale: float = Field(default=0.2, description="Scaling factor for volume impact")

class SignalGenerationConfig(BaseModel):
    """Configuration for signal generation process"""
    historical_window: int = Field(default=100, description="Historical window for calculations")
    volume_impact: float = Field(default=0.2, description="Volume impact on signal confidence")
    smoothing_window: int = Field(default=1, description="Window for signal smoothing")
    combination_method: str = Field(default="weighted", description="Method to combine signals: weighted, voting, or consensus")

class SignalThresholds(BaseModel):
    """Configuration for signal generation thresholds"""
    # Basic thresholds
    rsi_oversold: float = Field(default=30.0, description="RSI oversold threshold")
    rsi_overbought: float = Field(default=70.0, description="RSI overbought threshold")
    rsi_weight: float = Field(default=0.4, description="Weight of RSI in composite signal")
    
    macd_threshold_std: float = Field(default=1.5, description="MACD threshold in standard deviations")
    macd_weight: float = Field(default=0.4, description="Weight of MACD in composite signal")
    
    stoch_oversold: float = Field(default=20.0, description="Stochastic oversold threshold")
    stoch_overbought: float = Field(default=80.0, description="Stochastic overbought threshold")
    stoch_weight: float = Field(default=0.2, description="Weight of Stochastic in composite signal")
    
    min_signal_strength: float = Field(default=0.1, description="Minimum signal strength to generate a signal")
    min_confidence: float = Field(default=0.5, description="Minimum confidence level for signals")
    
    # Additional configuration
    time_windows: Optional[TimeWindowConfig] = Field(None, description="Time window configurations")
    state_analysis: Optional[StateAnalysisConfig] = Field(None, description="State analysis configurations")
    signal_generation: Optional[SignalGenerationConfig] = Field(None, description="Signal generation configurations")

class TechnicalIndicator(BaseModel):
    """Model for technical indicator values."""
    name: str = Field(..., description="Name of the technical indicator")
    value: float = Field(..., description="Current value of the indicator")
    upper_threshold: Optional[float] = Field(None, description="Upper threshold for signal generation")
    lower_threshold: Optional[float] = Field(None, description="Lower threshold for signal generation")

class MarketState(BaseModel):
    """Model for market state information."""
    state_id: int = Field(..., description="Identifier for the market state")
    description: str = Field(..., description="Description of the market state")
    characteristics: Dict[str, float] = Field(
        default_factory=dict,
        description="Key characteristics of the state"
    )
    confidence: float = Field(
        ..., 
        ge=0, 
        le=1, 
        description="Confidence level of state identification"
    )

class TradingSignal(BaseModel):
    """Model for trading signals."""
    timestamp: datetime = Field(..., description="Timestamp of the signal")
    signal_type: str = Field(..., description="Type of signal (buy/sell/hold)")
    confidence: float = Field(..., ge=0, le=1, description="Confidence level of the signal")
    indicators: List[str] = Field(..., description="Indicators contributing to the signal")
    state_context: Optional[MarketState] = Field(None, description="Market state context for the signal")

class AnalysisRequest(BaseModel):
    """Model for market analysis request."""
    symbol: str = Field(..., description="Trading symbol to analyze")
    start_time: Optional[datetime] = Field(None, description="Start time for analysis")
    end_time: Optional[datetime] = Field(None, description="End time for analysis")
    indicators: List[str] = Field(
        default=["RSI", "MACD", "BB"],
        description="List of technical indicators to include"
    )
    state_analysis: bool = Field(
        default=True,
        description="Whether to perform market state analysis"
    )
    num_states: int = Field(
        default=3,
        description="Number of market states to identify",
        ge=2,
        le=5
    )
    thresholds: Optional[SignalThresholds] = Field(None, description="Signal generation thresholds")

class AnalysisResult(BaseModel):
    """Model for market analysis results."""
    symbol: str = Field(..., description="Trading symbol analyzed")
    timestamp: datetime = Field(..., description="Timestamp of analysis")
    current_price: Decimal = Field(..., description="Current price of the asset")
    technical_indicators: List[TechnicalIndicator] = Field(..., description="Current technical indicator values")
    market_state: Optional[MarketState] = Field(None, description="Current market state")
    latest_signal: Optional[TradingSignal] = Field(None, description="Latest trading signal")
    historical_signals: List[TradingSignal] = Field(
        default_factory=list,
        description="Historical trading signals"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC-USD",
                "timestamp": "2024-01-20T12:00:00Z",
                "current_price": "42000.50",
                "technical_indicators": [
                    {
                        "name": "RSI",
                        "value": 65.5,
                        "upper_threshold": 70,
                        "lower_threshold": 30
                    }
                ],
                "market_state": {
                    "state_id": 1,
                    "description": "Bullish Trend",
                    "characteristics": {
                        "volatility": 0.15,
                        "trend_strength": 0.8
                    },
                    "confidence": 0.85
                },
                "latest_signal": {
                    "timestamp": "2024-01-20T12:00:00Z",
                    "signal_type": "buy",
                    "confidence": 0.75,
                    "indicators": ["RSI", "MACD"],
                    "state_context": {
                        "state_id": 1,
                        "description": "Bullish Trend",
                        "characteristics": {
                            "volatility": 0.15,
                            "trend_strength": 0.8
                        },
                        "confidence": 0.85
                    }
                },
                "historical_signals": []
            }
        }
