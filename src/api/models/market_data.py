from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, validator, ValidationInfo


class MarketData(BaseModel):
    """Base model for market data."""
    symbol: str = Field(..., description="Trading symbol (e.g. 'BTC-USD')")
    timestamp: datetime = Field(..., description="Timestamp of the market data point")
    open: Decimal = Field(..., description="Opening price of the period", gt=0)
    high: Decimal = Field(..., description="Highest price in the period", gt=0)
    low: Decimal = Field(..., description="Lowest price in the period", gt=0)
    close: Decimal = Field(..., description="Closing price of the period", gt=0)
    volume: Decimal = Field(..., description="Trading volume", ge=0)
    adjusted_close: Optional[Decimal] = Field(None, description="Adjusted closing price", gt=0)

    @validator('symbol')
    def validate_symbol(cls, v: str) -> str:
        """Validate and normalize the trading symbol."""
        return v.upper().strip()

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC-USD",
                "timestamp": "2024-01-20T12:00:00Z",
                "open": "41950.00",
                "high": "42100.00",
                "low": "41900.00",
                "close": "42000.50",
                "volume": "100.5",
                "adjusted_close": "42000.50"
            }
        }


class MarketDataRequest(BaseModel):
    """Model for market data retrieval requests."""
    symbol: str = Field(..., description="Trading symbol to fetch data for")
    start_time: Optional[datetime] = Field(None, description="Start time for historical data")
    end_time: Optional[datetime] = Field(None, description="End time for historical data")
    interval: str = Field(
        "1d",
        description="Data interval (e.g., '1m', '5m', '1h', '1d')",
        pattern="^[1-9][0-9]?[mhd]$"
    )
    limit: Optional[int] = Field(
        100,
        description="Maximum number of data points to return",
        ge=1,
        le=1000
    )
    include_adjusted: bool = Field(
        True,
        description="Whether to include adjusted prices"
    )

    @validator('symbol')
    def validate_symbol(cls, v: str) -> str:
        """Validate and normalize the trading symbol."""
        return v.upper().strip()

    @validator('end_time')
    def validate_time_range(cls, v: Optional[datetime], values: dict, **kwargs) -> Optional[datetime]:
        """Validate that end_time is after start_time if both are provided."""
        if v and values.get('start_time') and v <= values['start_time']:
            raise ValueError("end_time must be after start_time")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC-USD",
                "start_time": "2024-01-20T00:00:00Z",
                "end_time": "2024-01-20T12:00:00Z",
                "interval": "1h",
                "limit": 100,
                "include_adjusted": True
            }
        }


class MarketDataResponse(BaseModel):
    """Model for market data response."""
    symbol: str = Field(..., description="Trading symbol")
    interval: str = Field(..., description="Data interval")
    start_time: datetime = Field(..., description="Start time of the data")
    end_time: datetime = Field(..., description="End time of the data")
    data: List[MarketData] = Field(..., description="List of market data points")
    rate_limit_remaining: Optional[int] = Field(
        None,
        description="Remaining API rate limit"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC-USD",
                "interval": "1h",
                "start_time": "2024-01-20T00:00:00Z",
                "end_time": "2024-01-20T12:00:00Z",
                "data": [
                    {
                        "symbol": "BTC-USD",
                        "timestamp": "2024-01-20T00:00:00Z",
                        "open": "41950.00",
                        "high": "42100.00",
                        "low": "41900.00",
                        "close": "42000.50",
                        "volume": "100.5",
                        "adjusted_close": "42000.50"
                    }
                ],
                "rate_limit_remaining": 45
            }
        }
