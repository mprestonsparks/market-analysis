"""
Configuration for technical indicators and trading signals.
"""

def get_base_config():
    """
    Get base configuration for technical indicators.
    These serve as default values before state-specific adjustments.
    """
    return {
        'rsi': {
            'window': 14,
            'threshold_percentile': 90,  # Used to dynamically set overbought/oversold
            'weight': 1.0
        },
        'macd': {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9,
            'threshold_std': 1.0,  # Number of standard deviations for signal threshold
            'weight': 1.0
        },
        'stochastic': {
            'k_period': 14,
            'd_period': 3,
            'threshold_percentile': 90,  # Used to dynamically set overbought/oversold
            'weight': 1.0
        },
        'bollinger': {
            'window': 20,
            'num_std': 2
        }
    }

def get_state_adjustment_factors():
    """
    Get adjustment factors for each feature based on PCA components.
    These will be used to modify indicator weights and thresholds based on 
    the statistical properties of each state.
    """
    return {
        'volatility': {
            'rsi_threshold_scale': lambda x: 1 + 0.5 * x,  # Wider thresholds in high volatility
            'rsi_weight_scale': lambda x: 1 / (1 + x),     # Lower weight in high volatility
            'macd_threshold_scale': lambda x: 1 + x,       # Higher threshold in high volatility
            'stoch_threshold_scale': lambda x: 1 + 0.5 * x # Wider thresholds in high volatility
        },
        'trend_strength': {
            'rsi_weight_scale': lambda x: 1 / (1 + abs(x)), # Lower RSI weight in strong trends
            'macd_weight_scale': lambda x: 1 + abs(x),      # Higher MACD weight in strong trends
            'macd_threshold_scale': lambda x: 1 - 0.3 * abs(x) # Lower threshold in strong trends
        },
        'volume': {
            'signal_confidence_scale': lambda x: 1 + 0.2 * x # Higher confidence with higher volume
        }
    }

def get_indicator_config():
    """
    Get configuration for technical indicators.
    Returns a dictionary with base configuration and adjustment factors.
    """
    return {
        'base_config': get_base_config(),
        'adjustment_factors': get_state_adjustment_factors(),
        'min_signal_confidence': 0.6,  # Minimum confidence threshold for signals
        'feature_names': ['volatility', 'trend_strength', 'volume', 'return_dispersion']
    }
