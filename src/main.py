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
    parser.add_argument('--symbol', type=str, required=True, help='Market symbol to analyze (e.g., BTCUSDT, AAPL)')
    
    # Date range options (mutually exclusive)
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument('--days', type=int, help='Number of days of historical data')
    date_group.add_argument('--start', type=parse_date, help='Start date (YYYY-MM-DD)')
    
    # Provider selection
    parser.add_argument('--provider', type=str, choices=['ibkr', 'binance', 'yf', 'yfinance'], default='yf', help='Market data provider (ibkr, binance, yf)')
    # IBKR-specific params
    parser.add_argument('--host', type=str, help='IBKR host (default: localhost)')
    parser.add_argument('--port', type=int, help='IBKR port (default: 7496)')
    parser.add_argument('--client_id', type=int, help='IBKR client ID (default: 1)')
    # Binance-specific params
    parser.add_argument('--api_key', type=str, help='Binance API key')
    parser.add_argument('--api_secret', type=str, help='Binance API secret')
    parser.add_argument('--testnet', action='store_true', help='Use Binance testnet')
    
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

    # Build provider config
    provider_config = {}
    if args.provider in ('ibkr', 'interactivebrokers'):
        if args.host:
            provider_config['host'] = args.host
        if args.port:
            provider_config['port'] = args.port
        if args.client_id:
            provider_config['client_id'] = args.client_id
    elif args.provider == 'binance':
        if args.api_key:
            provider_config['api_key'] = args.api_key
        if args.api_secret:
            provider_config['api_secret'] = args.api_secret
        if args.testnet:
            provider_config['testnet'] = True

    # Initialize analyzer with provider
    from data_providers import provider_factory
    provider = provider_factory(args.provider, provider_config)
    analyzer = MarketAnalyzer(
        symbol=args.symbol,
        provider=provider
    )
    
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


if __name__ == "__main__":
    main()
