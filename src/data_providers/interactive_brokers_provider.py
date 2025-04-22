"""
Interactive Brokers market data provider implementation.
"""
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any

from .base_provider import MarketDataProvider


class InteractiveBrokersProvider(MarketDataProvider):
    """Interactive Brokers implementation of MarketDataProvider."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Interactive Brokers provider.
        
        Args:
            config: Optional configuration dictionary containing:
                - host: TWS/IB Gateway host (default: localhost)
                - port: TWS/IB Gateway port (default: 7496)
                - client_id: Client ID for IB connection
        """
        super().__init__(config)
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 7496)
        self.client_id = config.get('client_id', 1)
        self.connection = None  # Will be initialized when needed

    async def _ensure_connection(self):
        """Ensure we have an active connection to Interactive Brokers."""
        if not self.connection or not self.connection.isConnected():
            # Import here to avoid loading IB dependencies unless needed
            from ib_insync import IB
            self.connection = IB()
            await self.connection.connectAsync(
                host=self.host,
                port=self.port,
                clientId=self.client_id
            )

    async def fetch_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch historical market data from Interactive Brokers (async)."""
        await self._ensure_connection()
        from ib_insync import Contract, util
        contract = Contract()
        contract.symbol = symbol
        contract.secType = 'STK'
        contract.exchange = 'SMART'
        contract.currency = 'USD'
        bars = await self.connection.reqHistoricalDataAsync(
            contract,
            endDateTime=end_date,
            durationStr=f"{(end_date - start_date).days + 1} D",
            barSizeSetting='1 min',
            whatToShow='TRADES',
            useRTH=True
        )
        df = util.df(bars)
        if df.empty:
            raise ValueError(f"No data available for {symbol}")
        df.columns = [col.lower() for col in df.columns]
        return df

    def fetch_data_sync(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Synchronous wrapper for fetch_data (for CLI/DAG/Operator use).
        Calls async fetch_data using asyncio.run if not already in an event loop.
        """
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            # In an event loop: run as task
            return loop.run_until_complete(self.fetch_data(symbol, start_date, end_date))
        else:
            return asyncio.run(self.fetch_data(symbol, start_date, end_date))

    async def get_real_time_data(self, symbol: str) -> pd.DataFrame:
        """Get real-time market data from Interactive Brokers.
        
        Args:
            symbol: Market symbol
            
        Returns:
            DataFrame with latest market data
        """
        await self._ensure_connection()
        
        from ib_insync import Contract
        
        # Create contract
        contract = Contract()
        contract.symbol = symbol
        contract.secType = 'STK'
        contract.exchange = 'SMART'
        contract.currency = 'USD'
        
        # Request market data
        self.connection.reqMktData(contract)
        await asyncio.sleep(1)  # Wait for data to arrive
        
        # Get the latest tick data
        ticker = self.connection.ticker(contract)
        
        # Convert to DataFrame
        data = {
            'symbol': [symbol],
            'last': [ticker.last],
            'bid': [ticker.bid],
            'ask': [ticker.ask],
            'high': [ticker.high],
            'low': [ticker.low],
            'volume': [ticker.volume],
            'timestamp': [datetime.now()]
        }
        return pd.DataFrame(data)

    def validate_symbol(self, symbol: str) -> bool:
        """Validate if a symbol exists in Interactive Brokers.
        
        Args:
            symbol: Market symbol to validate
            
        Returns:
            True if symbol is valid, False otherwise
        """
        try:
            from ib_insync import Contract
            
            contract = Contract()
            contract.symbol = symbol
            contract.secType = 'STK'
            contract.exchange = 'SMART'
            contract.currency = 'USD'
            
            # Try to resolve the contract
            qualified_contracts = self.connection.reqMatchingSymbols(symbol)
            return any(c.contract.symbol == symbol for c in qualified_contracts)
        except:
            return False

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_connection()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.connection:
            self.connection.disconnect()
