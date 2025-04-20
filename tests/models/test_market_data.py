from datetime import datetime, timezone
from decimal import Decimal
import pytest
from pydantic import ValidationError

from src.api.models.market_data import MarketData, MarketDataRequest, MarketDataResponse


def test_market_data_valid():
    """Test creating a valid MarketData instance."""
    data = {
        "symbol": "BTC-USD",
        "timestamp": datetime.now(timezone.utc),
        "open": Decimal("41950.00"),
        "high": Decimal("42100.00"),
        "low": Decimal("41900.00"),
        "close": Decimal("42000.50"),
        "volume": Decimal("100.5"),
        "adjusted_close": Decimal("42000.50")
    }
    market_data = MarketData(**data)
    assert market_data.symbol == "BTC-USD"
    assert isinstance(market_data.open, Decimal)
    assert market_data.close == Decimal("42000.50")


def test_market_data_symbol_normalization():
    """Test that symbols are normalized to uppercase."""
    data = {
        "symbol": "btc-usd",
        "timestamp": datetime.now(timezone.utc),
        "open": Decimal("41950.00"),
        "high": Decimal("42100.00"),
        "low": Decimal("41900.00"),
        "close": Decimal("42000.50"),
        "volume": Decimal("100.5")
    }
    market_data = MarketData(**data)
    assert market_data.symbol == "BTC-USD"


def test_market_data_invalid_price():
    """Test that negative prices are rejected."""
    data = {
        "symbol": "BTC-USD",
        "timestamp": datetime.now(timezone.utc),
        "open": Decimal("-41950.00"),
        "high": Decimal("42100.00"),
        "low": Decimal("41900.00"),
        "close": Decimal("42000.50"),
        "volume": Decimal("100.5")
    }
    with pytest.raises(ValidationError):
        MarketData(**data)


def test_market_data_invalid_volume():
    """Test that negative volume is rejected."""
    data = {
        "symbol": "BTC-USD",
        "timestamp": datetime.now(timezone.utc),
        "open": Decimal("41950.00"),
        "high": Decimal("42100.00"),
        "low": Decimal("41900.00"),
        "close": Decimal("42000.50"),
        "volume": Decimal("-100.5")
    }
    with pytest.raises(ValidationError):
        MarketData(**data)


def test_market_data_request_valid():
    """Test creating a valid MarketDataRequest instance."""
    data = {
        "symbol": "BTC-USD",
        "start_time": datetime.now(timezone.utc),
        "end_time": datetime.now(timezone.utc),
        "interval": "1h",
        "limit": 100,
        "include_adjusted": True
    }
    request = MarketDataRequest(**data)
    assert request.symbol == "BTC-USD"
    assert request.interval == "1h"
    assert request.limit == 100


def test_market_data_request_invalid_interval():
    """Test that invalid intervals are rejected."""
    data = {
        "symbol": "BTC-USD",
        "interval": "invalid"  # Should match pattern
    }
    with pytest.raises(ValidationError):
        MarketDataRequest(**data)


def test_market_data_request_invalid_time_range():
    """Test that end_time before start_time is rejected."""
    end_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    start_time = datetime(2024, 1, 2, tzinfo=timezone.utc)
    data = {
        "symbol": "BTC-USD",
        "start_time": start_time,
        "end_time": end_time,
        "interval": "1d"
    }
    with pytest.raises(ValidationError):
        MarketDataRequest(**data)


def test_market_data_request_invalid_limit():
    """Test that invalid limits are rejected."""
    data = {
        "symbol": "BTC-USD",
        "limit": 0  # Should be >= 1
    }
    with pytest.raises(ValidationError):
        MarketDataRequest(**data)

    data["limit"] = 1001  # Should be <= 1000
    with pytest.raises(ValidationError):
        MarketDataRequest(**data)


def test_market_data_response_valid():
    """Test creating a valid MarketDataResponse instance."""
    data = {
        "symbol": "BTC-USD",
        "interval": "1h",
        "start_time": datetime.now(timezone.utc),
        "end_time": datetime.now(timezone.utc),
        "data": [
            {
                "symbol": "BTC-USD",
                "timestamp": datetime.now(timezone.utc),
                "open": Decimal("41950.00"),
                "high": Decimal("42100.00"),
                "low": Decimal("41900.00"),
                "close": Decimal("42000.50"),
                "volume": Decimal("100.5"),
                "adjusted_close": Decimal("42000.50")
            }
        ],
        "rate_limit_remaining": 45
    }
    response = MarketDataResponse(**data)
    assert response.symbol == "BTC-USD"
    assert response.interval == "1h"
    assert len(response.data) == 1
    assert response.rate_limit_remaining == 45
