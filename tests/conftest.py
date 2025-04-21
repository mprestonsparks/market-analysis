"""
Test configuration and fixtures.
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from src.api.app import create_app
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np
import os

pytest_plugins = ["pytest_asyncio"]

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_client():
    """Create test client."""
    app = create_app(test_mode=True)
    with TestClient(app) as client:
        yield client

@pytest.fixture
def mock_market_data(monkeypatch):
    """Mock market data for testing."""
    def mock_fetch_data(*args, **kwargs):
        # Create sample data
        dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='D')
        data = pd.DataFrame({
            'Open': np.random.uniform(100, 200, len(dates)),
            'High': np.random.uniform(100, 200, len(dates)),
            'Low': np.random.uniform(100, 200, len(dates)),
            'Close': np.random.uniform(100, 200, len(dates)),
            'Volume': np.random.uniform(1000000, 2000000, len(dates))
        }, index=dates)
        return data
        
    # Patch the fetch_data method
    from src.api.market_analyzer import MarketAnalyzer
    monkeypatch.setattr(MarketAnalyzer, 'fetch_data', mock_fetch_data)

@pytest.fixture
def valid_analysis_request():
    """Create a valid analysis request."""
    return {
        "symbol": "AAPL",
        "indicators": ["RSI", "MACD", "BB"],
        "state_analysis": True,
        "num_states": 3,
        "start_time": datetime.now(timezone.utc).isoformat(),
        "end_time": datetime.now(timezone.utc).isoformat(),
        "thresholds": {
            "rsi_oversold": 30.0,
            "rsi_overbought": 70.0,
            "macd_buy": 0.0,
            "macd_sell": 0.0,
            "bb_buy": -2.0,
            "bb_sell": 2.0,
            "stoch_oversold": 20.0,
            "stoch_overbought": 80.0
        }
    }
