"""
Tests for market analysis module
"""

import unittest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from src.market_analysis import MarketAnalyzer

class TestMarketAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = MarketAnalyzer('AAPL')
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=30)

    def test_fetch_data(self):
        """Test data fetching functionality"""
        self.analyzer.fetch_data(self.start_date, self.end_date)
        self.assertIsNotNone(self.analyzer.data)
        self.assertIsInstance(self.analyzer.data, pd.DataFrame)
        self.assertTrue(len(self.analyzer.data) > 0)

    def test_technical_indicators(self):
        """Test technical indicator calculation"""
        self.analyzer.fetch_data(self.start_date, self.end_date)
        self.analyzer.calculate_technical_indicators()
        
        # Check if all indicators are calculated
        self.assertIn('rsi', self.analyzer.technical_indicators)
        self.assertIn('macd', self.analyzer.technical_indicators)
        self.assertIn('bb_high', self.analyzer.technical_indicators)
        
        # Check if values are within expected ranges
        rsi = self.analyzer.technical_indicators['rsi']
        self.assertTrue(all(0 <= x <= 100 for x in rsi.dropna()))

    def test_market_states(self):
        """Test market state identification"""
        self.analyzer.fetch_data(self.start_date, self.end_date)
        self.analyzer.identify_market_states(n_states=3)
        
        # Check if states are assigned
        self.assertTrue(len(self.analyzer.states) > 0)
        # Check if states are within expected range
        self.assertTrue(all(0 <= x <= 2 for x in self.analyzer.states))

    def test_trading_signals(self):
        """Test trading signal generation"""
        self.analyzer.fetch_data(self.start_date, self.end_date)
        self.analyzer.calculate_technical_indicators()
        signals = self.analyzer.generate_trading_signals()

        # Check signal structure
        self.assertIn('composite_signal', signals)
        self.assertIn('confidence', signals)
        self.assertIn('state_characteristics', signals)
        self.assertIn('current_state', signals)

if __name__ == '__main__':
    unittest.main()
