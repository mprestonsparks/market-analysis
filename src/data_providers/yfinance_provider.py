"""
YFinance market data provider implementation.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime
from ratelimit import limits, sleep_and_retry
from typing import Optional, Dict, Any

from .base_provider import MarketDataProvider
from ..config.rate_limits import get_rate_limit_config


class YFinanceProvider(MarketDataProvider):
    """YFinance implementation of MarketDataProvider."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize YFinance provider.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.rate_limit_config = get_rate_limit_config('yfinance')

    @sleep_and_retry
    @limits(calls=lambda self: self.rate_limit_config['CALLS_PER_HOUR'], 
            period=lambda self: self.rate_limit_config['PERIOD'])
    async def fetch_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch historical market data using YFinance.
        
        Args:
            symbol: Market symbol
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with market data
        
        Raises:
            ValueError: If no data is available for the symbol
        """
        for attempt in range(self.rate_limit_config['MAX_RETRIES']):
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date, end=end_date)
                if data.empty:
                    raise ValueError(f"No data available for {symbol} in the specified time range")
                
                # Standardize column names to lowercase
                data.columns = [col.lower() for col in data.columns]
                return data
                
            except Exception as e:
                if attempt == self.rate_limit_config['MAX_RETRIES'] - 1:
                    raise e
                wait_time = (2 ** attempt) * self.rate_limit_config['BASE_WAIT_TIME']
                await asyncio.sleep(wait_time)

    async def get_real_time_data(self, symbol: str) -> pd.DataFrame:
        """Get real-time market data using YFinance.
        Note: YFinance doesn't provide true real-time data, this is delayed.
        
        Args:
            symbol: Market symbol
            
        Returns:
            DataFrame with latest market data
        """
        ticker = yf.Ticker(symbol)
        data = ticker.history(period='1d', interval='1m')
        if data.empty:
            raise ValueError(f"No real-time data available for {symbol}")
        
        # Standardize column names to lowercase
        data.columns = [col.lower() for col in data.columns]
        return data

    def validate_symbol(self, symbol: str) -> bool:
        """Validate if a symbol exists in YFinance.
        
        Args:
            symbol: Market symbol to validate
            
        Returns:
            True if symbol is valid, False otherwise
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return bool(info and 'symbol' in info)
        except:
            return False
