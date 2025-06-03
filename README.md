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

## Development Environment Setup

### Option 1: Multi-Repository Dev Container (Recommended)

For integrated development across all repositories, use the multi-repository Dev Container workspace:

1. **Prerequisites:**
   - [VSCode](https://code.visualstudio.com/) with [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
   - [Docker Desktop](https://www.docker.com/products/docker-desktop/)

2. **Setup:**
   ```bash
   # Ensure all repositories are cloned as siblings
   ~/Documents/gitRepos/
     ├── airflow-hub/
     ├── IndexAgent/
     ├── market-analysis/
     └── infra/
   
   # Open the parent directory in VSCode
   code ~/Documents/gitRepos
   
   # Select "Reopen in Container" and choose the workspace configuration
   ```

3. **Benefits:**
   - Integrated development environment with all repositories
   - Shared PostgreSQL database with dedicated `market_analysis` schema
   - Vault integration for API key management
   - Port 8000 for FastAPI service access
   - Cross-repository communication and testing

### Option 2: Standalone Development

For traditional local development setup:

1. **Clone and Install:**
   ```bash
   git clone https://github.com/mprestonsparks/market-analysis.git
   cd market-analysis
   pip install -r requirements.txt
   ```

2. **Docker Setup:**
   ```bash
   docker build -t market-analysis .
   docker run -it market-analysis
   ```

## Getting Started

### Multi-Repository Workspace Development

When using the multi-repository workspace:

1. **Access FastAPI Service:** http://localhost:8000
   - Interactive API docs: http://localhost:8000/docs
   - OpenAPI schema: http://localhost:8000/openapi.json

2. **Database Access:**
   ```bash
   # Connect to market analysis database
   psql -h postgres -U airflow -d market_analysis
   
   # List tables
   psql -h postgres -U airflow -d market_analysis -c "\dt"
   ```

3. **API Development:**
   ```bash
   # Navigate to market-analysis
   cd /workspaces/market-analysis
   
   # Start development server
   uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
   
   # Run tests
   pytest tests/
   ```

4. **Cross-Repository Integration:**
   ```bash
   # Access other repositories
   cd /workspaces/airflow-hub     # Port 8080 - Airflow orchestration
   cd /workspaces/IndexAgent      # Port 8081 - Code indexing
   cd /workspaces/infra          # Infrastructure tools
   ```

### Standalone Development

```bash
# Start API server
python -m uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000

# Run analysis
python src/main.py --symbol AAPL --days 365

# Run tests
pytest tests/
```

## API Documentation

### FastAPI Endpoints

The market analysis service provides a comprehensive REST API for financial data analysis:

#### Core Analysis Endpoints

**POST /analyze**
```bash
curl -X POST "http://localhost:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "symbol": "AAPL",
       "indicators": ["RSI", "MACD", "BB"],
       "state_analysis": true,
       "num_states": 3
     }'
```

**Response Schema:**
```json
{
  "symbol": "AAPL",
  "analysis_date": "2024-01-01T00:00:00Z",
  "market_state": {
    "current_state": 1,
    "confidence": 0.85,
    "state_characteristics": {
      "volatility": "medium",
      "trend": "bullish",
      "momentum": "strong"
    }
  },
  "technical_indicators": {
    "rsi": {
      "value": 65.2,
      "signal": "neutral",
      "threshold_upper": 70,
      "threshold_lower": 30
    },
    "macd": {
      "macd_line": 1.23,
      "signal_line": 0.98,
      "histogram": 0.25,
      "signal": "bullish"
    },
    "bollinger_bands": {
      "upper": 152.30,
      "middle": 150.00,
      "lower": 147.70,
      "position": "middle"
    }
  },
  "trading_signals": [
    {
      "type": "buy",
      "confidence": 0.78,
      "reason": "RSI oversold with MACD bullish crossover"
    }
  ]
}
```

#### Historical Data Endpoints

**GET /historical/{symbol}**
```bash
curl -X GET "http://localhost:8000/historical/AAPL?days=30&indicators=RSI,MACD"
```

**GET /states/{symbol}**
```bash
curl -X GET "http://localhost:8000/states/AAPL?start_date=2024-01-01&end_date=2024-12-31"
```

#### Health and Status Endpoints

**GET /health**
```bash
curl -X GET "http://localhost:8000/health"
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "external_apis": {
    "yfinance": "available",
    "binance": "connected"
  }
}
```

### WebSocket Integration

Real-time market data streaming:

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/market-stream');

// Subscribe to symbol updates
ws.send(JSON.stringify({
  "action": "subscribe",
  "symbols": ["AAPL", "MSFT", "GOOGL"],
  "indicators": ["RSI", "MACD"]
}));

// Handle real-time updates
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Market update:', data);
};
```

### Database Integration

#### Schema Design

The market analysis service uses a dedicated PostgreSQL schema:

```sql
-- Market data table
CREATE TABLE market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Technical indicators table
CREATE TABLE technical_indicators (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    indicator_type VARCHAR(20) NOT NULL,
    value DECIMAL(10,4),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Market states table
CREATE TABLE market_states (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    state_id INTEGER,
    confidence DECIMAL(5,4),
    characteristics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Database Operations

```python
# Database connection in workspace
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use shared PostgreSQL instance
DATABASE_URL = "postgresql://airflow:airflow@postgres:5432/market_analysis"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Example usage
def store_analysis_result(symbol: str, analysis_data: dict):
    db = SessionLocal()
    try:
        # Store market data
        market_data = MarketData(
            symbol=symbol,
            timestamp=analysis_data['timestamp'],
            close=analysis_data['close_price']
        )
        db.add(market_data)
        db.commit()
    finally:
        db.close()
```

### Migration Procedures

```bash
# Run database migrations
cd /workspaces/market-analysis

# Create new migration
alembic revision --autogenerate -m "Add new market analysis table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Command Line Usage

### Basic Analysis

```bash
# Analyze last 365 days of AAPL
python src/main.py --symbol AAPL --days 365

# Analyze specific date range for TSLA
python src/main.py --symbol TSLA --start 2023-01-01 --end 2023-12-31 --no-signals

# Quick analysis without state identification
python src/main.py --symbol MSFT --days 30 --no-states

# Save analysis plot
python src/main.py --symbol GOOGL --days 180 --save analysis.png
```

### Advanced Options

```bash
# Custom indicators and parameters
python src/main.py --symbol AAPL \
  --indicators RSI,MACD,BB,STOCH \
  --rsi-period 21 \
  --macd-fast 8 \
  --macd-slow 21 \
  --bb-period 20 \
  --bb-std 2.5

# State analysis configuration
python src/main.py --symbol AAPL \
  --num-states 5 \
  --state-features close,volume,rsi,macd \
  --clustering-method kmeans

# Output formats
python src/main.py --symbol AAPL \
  --output-format json \
  --save-data analysis_data.json \
  --save-plot analysis_chart.png
```

### Docker Usage

```bash
# Build and run analysis
docker build -t market-analysis .
docker run -v $(pwd):/app market-analysis --symbol AAPL --days 365

# Run with environment variables
docker run -e BINANCE_API_KEY=your_key \
           -e BINANCE_SECRET_KEY=your_secret \
           -v $(pwd):/app \
           market-analysis --symbol AAPL --days 365
```

## Financial Data Integration

### Data Sources

**Yahoo Finance (Primary):**
- Historical stock data
- Real-time quotes
- Corporate actions and dividends
- Rate limiting: 2000 requests/hour

**Binance API (Cryptocurrency):**
- Crypto market data
- Real-time price feeds
- Order book data
- Rate limiting: 1200 requests/minute

### API Key Management

#### Workspace Environment

```bash
# Store API keys in Vault
vault kv put secret/market-analysis \
  binance_api_key="your_api_key" \
  binance_secret_key="your_secret_key" \
  alpha_vantage_key="your_av_key"

# Access in application
from airflow.models import Variable

binance_key = Variable.get("binance_api_key")
binance_secret = Variable.get("binance_secret_key")
```

#### Local Development

```bash
# Create .env file
cat > .env << EOF
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key
ALPHA_VANTAGE_KEY=your_av_key
EOF

# Load in application
from dotenv import load_dotenv
load_dotenv()
```

### Data Processing Pipeline

```python
# Example data processing workflow
from src.data.fetcher import DataFetcher
from src.analysis.technical import TechnicalAnalyzer
from src.analysis.states import StateAnalyzer

def analyze_symbol(symbol: str, days: int = 365):
    # Fetch historical data
    fetcher = DataFetcher()
    data = fetcher.get_historical_data(symbol, days=days)
    
    # Calculate technical indicators
    tech_analyzer = TechnicalAnalyzer()
    indicators = tech_analyzer.calculate_all(data)
    
    # Identify market states
    state_analyzer = StateAnalyzer()
    states = state_analyzer.identify_states(data, indicators)
    
    return {
        'data': data,
        'indicators': indicators,
        'states': states
    }
```

## Testing Procedures

### Unit Tests

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/test_api.py -v
pytest tests/test_technical_analysis.py -v
pytest tests/test_state_analysis.py -v

# Run with coverage
pytest --cov=src --cov-report=html tests/
```

### Integration Tests

```bash
# Test API endpoints
pytest tests/integration/test_api_integration.py

# Test database operations
pytest tests/integration/test_database.py

# Test external API connections
pytest tests/integration/test_data_sources.py
```

### Performance Tests

```bash
# Load testing
pytest tests/performance/test_load.py

# Memory usage tests
pytest tests/performance/test_memory.py

# Response time benchmarks
pytest tests/performance/test_response_times.py
```

### Docker Test Environment

```bash
# Run tests in isolated container
docker-compose up --build --abort-on-container-exit --exit-code-from test test

# Run specific test suite
docker-compose run --rm test pytest tests/test_api.py -v
```

## Airflow Integration

### DAG Integration

The market analysis tool integrates seamlessly with Airflow for scheduled analysis:

```python
# Example Airflow DAG
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.docker_operator import DockerOperator

default_args = {
    'owner': 'market_analysis',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'market_analysis_daily',
    default_args=default_args,
    description='Daily market analysis workflow',
    schedule_interval='0 9 * * 1-5',  # Weekdays at 9 AM
    catchup=False,
)

analyze_stocks = DockerOperator(
    task_id='analyze_major_stocks',
    image='market-analysis:latest',
    command=['python', 'src/main.py', '--symbol', 'AAPL,MSFT,GOOGL', '--days', '30'],
    environment={
        'BINANCE_API_KEY': '{{ var.value.binance_api_key }}',
        'BINANCE_SECRET_KEY': '{{ var.value.binance_secret_key }}',
    },
    dag=dag,
)
```

### Cross-Service Communication

```python
# Call from Airflow DAG
import requests

def trigger_market_analysis():
    response = requests.post(
        "http://market-analysis:8000/analyze",
        json={
            "symbol": "AAPL",
            "indicators": ["RSI", "MACD", "BB"],
            "state_analysis": True
        }
    )
    return response.json()

# Use in PythonOperator
from airflow.operators.python import PythonOperator

analysis_task = PythonOperator(
    task_id='run_market_analysis',
    python_callable=trigger_market_analysis,
    dag=dag,
)
```

## Troubleshooting

### Common Issues

**API Connection Errors:**
```bash
# Test external API connectivity
curl -X GET "https://api.binance.com/api/v3/ping"
curl -X GET "https://query1.finance.yahoo.com/v8/finance/chart/AAPL"

# Check API key configuration
vault kv get secret/market-analysis
```

**Database Connection Issues:**
```bash
# Test PostgreSQL connectivity
pg_isready -h postgres -p 5432 -U airflow

# Check database exists
psql -h postgres -U airflow -c "\l" | grep market_analysis

# Test connection from application
python -c "
from sqlalchemy import create_engine
engine = create_engine('postgresql://airflow:airflow@postgres:5432/market_analysis')
print('Connection successful:', engine.execute('SELECT 1').scalar())
"
```

**Port Conflicts:**
- FastAPI service: Port 8000
- Ensure no other services are using this port
- Check Docker port mappings: `docker ps`

**Memory Issues:**
```bash
# Monitor memory usage
docker stats market-analysis

# Check for memory leaks in analysis
python -m memory_profiler src/main.py --symbol AAPL --days 365
```

**Rate Limiting Issues:**
```bash
# Check rate limit configuration
grep -r "rate_limit" src/config/

# Monitor API usage
tail -f /logs/market-analysis/api_usage.log
```

### Performance Optimization

**Data Processing:**
- Use vectorized operations with pandas and numpy
- Implement data caching for frequently accessed symbols
- Use connection pooling for database operations
- Optimize SQL queries with proper indexing

**API Response Times:**
- Implement response caching for static data
- Use async/await for concurrent API calls
- Optimize JSON serialization
- Monitor response times with metrics

**Memory Management:**
- Process large datasets in chunks
- Use generators for streaming data
- Clear unused variables and DataFrames
- Monitor memory usage during analysis

## Project Structure

```
market-analysis/
├── Dockerfile                    # Container configuration
├── docker-compose.yml           # Local development setup
├── requirements.txt             # Python dependencies
├── pyproject.toml              # Project configuration
├── README.md                   # This file
├── .env.template               # Environment variables template
├── conftest.py                 # Pytest configuration
├── pytest.ini                 # Test settings
├── docs/                       # Documentation
│   ├── api_reference.md        # API documentation
│   ├── state_aware_trading.md  # Technical details
│   └── dev/                    # Development guides
│       └── README.md
├── examples/                   # Usage examples
│   └── run_analysis.py         # Complete example
├── src/                        # Source code
│   ├── __init__.py
│   ├── main.py                 # CLI entry point
│   ├── api/                    # FastAPI application
│   │   ├── __init__.py
│   │   ├── app.py              # Main FastAPI app
│   │   ├── routes/             # API route definitions
│   │   ├── models/             # Pydantic models
│   │   └── dependencies.py     # Dependency injection
│   ├── analysis/               # Analysis modules
│   │   ├── __init__.py
│   │   ├── technical.py        # Technical indicators
│   │   ├── states.py           # Market state analysis
│   │   └── signals.py          # Trading signals
│   ├── data/                   # Data management
│   │   ├── __init__.py
│   │   ├── fetcher.py          # Data fetching
│   │   ├── processor.py        # Data processing
│   │   └── storage.py          # Database operations
│   ├── config/                 # Configuration
│   │   ├── __init__.py
│   │   ├── settings.py         # Application settings
│   │   ├── rate_limits.py      # API rate limiting
│   │   └── database.py         # Database configuration
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       ├── logging.py          # Logging configuration
│       └── validation.py       # Data validation
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_api.py             # API tests
│   ├── test_technical.py       # Technical analysis tests
│   ├── test_states.py          # State analysis tests
│   ├── integration/            # Integration tests
│   ├── performance/            # Performance tests
│   └── fixtures/               # Test data
├── scripts/                    # Utility scripts
│   ├── setup_database.py       # Database initialization
│   ├── migrate_data.py         # Data migration
│   └── benchmark.py            # Performance benchmarking
└── requirements/               # Dependency management
    ├── base.txt                # Core dependencies
    ├── dev.txt                 # Development dependencies
    └── test.txt                # Testing dependencies
```

## Contributing

### Development Guidelines

1. **Code Standards:**
   - Follow PEP 8 for Python code
   - Use type hints for all function signatures
   - Include comprehensive docstrings
   - Write unit tests for all new features

2. **API Guidelines:**
   - Use RESTful conventions for endpoints
   - Include proper HTTP status codes
   - Validate all input data with Pydantic models
   - Document all endpoints with OpenAPI schemas

3. **Testing Requirements:**
   - Maintain >90% test coverage
   - Include integration tests for external APIs
   - Performance tests for analysis functions
   - Mock external dependencies in unit tests

4. **Documentation:**
   - Update API documentation for endpoint changes
   - Include usage examples for new features
   - Document configuration options
   - Update troubleshooting guides

### Pull Request Process

1. Create feature branch from `main`
2. Implement changes with comprehensive tests
3. Update documentation and examples
4. Ensure all tests pass and coverage requirements met
5. Submit pull request with detailed description
6. Address review feedback
7. Merge after approval and CI success

## License

This project is the private property of M. Preston Sparks. All rights reserved.
