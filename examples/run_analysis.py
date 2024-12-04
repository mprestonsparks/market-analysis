"""
State-Aware Market Analysis Example
================================

This script demonstrates our unsupervised market state analysis approach:
1. Fetch historical market data
2. Extract market features (volatility, trend strength, volume, return dispersion)
3. Identify market states using unsupervised learning (PCA + clustering)
4. Dynamically adjust technical indicators based on market state
5. Generate state-aware trading signals
6. Visualize the results with state transitions

Run this script directly to see the analysis in action:
python run_analysis.py
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.market_analysis import MarketAnalyzer

def analyze_market_states(analyzer, signals):
    """Analyze and print characteristics of each market state"""
    print("\nMarket State Analysis:")
    print("=====================")
    
    for state, chars in signals['state_characteristics'].items():
        print(f"\nState {state}:")
        print("Characteristics:")
        for key, value in chars.items():
            print(f"  - {key}: {value:.3f}")
            
        # Determine typical behavior in this state
        volatility = chars['volatility']
        trend = chars['trend_strength']
        volume = chars['volume']
        
        print("Typical Behavior:")
        print(f"  - Volatility: {'High' if volatility > 0.5 else 'Low'}")
        print(f"  - Trend: {'Strong' if abs(trend) > 0.5 else 'Weak'} "
              f"({'Upward' if trend > 0 else 'Downward'})")
        print(f"  - Volume: {'Above' if volume > 1 else 'Below'} average")

def main():
    # Initialize analyzer with Apple stock
    symbol = 'AAPL'
    analyzer = MarketAnalyzer(symbol)
    
    # Fetch one year of historical data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    analyzer.fetch_data(start_date, end_date)
    
    # Identify market states using unsupervised learning
    print(f"\nAnalyzing market states for {symbol}...")
    analyzer.identify_market_states()
    
    # Calculate technical indicators with state-aware thresholds
    analyzer.calculate_technical_indicators()
    
    # Generate trading signals using state-aware logic
    signals = analyzer.generate_trading_signals()
    
    # Analyze market states and their characteristics
    analyze_market_states(analyzer, signals)
    
    # Print current market state and signal
    current_state = signals['current_state']
    current_signal = signals['composite_signal'][-1]
    current_confidence = signals['confidence'][-1]
    
    print(f"\nCurrent Analysis:")
    print("================")
    print(f"Current Market State: {current_state}")
    print(f"Signal Strength: {current_signal:.2f}")
    print(f"Signal Confidence: {current_confidence:.2f}")
    
    # Plot the complete analysis with state transitions
    analyzer.plot_analysis(show_states=True, show_signals=True)
    
if __name__ == "__main__":
    main()
