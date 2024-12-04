"""
API data models using Pydantic for request/response validation.
"""
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class MarketDataRequest(BaseModel):
    """Request model for market data analysis"""
    symbol: str = Field(..., description="Stock symbol to analyze")
    start_date: datetime = Field(..., description="Analysis start date")
    end_date: Optional[datetime] = Field(None, description="Analysis end date (defaults to current)")
    include_states: bool = Field(True, description="Include market state analysis")
    include_signals: bool = Field(True, description="Include trading signals")

class SignalResponse(BaseModel):
    """Response model for trading signals"""
    timestamp: datetime
    composite_signal: float = Field(..., ge=-1, le=1)
    confidence: float = Field(..., ge=0, le=1)
    state: int = Field(..., description="Current market state")
    
class MarketStateResponse(BaseModel):
    """Response model for market state characteristics"""
    state: int
    volatility: float
    trend_strength: float
    volume: float
    return_dispersion: float
    
class AnalysisResponse(BaseModel):
    """Complete analysis response model"""
    symbol: str
    signals: List[SignalResponse]
    states: List[MarketStateResponse]
    metadata: Dict[str, float] = Field(
        ...,
        description="Analysis metadata (performance metrics, risk measures, etc.)"
    )
