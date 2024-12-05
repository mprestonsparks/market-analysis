from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from decimal import Decimal

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
