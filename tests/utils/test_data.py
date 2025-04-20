"""Utility functions for generating test market data."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_test_market_data(symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Generate synthetic market data for testing.
    
    Args:
        symbol: Market symbol
        start_date: Start date for data generation
        end_date: End date for data generation
        
    Returns:
        DataFrame with OHLCV data
    """
    # Generate date range
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    n_points = len(date_range)
    
    # Generate synthetic price data with realistic patterns
    base_price = 100.0
    trend = np.linspace(0, 20, n_points) * np.random.choice([1, -1])
    noise = np.random.normal(0, 2, n_points)
    price = base_price + trend + noise
    
    # Generate OHLCV data
    data = pd.DataFrame({
        'Open': price + np.random.normal(0, 1, n_points),
        'High': price + abs(np.random.normal(0, 2, n_points)),
        'Low': price - abs(np.random.normal(0, 2, n_points)),
        'Close': price + np.random.normal(0, 1, n_points),
        'Volume': np.random.uniform(1000000, 5000000, n_points),
        'Dividends': np.zeros(n_points),
        'Stock Splits': np.zeros(n_points)
    }, index=date_range)
    
    # Ensure High is highest and Low is lowest
    data['High'] = data[['Open', 'High', 'Close']].max(axis=1)
    data['Low'] = data[['Open', 'Low', 'Close']].min(axis=1)
    
    return data

def get_test_market_data(symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Get test market data, either from cache or generate new.
    
    Args:
        symbol: Market symbol
        start_date: Start date
        end_date: End date
        
    Returns:
        DataFrame with OHLCV data
    """
    # For now, always generate new data
    # In the future, we could add caching if needed
    return generate_test_market_data(symbol, start_date, end_date)

VALID_TEST_SYMBOLS = {'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'BTCUSD', 'BTC-USD', 'ETHUSD', 'ETH-USD'}
