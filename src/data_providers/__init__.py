"""
Market data providers package.
"""
from .base_provider import MarketDataProvider
from .yfinance_provider import YFinanceProvider
from .interactive_brokers_provider import InteractiveBrokersProvider
from .binance_provider import BinanceProvider
import os

import json

def provider_factory(provider: str = None, config: dict = None) -> MarketDataProvider:
    """
    Factory function to return a MarketDataProvider instance based on provider name or env.
    Tries to load config from Airflow connection extras if running in Airflow.
    Args:
        provider: 'yfinance', 'ibkr', or 'binance'. If None, uses PROVIDER env var or defaults to 'yfinance'.
        config: Optional configuration dictionary for the provider.
    Returns:
        MarketDataProvider instance
    Raises:
        ValueError if provider is unknown
    """
    provider = provider or os.getenv('PROVIDER', 'yfinance').lower()
    # If running in Airflow, try to load config from connection extras
    if config is None and 'AIRFLOW_CTX_DAG_ID' in os.environ:
        try:
            from airflow.hooks.base import BaseHook
            conn_id = os.getenv('PROVIDER_CONN_ID', f'market_analysis_{provider}')
            conn = BaseHook.get_connection(conn_id)
            if conn and conn.extra:
                config = json.loads(conn.extra)
        except Exception as e:
            pass  # Fallback to default config
    if provider in ("yfinance", "yf"):
        return YFinanceProvider(config)
    elif provider in ("ibkr", "interactivebrokers"):
        return InteractiveBrokersProvider(config)
    elif provider == "binance":
        return BinanceProvider(config)
    else:
        raise ValueError(f"Unknown provider: {provider}")

__all__ = [
    'MarketDataProvider',
    'YFinanceProvider',
    'InteractiveBrokersProvider',
    'BinanceProvider',
    'provider_factory',
]
