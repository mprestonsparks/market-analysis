# Market Analysis API Reference

## Overview

The Market Analysis API provides endpoints for analyzing market data using various technical indicators and machine learning techniques. It features state-aware analysis using PCA and clustering to identify market states and generate trading signals.

## Base URL

```
http://localhost:8000
```

## Endpoints

### Health Check

Check the API's health status.

```
GET /health
```

#### Response

```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "1.0.0"
}
```

### Market Analysis

Analyze market data and generate insights.

```
POST /analyze
```

#### Request Body

```json
{
    "symbol": "AAPL",
    "indicators": ["RSI", "MACD", "BB"],
    "state_analysis": true,
    "num_states": 3,
    "thresholds": {
        "rsi_oversold": 30,
        "rsi_overbought": 70,
        "rsi_weight": 0.4,
        "macd_threshold_std": 1.5,
        "macd_weight": 0.4,
        "stoch_oversold": 20,
        "stoch_overbought": 80,
        "stoch_weight": 0.2,
        "min_signal_strength": 0.1,
        "min_confidence": 0.5
    },
    "start_time": "2024-01-01T00:00:00Z",  // Optional
    "end_time": "2024-01-31T00:00:00Z"     // Optional
}
```

#### Parameters

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| symbol | string | Trading symbol to analyze | Required |
| indicators | array | List of technical indicators to include | ["RSI", "MACD", "BB"] |
| state_analysis | boolean | Whether to perform market state analysis | true |
| num_states | integer | Number of market states to identify (2-5) | 3 |
| thresholds | object | Signal generation thresholds | Optional |
| start_time | string | Start time for analysis (ISO format) | 30 days ago |
| end_time | string | End time for analysis (ISO format) | Current time |

#### Threshold Configuration

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| rsi_oversold | float | RSI oversold threshold | 30.0 |
| rsi_overbought | float | RSI overbought threshold | 70.0 |
| rsi_weight | float | Weight of RSI in composite signal | 0.4 |
| macd_threshold_std | float | MACD threshold in standard deviations | 1.5 |
| macd_weight | float | Weight of MACD in composite signal | 0.4 |
| stoch_oversold | float | Stochastic oversold threshold | 20.0 |
| stoch_overbought | float | Stochastic overbought threshold | 80.0 |
| stoch_weight | float | Weight of Stochastic in composite signal | 0.2 |
| min_signal_strength | float | Minimum signal strength to generate a signal | 0.1 |
| min_confidence | float | Minimum confidence level for signals | 0.5 |

#### Response

```json
{
    "symbol": "AAPL",
    "timestamp": "2024-01-01T00:00:00Z",
    "current_price": "150.25",
    "technical_indicators": [
        {
            "name": "RSI",
            "value": 65.5,
            "upper_threshold": 70.0,
            "lower_threshold": 30.0
        }
    ],
    "market_state": {
        "state_id": 1,
        "description": "Bullish Trend",
        "characteristics": {
            "volatility": 0.15,
            "trend_strength": 0.8,
            "volume": 1.2,
            "return_dispersion": 0.05
        },
        "confidence": 0.85
    },
    "latest_signal": {
        "timestamp": "2024-01-01T00:00:00Z",
        "signal_type": "BUY",
        "confidence": 0.75,
        "indicators": ["RSI", "MACD"],
        "state_context": {
            "state_id": 1,
            "description": "Bullish Trend",
            "characteristics": {
                "volatility": 0.15,
                "trend_strength": 0.8,
                "volume": 1.2,
                "return_dispersion": 0.05
            },
            "confidence": 0.85
        }
    },
    "historical_signals": []
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Trading symbol analyzed |
| timestamp | string | Time of analysis |
| current_price | string | Current price of the asset |
| technical_indicators | array | List of technical indicator values |
| market_state | object | Current market state information |
| latest_signal | object | Most recent trading signal |
| historical_signals | array | List of historical trading signals |

### Market States

The API uses PCA (Principal Component Analysis) and clustering to identify distinct market states. Each state is characterized by:

- **Volatility**: Measure of price fluctuations
- **Trend Strength**: Magnitude and consistency of price trends
- **Volume**: Trading volume relative to historical average
- **Return Dispersion**: Distribution of returns indicating market regime

States are dynamically identified based on these characteristics, allowing for adaptive threshold adjustment and signal generation.

### Error Responses

#### 400 Bad Request

```json
{
    "detail": "No data available for symbol INVALID in the specified date range"
}
```

#### 500 Internal Server Error

```json
{
    "detail": "Error processing market analysis: [error message]"
}
```

## Rate Limiting

The API implements rate limiting for data fetching:
- Maximum calls per hour (configurable)
- Exponential backoff for failed requests
- Automatic retry mechanism

## Best Practices

1. **Date Ranges**: Keep analysis periods reasonable (e.g., 30-90 days) for optimal performance
2. **State Analysis**: Use 3-4 market states for most applications
3. **Signal Thresholds**: Adjust based on:
   - Asset volatility
   - Trading timeframe
   - Risk tolerance
4. **Indicator Weights**: Balance between:
   - Momentum (RSI)
   - Trend (MACD)
   - Mean reversion (Stochastic)
