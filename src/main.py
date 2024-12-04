"""
Main script for market analysis
"""

import argparse
from datetime import datetime, timedelta
import logging
from market_analysis import MarketAnalyzer
import matplotlib.pyplot as plt

def parse_date(date_str):
    """Parse date string in YYYY-MM-DD format"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Market Analysis Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze last 365 days of AAPL with all features
  python main.py --symbol AAPL --days 365
  
  # Analyze specific date range for TSLA without signals
  python main.py --symbol TSLA --start 2023-01-01 --end 2023-12-31 --no-signals
  
  # Quick analysis of MSFT without state identification
  python main.py --symbol MSFT --days 30 --no-states
        """
    )
    
    # Required arguments
    parser.add_argument('--symbol', type=str, required=True, help='Stock symbol to analyze')
    
    # Date range options (mutually exclusive)
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument('--days', type=int, help='Number of days of historical data')
    date_group.add_argument('--start', type=parse_date, help='Start date (YYYY-MM-DD)')
    
    # Optional arguments
    parser.add_argument('--end', type=parse_date, help='End date (YYYY-MM-DD), defaults to today')
    parser.add_argument('--no-signals', action='store_true', help='Disable trading signal generation')
    parser.add_argument('--no-states', action='store_true', help='Disable market state identification')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--save', type=str, help='Save plot to file (e.g., analysis.png)')
    
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Calculate dates
    end_date = args.end or datetime.now()
    if args.days:
        start_date = end_date - timedelta(days=args.days)
    else:
        start_date = args.start

    try:
        # Initialize analyzer
        analyzer = MarketAnalyzer(args.symbol)
        
        # Fetch and analyze data
        logging.info(f"Fetching data for {args.symbol} from {start_date.date()} to {end_date.date()}...")
        analyzer.fetch_data(start_date, end_date)
        
        if not args.no_signals:
            logging.info("Calculating technical indicators...")
            analyzer.calculate_technical_indicators()
        
        if not args.no_states:
            logging.info("Identifying market states...")
            analyzer.identify_market_states()
        
        # Generate signals
        if not args.no_signals:
            signals = analyzer.generate_trading_signals()
            logging.info(f"Trading signals: {signals}")
        
        # Plot analysis
        fig = analyzer.plot_analysis(
            show_states=not args.no_states,
            show_signals=not args.no_signals
        )
        
        # Save or display plot
        if args.save:
            plt.savefig(args.save, bbox_inches='tight', dpi=300)
            logging.info(f"Plot saved to {args.save}")
        else:
            plt.show()
        
    except Exception as e:
        logging.error(f"Error in analysis: {str(e)}")
        raise

if __name__ == "__main__":
    main()
