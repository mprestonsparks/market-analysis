"""
Market Analysis Module
====================

This module provides functionality for analyzing market data using various technical indicators
and machine learning techniques to identify market states and generate trading signals.
"""

import os
import sys
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import logging
import asyncio
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.metrics import mean_squared_error
from scipy import stats
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands
import warnings
from ratelimit import limits, sleep_and_retry

# Add src directory to Python path
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.append(src_dir)

from src.config.rate_limits import get_rate_limit_config
from src.config.technical_indicators import get_indicator_config

warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get rate limit configuration for YFinance
yf_config = get_rate_limit_config('yfinance')

@sleep_and_retry
@limits(calls=yf_config['CALLS_PER_HOUR'], period=yf_config['PERIOD'])
def rate_limited_fetch(symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Rate-limited wrapper for yfinance data fetching.
    Implements exponential backoff for failed requests.
    """
    for attempt in range(yf_config['MAX_RETRIES']):
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            if data.empty:
                raise ValueError(f"No data available for {symbol} in the specified time range")
            return data
        except Exception as e:
            if attempt == yf_config['MAX_RETRIES'] - 1:
                raise e
            wait_time = (2 ** attempt) * yf_config['BASE_WAIT_TIME']
            logger.warning(f"Attempt {attempt + 1} failed, waiting {wait_time}s before retry")
            time.sleep(wait_time)

def fetch_market_data(symbol: str, start_date: datetime, end_date: datetime, test_mode: bool = False) -> pd.DataFrame:
    """
    Fetch market data for a given symbol with rate limiting.
    
    Args:
        symbol: Market symbol
        start_date: Start date
        end_date: End date
        test_mode: If True, use test data instead of real market data
        
    Returns:
        DataFrame with market data
    """
    if test_mode:
        # Import test utilities only in test mode
        try:
            from tests.utils.test_data import get_test_market_data, VALID_TEST_SYMBOLS
            if symbol not in VALID_TEST_SYMBOLS:
                raise ValueError(f"Invalid test symbol: {symbol}. Valid test symbols are: {VALID_TEST_SYMBOLS}")
            return get_test_market_data(symbol, start_date, end_date)
        except ImportError:
            raise ImportError("Test utilities not available. Make sure tests/utils is in your Python path.")
    return rate_limited_fetch(symbol, start_date, end_date)

class MarketAnalyzer:
    """Main class for market analysis functionality."""
    
    def __init__(self, symbol: str, indicator_config: Dict = None, test_mode: bool = False, provider=None):
        """Initialize MarketAnalyzer.
        
        Args:
            symbol: Market symbol to analyze
            indicator_config: Optional custom indicator configuration
            test_mode: If True, use test data instead of real market data
            provider: Optional MarketDataProvider instance (default: yfinance)
        """
        self.symbol = symbol
        self.data = None
        self.states = []
        self.technical_indicators = {}
        self.indicator_config = indicator_config or get_indicator_config()
        self.current_state = None
        self.state_description = None
        self.state_characteristics = None
        self.test_mode = test_mode
        if provider is None:
            from src.data_providers import provider_factory
            self.provider = provider_factory()
        else:
            self.provider = provider

        
    def get_state_adjusted_config(self):
        """
        Get configuration dynamically adjusted based on current state characteristics.
        """
        if self.current_state is None or not hasattr(self, 'current_characteristics'):
            return self.indicator_config['base_config']
        
        base_config = self.indicator_config['base_config'].copy()
        adjustment_factors = self.indicator_config['adjustment_factors']
        
        # Apply dynamic adjustments based on state characteristics
        for feature, adjustments in adjustment_factors.items():
            feature_value = self.current_characteristics[feature]
            
            for indicator in base_config:
                # Adjust thresholds
                if f'{indicator}_threshold_scale' in adjustments:
                    scale = adjustments[f'{indicator}_threshold_scale'](feature_value)
                    if 'threshold_percentile' in base_config[indicator]:
                        base_config[indicator]['threshold_percentile'] *= scale
                    if 'threshold_std' in base_config[indicator]:
                        base_config[indicator]['threshold_std'] *= scale
                
                # Adjust weights
                if f'{indicator}_weight_scale' in adjustments:
                    scale = adjustments[f'{indicator}_weight_scale'](feature_value)
                    base_config[indicator]['weight'] *= scale
        
        return base_config
        
    def identify_market_states(self, n_states: int = 3):
        """
        Identify market states using PCA and clustering.
        Returns state characteristics for dynamic threshold adjustment.
        """
        if self.data is None:
            raise ValueError("No data available. Call fetch_data first.")
            
        # Calculate features for PCA
        returns = self.data['close'].pct_change()
        volatility = returns.rolling(window=20).std()
        volume = self.data['volume'] / self.data['volume'].rolling(window=50).mean()
        
        # Calculate trend strength using price momentum and moving average crossovers
        price = self.data['close']
        sma_20 = price.rolling(window=20).mean()
        sma_50 = price.rolling(window=50).mean()
        trend_strength = ((price - sma_20) / price + (sma_20 - sma_50) / sma_20).fillna(0)
        
        # Calculate return dispersion (measure of market regime)
        return_dispersion = returns.rolling(window=20).apply(lambda x: np.percentile(x, 75) - np.percentile(x, 25))
        
        # Prepare features for PCA
        self.feature_names = ['volatility', 'trend_strength', 'volume', 'return_dispersion']
        features = pd.DataFrame({
            'volatility': volatility,
            'trend_strength': trend_strength,
            'volume': volume,
            'return_dispersion': return_dispersion
        }).fillna(0)
        
        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # Perform PCA
        from sklearn.decomposition import PCA
        self.pca = PCA(n_components=2)
        self.pca_result = self.pca.fit_transform(features_scaled)
        
        # Ensure we have enough unique points for the requested number of clusters
        unique_points = np.unique(self.pca_result, axis=0)
        actual_n_states = min(n_states, len(unique_points))
        
        # Cluster states using PCA components
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=actual_n_states, random_state=42)
        self.states = kmeans.fit_predict(self.pca_result)
        
        # Calculate state characteristics for dynamic threshold adjustment
        self.state_characteristics = {}
        for state in range(actual_n_states):
            state_mask = self.states == state
            if not np.any(state_mask):  # Skip if no points in this state
                continue
                
            state_features = features[state_mask]
            
            # Calculate means with proper error handling
            def safe_mean(arr):
                return np.nan if len(arr) == 0 else np.mean(arr)
            
            self.state_characteristics[state] = {
                'volatility': safe_mean(state_features['volatility']),
                'trend_strength': safe_mean(state_features['trend_strength']),
                'volume': safe_mean(state_features['volume']),
                'return_dispersion': safe_mean(state_features['return_dispersion']),
                'component_1': safe_mean(self.pca_result[state_mask, 0]),
                'component_2': safe_mean(self.pca_result[state_mask, 1])
            }
        
        # Set current state and its characteristics
        self.current_state = self.states[-1]
        self.current_characteristics = self.state_characteristics[self.current_state]
        
    def calculate_technical_indicators(self):
        """Calculate various technical indicators."""
        if self.data is None:
            raise ValueError("No data available. Call fetch_data first.")
            
        config = self.indicator_config['base_config']
            
        # RSI
        rsi = RSIIndicator(
            close=self.data['close'],
            window=config['rsi']['window']
        )
        self.technical_indicators['rsi'] = rsi.rsi()
        
        # MACD
        macd = MACD(
            close=self.data['close'],
            window_fast=config['macd']['fast_period'],
            window_slow=config['macd']['slow_period'],
            window_sign=config['macd']['signal_period']
        )
        self.technical_indicators['macd'] = macd.macd()
        self.technical_indicators['macd_signal'] = macd.macd_signal()
        
        # Stochastic
        stoch = StochasticOscillator(
            high=self.data['high'],
            low=self.data['low'],
            close=self.data['close'],
            window=config['stochastic']['k_period'],
            smooth_window=config['stochastic']['d_period']
        )
        self.technical_indicators['stoch_k'] = stoch.stoch()
        self.technical_indicators['stoch_d'] = stoch.stoch_signal()
        
        # Bollinger Bands
        bb = BollingerBands(
            close=self.data['close'],
            window=config['bollinger']['window'],
            window_dev=config['bollinger']['num_std']
        )
        self.technical_indicators['bb_high'] = bb.bollinger_hband()
        self.technical_indicators['bb_low'] = bb.bollinger_lband()
        self.technical_indicators['bb_mid'] = bb.bollinger_mavg()

    def generate_trading_signals(self, thresholds=None) -> Dict:
        """
        Generate trading signals based on technical indicators and dynamic state-based thresholds.
        Returns signals for the entire time series.
        
        Args:
            thresholds: Optional signal generation thresholds. If None, uses default configuration.
        """
        if not self.technical_indicators:
            self.calculate_technical_indicators()
            
        if self.current_state is None:
            self.identify_market_states()
            
        config = self.get_state_adjusted_config()
        
        # Override config with provided thresholds if any
        if thresholds:
            config['rsi']['oversold'] = thresholds.rsi_oversold
            config['rsi']['overbought'] = thresholds.rsi_overbought
            config['rsi']['weight'] = thresholds.rsi_weight
            
            config['macd']['threshold_std'] = thresholds.macd_threshold_std
            config['macd']['weight'] = thresholds.macd_weight
            
            config['stochastic']['oversold'] = thresholds.stoch_oversold
            config['stochastic']['overbought'] = thresholds.stoch_overbought
            config['stochastic']['weight'] = thresholds.stoch_weight
            
            self.indicator_config['min_signal_confidence'] = thresholds.min_confidence
        
        # Initialize signal arrays
        length = len(self.data)
        composite_signals = np.zeros(length)
        confidence_values = np.zeros(length)
        
        # Get historical data for percentile calculations
        historical_window = 100  # Look back period for percentile calculations
        
        for i in range(historical_window, length):
            # Calculate RSI signals
            rsi = self.technical_indicators['rsi'].iloc[i]
            rsi_history = self.technical_indicators['rsi'].iloc[i-historical_window:i]
            
            oversold = config['rsi']['oversold']
            overbought = config['rsi']['overbought']
            
            rsi_signal = 1 if rsi < oversold else -1 if rsi > overbought else 0
            rsi_strength = abs((rsi - 50) / 50)
            
            # Calculate MACD signals
            macd = self.technical_indicators['macd'].iloc[i]
            macd_signal = self.technical_indicators['macd_signal'].iloc[i]
            macd_history = (self.technical_indicators['macd'] - self.technical_indicators['macd_signal']).iloc[i-historical_window:i]
            
            macd_threshold = config['macd']['threshold_std'] * macd_history.std()
            macd_diff = macd - macd_signal
            
            macd_signal = 1 if macd_diff > macd_threshold else -1 if macd_diff < -macd_threshold else 0
            macd_strength = abs(macd_diff) / macd_history.std()
            
            # Calculate Stochastic signals
            stoch_k = self.technical_indicators['stoch_k'].iloc[i]
            stoch_history = self.technical_indicators['stoch_k'].iloc[i-historical_window:i]
            
            oversold = config['stochastic']['oversold']
            overbought = config['stochastic']['overbought']
            
            stoch_signal = 1 if stoch_k < oversold else -1 if stoch_k > overbought else 0
            stoch_strength = min(abs(stoch_k - 50) / 50, 1.0)
            
            # Calculate weighted composite signal
            weights = [
                config['rsi']['weight'],
                config['macd']['weight'],
                config['stochastic']['weight']
            ]
            signals = [rsi_signal, macd_signal, stoch_signal]
            strengths = [rsi_strength, macd_strength, stoch_strength]
            
            weighted_signal = sum(s * st * w for s, st, w in zip(signals, strengths, weights))
            total_weight = sum(weights)
            composite_signals[i] = weighted_signal / total_weight
            
            # Calculate confidence
            volume_scale = self.data['volume'].iloc[i] / self.data['volume'].iloc[i-20:i].mean()
            confidence_scale = 1 + 0.2 * volume_scale  # Simple volume-based scaling
            confidence_values[i] = confidence_scale * min(
                max(abs(composite_signals[i]), self.indicator_config['min_signal_confidence']),
                1.0
            )
        
        return {
            'composite_signal': composite_signals,
            'confidence': confidence_values,
            'state_characteristics': self.state_characteristics,
            'current_state': self.current_state
        }
        
    def plot_analysis(self, show_states=True, show_signals=True):
        """
        Plot comprehensive market analysis in a single interactive window:
        1. Price and volume data
        2. Technical indicators
        3. Market states from PCA and characteristics
        4. Trading signals with confidence
        5. Feature importance
        """
        if self.data is None:
            raise ValueError("No data available. Call fetch_data first.")
            
        if show_signals and not self.technical_indicators:
            self.calculate_technical_indicators()
            
        if show_states and self.current_state is None:
            self.identify_market_states()

        import tkinter as tk
        from tkinter import ttk
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        
        # Create main window
        root = tk.Tk()
        root.title(f"Market Analysis - {self.symbol}")
        root.geometry("1200x800")
        
        # Create notebook (tabbed interface)
        notebook = ttk.Notebook(root)
        notebook.pack(fill='both', expand=True)
        
        def create_tab(title):
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=title)
            return frame
            
        def add_plot_to_tab(fig, frame):
            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.draw()
            toolbar = NavigationToolbar2Tk(canvas, frame)
            toolbar.update()
            canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # 1. Price and Volume Plot
        fig1 = plt.figure(figsize=(12, 6))
        ax1 = fig1.add_subplot(111)
        self._plot_price_and_volume(ax1, show_states)
        fig1.tight_layout()
        add_plot_to_tab(fig1, create_tab("Price & Volume"))
        
        # 2. Technical Indicators
        if show_signals:
            tech_frame = create_tab("Technical Indicators")
            
            # Create control frame for dropdown
            control_frame = ttk.Frame(tech_frame)
            control_frame.pack(fill='x', padx=5, pady=5)
            
            # Create indicator selection dropdown
            ttk.Label(control_frame, text="Select Indicator:").pack(side='left', padx=5)
            indicator_var = tk.StringVar(value='RSI')
            indicators = ['RSI', 'MACD', 'Stochastic', 'Bollinger Bands']
            indicator_dropdown = ttk.Combobox(control_frame, textvariable=indicator_var, values=indicators, state='readonly')
            indicator_dropdown.pack(side='left', padx=5)
            
            # Create plot frame
            plot_frame = ttk.Frame(tech_frame)
            plot_frame.pack(fill='both', expand=True)
            
            # Initial plot
            fig2 = plt.figure(figsize=(12, 6))
            ax2 = fig2.add_subplot(111)
            self._plot_technical_indicators(ax2, indicator_var.get())
            fig2.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig2, master=plot_frame)
            canvas.draw()
            toolbar = NavigationToolbar2Tk(canvas, plot_frame)
            toolbar.update()
            canvas.get_tk_widget().pack(fill='both', expand=True)
            
            # Update function for dropdown
            def update_indicator(*args):
                ax2.clear()
                self._plot_technical_indicators(ax2, indicator_var.get())
                fig2.tight_layout()
                canvas.draw()
            
            indicator_var.trace('w', update_indicator)
        
        # 3. Market States Analysis
        if show_states:
            fig3 = plt.figure(figsize=(12, 6))
            gs3 = fig3.add_gridspec(1, 2)
            ax3_1 = fig3.add_subplot(gs3[0, 0])
            self._plot_pca_components(ax3_1)
            ax3_2 = fig3.add_subplot(gs3[0, 1])
            self._plot_state_characteristics(ax3_2)
            fig3.tight_layout()
            add_plot_to_tab(fig3, create_tab("Market States"))
        
        # 4. Trading Signals
        if show_signals:
            fig4 = plt.figure(figsize=(12, 6))
            ax4 = fig4.add_subplot(111)
            self._plot_trading_signals(ax4)
            fig4.tight_layout()
            add_plot_to_tab(fig4, create_tab("Trading Signals"))
        
        # 5. Feature Importance
        if show_states:
            fig5 = plt.figure(figsize=(12, 6))
            ax5 = fig5.add_subplot(111)
            self._plot_feature_importance(ax5)
            fig5.tight_layout()
            add_plot_to_tab(fig5, create_tab("Feature Importance"))
        
        # Start the tkinter event loop
        root.mainloop()
        
    def _plot_price_and_volume(self, ax, show_states=True):
        """Plot price and volume with state backgrounds."""
        # Plot price
        ax2 = ax.twinx()
        ax.plot(self.data.index, self.data['close'], 'b-', label='Price', zorder=2)
        
        # Add state backgrounds if available
        if show_states and hasattr(self, 'states'):
            unique_states = np.unique(self.states)
            colors = plt.cm.tab20(np.linspace(0, 1, len(unique_states)))
            
            for state in unique_states:
                mask = self.states == state
                ax.fill_between(self.data.index, ax.get_ylim()[0], ax.get_ylim()[1],
                              where=mask, color=colors[state], alpha=0.2,
                              label=f'State {state}')
        
        # Plot volume
        volume_normalized = self.data['volume'] / self.data['volume'].max()
        ax2.fill_between(self.data.index, 0, volume_normalized, color='gray', alpha=0.3, label='Volume')
        
        ax.set_title('Price and Volume with Market States')
        ax.set_xlabel('Date')
        ax.set_ylabel('Price')
        ax2.set_ylabel('Normalized Volume')
        ax.legend(loc='upper left')
        ax2.legend(loc='upper right')
        
    def _plot_technical_indicators(self, ax, indicator_type='RSI'):
        """Plot selected technical indicator with dynamic thresholds."""
        config = self.get_state_adjusted_config()
        
        if indicator_type == 'RSI':
            # Plot RSI
            ax.plot(self.data.index, self.technical_indicators['rsi'], 'b-', label='RSI')
            
            # Add dynamic thresholds
            rsi_history = self.technical_indicators['rsi'].iloc[-100:]
            oversold = np.percentile(rsi_history, 100 - config['rsi']['threshold_percentile'])
            overbought = np.percentile(rsi_history, config['rsi']['threshold_percentile'])
            
            ax.axhline(y=oversold, color='g', linestyle='--', alpha=0.5, label='Oversold')
            ax.axhline(y=overbought, color='r', linestyle='--', alpha=0.5, label='Overbought')
            ax.set_ylim(0, 100)
            
        elif indicator_type == 'MACD':
            # Plot MACD
            ax.plot(self.data.index, self.technical_indicators['macd'], 'b-', label='MACD')
            ax.plot(self.data.index, self.technical_indicators['macd_signal'], 'r-', label='Signal Line')
            
            # Plot MACD histogram
            hist = self.technical_indicators['macd'] - self.technical_indicators['macd_signal']
            ax.bar(self.data.index, hist, color=['g' if x >= 0 else 'r' for x in hist], alpha=0.3, label='MACD Histogram')
            
        elif indicator_type == 'Stochastic':
            # Plot Stochastic
            ax.plot(self.data.index, self.technical_indicators['stoch_k'], 'b-', label='%K')
            ax.plot(self.data.index, self.technical_indicators['stoch_d'], 'r-', label='%D')
            
            # Add overbought/oversold levels
            ax.axhline(y=20, color='g', linestyle='--', alpha=0.5, label='Oversold')
            ax.axhline(y=80, color='r', linestyle='--', alpha=0.5, label='Overbought')
            ax.set_ylim(0, 100)
            
        elif indicator_type == 'Bollinger Bands':
            # Plot Bollinger Bands
            ax.plot(self.data.index, self.data['close'], 'k-', label='Price', alpha=0.5)
            ax.plot(self.data.index, self.technical_indicators['bb_high'], 'r-', label='Upper Band')
            ax.plot(self.data.index, self.technical_indicators['bb_mid'], 'b-', label='Middle Band')
            ax.plot(self.data.index, self.technical_indicators['bb_low'], 'g-', label='Lower Band')
            
            # Fill between bands
            ax.fill_between(self.data.index, 
                          self.technical_indicators['bb_high'],
                          self.technical_indicators['bb_low'],
                          alpha=0.1, color='gray')
        
        ax.set_title(f'{indicator_type} Indicator')
        ax.set_xlabel('Date')
        ax.set_ylabel('Value')
        ax.legend()
        ax.grid(True, alpha=0.3)

    def _plot_pca_components(self, ax):
        """Plot PCA components and clustering results."""
        if not hasattr(self, 'pca_result'):
            return
            
        scatter = ax.scatter(self.pca_result[:, 0], self.pca_result[:, 1],
                           c=self.states, cmap='tab20', alpha=0.6)
        ax.set_title('Market States in PCA Space')
        ax.set_xlabel('First Principal Component')
        ax.set_ylabel('Second Principal Component')
        plt.colorbar(scatter, ax=ax, label='State')
        
    def _plot_state_characteristics(self, ax):
        """Plot characteristics of each market state."""
        if not hasattr(self, 'state_characteristics'):
            return
            
        features = list(self.state_characteristics[0].keys())
        states = list(self.state_characteristics.keys())
        
        x = np.arange(len(features))
        width = 0.8 / len(states)
        
        for i, state in enumerate(states):
            characteristics = list(self.state_characteristics[state].values())
            ax.bar(x + i * width, characteristics, width, label=f'State {state}')
        
        ax.set_title('State Characteristics')
        ax.set_xticks(x + width * (len(states) - 1) / 2)
        ax.set_xticklabels(features, rotation=45)
        ax.legend()
        
    def _plot_trading_signals(self, ax):
        """Plot trading signals with confidence bands."""
        signals = self.generate_trading_signals()
        
        # Plot composite signal
        ax.plot(self.data.index, signals['composite_signal'],
                'b-', label='Signal', linewidth=1.5)
        
        # Plot confidence bands
        ax.fill_between(self.data.index,
                       -signals['confidence'], signals['confidence'],
                       color='gray', alpha=0.2, label='Confidence Band')
        
        # Add state transitions
        if hasattr(self, 'states'):
            for i in range(1, len(self.states)):
                if self.states[i] != self.states[i-1]:
                    ax.axvline(x=self.data.index[i], color='r', linestyle='--', alpha=0.3)
        
        ax.set_title('Trading Signals with Confidence')
        ax.set_xlabel('Date')
        ax.set_ylabel('Signal Strength')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
    def _plot_feature_importance(self, ax):
        """Plot feature importance from PCA."""
        if not hasattr(self, 'pca') or not hasattr(self, 'feature_names'):
            return
            
        features = self.feature_names
        importance = np.abs(self.pca.components_[0])  # Use first principal component
        
        y_pos = np.arange(len(features))
        ax.barh(y_pos, importance)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(features)
        ax.set_title('Feature Importance in First Principal Component')
        ax.set_xlabel('Absolute Coefficient Value')
        
    def _standardize_columns(self, data: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names from various data sources."""
        column_map = {
            'Close': 'close',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Volume': 'volume',
            'Adj Close': 'adj_close'
        }
        return data.rename(columns=column_map)

    async def fetch_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch market data for analysis using the configured provider.
        
        Args:
            start_date: Start date for data fetch
            end_date: End date for data fetch
            
        Returns:
            DataFrame with market data
        """
        try:
            data = await self.provider.fetch_data(self.symbol, start_date, end_date)
            if data is None or len(data) == 0:
                raise ValueError(f"No data available for {self.symbol}")
            
            # Standardize column names
            self.data = self._standardize_columns(data)
            return self.data
        except Exception as e:
            logger.error(f"Error fetching data for {self.symbol}: {str(e)}")
            raise
