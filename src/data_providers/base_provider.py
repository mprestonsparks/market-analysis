"""
Base class for market data providers.
"""
from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd
from typing import Optional, Dict, Any


class MarketDataProvider(ABC):
    """Abstract base class for market data providers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the data provider.
        
        Args:
            config: Optional configuration dictionary for the provider
        """
        self.config = config or {}

    @abstractmethod
    async def fetch_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch market data for a given symbol.
        
        Args:
            symbol: Market symbol
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with market data containing at least these columns:
            - open: Opening price
            - high: High price
            - low: Low price
            - close: Closing price
            - volume: Trading volume
        """
        pass

    @abstractmethod
    async def get_real_time_data(self, symbol: str) -> pd.DataFrame:
        """Get real-time market data for a symbol.
        
        Args:
            symbol: Market symbol
            
        Returns:
            DataFrame with latest market data
        """
        pass

    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """Validate if a symbol is supported by this provider.
        
        Args:
            symbol: Market symbol to validate
            
        Returns:
            True if symbol is valid, False otherwise
        """
        pass
