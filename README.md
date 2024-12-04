# Market Analysis Tool

A Python-based market analysis tool that provides technical analysis, market state identification, and trading signals for financial instruments. The system uses advanced machine learning techniques (PCA and clustering) to identify market states and dynamically adjust trading signals based on market conditions.

## Features

- **State-Aware Trading System**
  - Dynamic market state identification using PCA and unsupervised learning
  - Adaptive technical indicator thresholds based on market conditions
  - State-specific signal generation with confidence metrics
  - Comprehensive visualization of market states and signals

- **Technical Analysis**
  - RSI with dynamic thresholds
  - MACD with state-adjusted sensitivity
  - Stochastic Oscillator with adaptive parameters
  - Bollinger Bands for volatility analysis

- **Data Management**
  - Historical market data fetching with rate limiting
  - Efficient data processing and feature engineering
  - Real-time state and signal updates

- **Visualization Suite**
  - Interactive market state visualization
  - PCA component analysis plots
  - State characteristic comparisons
  - Trading signal confidence bands

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd market-analysis
```

2. Build and run using Docker:
```bash
docker build -t market-analysis .
docker run -it market-analysis
```

Or install locally with pip:
```bash
pip install -r requirements.txt
```

## Usage

The market analysis tool can be run from the command line with various options:

```bash
# Basic usage - analyze last 365 days of AAPL
python src/main.py --symbol AAPL --days 365

# Analyze specific date range for TSLA without signals
python src/main.py --symbol TSLA --start 2023-01-01 --end 2023-12-31 --no-signals

# Quick analysis of MSFT without state identification
python src/main.py --symbol MSFT --days 30 --no-states

# Save plot to file
python src/main.py --symbol GOOGL --days 180 --save analysis.png
```

### Command Line Options

- `--symbol` (required): Stock symbol to analyze (e.g., AAPL, MSFT)
- `--days` or `--start`: Number of days of historical data OR specific start date
- `--end`: End date for analysis (defaults to today)
- `--no-signals`: Disable trading signal generation
- `--no-states`: Disable market state identification
- `--debug`: Enable debug logging
- `--save`: Save plot to specified file

### Docker Usage

Build and run the analysis tool using Docker:

```bash
# Build the Docker image
docker build -t market-analysis .

# Run analysis (example)
docker run -v $(pwd):/app market-analysis --symbol AAPL --days 365
```

## Examples

Check out the `examples` directory for sample scripts demonstrating various analysis scenarios:

- `run_analysis.py`: Complete example showing basic usage of all features

## Documentation

Detailed documentation is available in the [docs](docs/) directory:
- [State-Aware Trading System Guide](docs/state_aware_trading.md)

## Project Structure

```
market-analysis/
├── Dockerfile
├── requirements.txt
├── README.md
├── docs/
│   └── state_aware_trading.md
├── examples/
│   └── run_analysis.py
└── src/
    ├── config/
    │   ├── __init__.py
    │   ├── rate_limits.py
    │   └── technical_indicators.py
    ├── market_analysis.py
    └── main.py
```

## Dependencies

- numpy
- pandas
- yfinance
- scikit-learn
- scipy
- matplotlib
- ta
- ratelimit
- python-dotenv
- asyncio

## Rate Limiting

The tool implements rate limiting for the YFinance API to prevent exceeding usage limits. Configuration can be modified in `src/config/rate_limits.py`.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is the private property of M. Preston Sparks. All rights reserved.
