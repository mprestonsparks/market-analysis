"""
Configuration file for API rate limits and related settings.
"""

# YFinance API rate limits
YFINANCE_SETTINGS = {
    'CALLS_PER_HOUR': 60,  # Maximum number of calls per hour
    'PERIOD': 3600,        # Time period in seconds (1 hour)
    'MAX_RETRIES': 5,      # Maximum number of retry attempts
    'BASE_DELAY': 1,       # Base delay in seconds before retrying
    'MAX_DELAY': 32        # Maximum delay in seconds between retries
}

# General API settings
DEFAULT_SETTINGS = {
    'ENABLE_RATE_LIMITING': True,
    'LOG_RATE_LIMITS': True,
    'ASYNC_TIMEOUT': 30    # Timeout in seconds for async operations
}

def get_rate_limit_config(api_name: str = 'yfinance'):
    """
    Get rate limit configuration for specified API.
    
    Args:
        api_name: Name of the API to get configuration for
        
    Returns:
        Dictionary containing rate limit settings
    """
    configs = {
        'yfinance': YFINANCE_SETTINGS,
        'default': DEFAULT_SETTINGS
    }
    return configs.get(api_name.lower(), DEFAULT_SETTINGS)
