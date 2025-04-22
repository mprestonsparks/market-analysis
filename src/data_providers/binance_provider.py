"""
Binance market data provider implementation.
"""
import pandas as pd
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from binance import Client, BinanceAPIException

from .base_provider import MarketDataProvider


class BinanceProvider(MarketDataProvider):
    """Binance implementation of MarketDataProvider."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Binance provider.
        
        Args:
            config: Optional configuration dictionary containing:
                - api_key: Binance API key
                - api_secret: Binance API secret
                - testnet: Whether to use testnet (default: False)
        """
        super().__init__(config)
        self.config = config or {}
        self.client = Client(
            api_key=self.config.get('api_key'),
            api_secret=self.config.get('api_secret'),
            testnet=self.config.get('testnet', False)
        )

    async def fetch_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch historical market data from Binance.
        
        Args:
            symbol: Market symbol (e.g., 'BTCUSDT')
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with market data
            
        Raises:
            ValueError: If no data is available for the symbol
        """
        try:
            # Convert datetime to milliseconds timestamp
            start_ts = int(start_date.timestamp() * 1000)
            end_ts = int(end_date.timestamp() * 1000)

            # Fetch klines (candlestick) data
            klines = await asyncio.to_thread(
                self.client.get_historical_klines,
                symbol,
                Client.KLINE_INTERVAL_1MINUTE,
                start_ts,
                end_ts
            )

            if not klines:
                raise ValueError(f"No data available for {symbol}")

            # Convert to DataFrame with standardized column names
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            # Keep only essential columns
            essential_columns = ['open', 'high', 'low', 'close', 'volume']
            df = df[essential_columns]

            # Convert string values to float
            for col in essential_columns:
                df[col] = df[col].astype(float)

            return df

        except BinanceAPIException as e:
            raise ValueError(f"Error fetching data from Binance: {str(e)}")

    async def get_real_time_data(self, symbol: str) -> pd.DataFrame:
        """Get real-time market data from Binance.
        
        Args:
            symbol: Market symbol (e.g., 'BTCUSDT')
            
        Returns:
            DataFrame with latest market data
        """
        try:
            # Get ticker information
            ticker = await asyncio.to_thread(
                self.client.get_ticker,
                symbol=symbol
            )

            # Create DataFrame with latest data
            data = {
                'symbol': [symbol],
                'price': [float(ticker['lastPrice'])],
                'volume': [float(ticker['volume'])],
                'high': [float(ticker['highPrice'])],
                'low': [float(ticker['lowPrice'])],
                'timestamp': [pd.to_datetime(ticker['closeTime'], unit='ms')]
            }
            
            return pd.DataFrame(data)

        except BinanceAPIException as e:
            raise ValueError(f"Error fetching real-time data from Binance: {str(e)}")

    def validate_symbol(self, symbol: str) -> bool:
        """Validate if a symbol exists in Binance.
        
        Args:
            symbol: Market symbol to validate (e.g., 'BTCUSDT')
            
        Returns:
            True if symbol is valid, False otherwise
        """
        try:
            # Get exchange information
            exchange_info = self.client.get_exchange_info()
            valid_symbols = {s['symbol'] for s in exchange_info['symbols']}
            return symbol in valid_symbols
        except:
            return False

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Close any open connections
        if hasattr(self.client, 'close_connection'):
            self.client.close_connection()
