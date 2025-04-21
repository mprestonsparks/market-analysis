"""
FastAPI application implementation for market analysis.
"""
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from prometheus_fastapi_instrumentator import Instrumentator
import time
import os
import psutil
import logging
import pandas as pd
import numpy as np

from src.market_analysis import MarketAnalyzer
from src.api.models.analysis import (
    AnalysisRequest,
    AnalysisResult,
    TechnicalIndicator,
    TradingSignal,
    MarketState
)
from src.api.models.health import HealthResponse, SystemMetrics
from src.api.middleware.rate_limiter import RateLimiter
from src.api.websocket.handlers import handle_market_subscription
from src.api.queue.queue_manager import QueueManager
from src.api.queue.redis_client import RedisClient
from src.api.routers import health

logger = logging.getLogger(__name__)

def clean_float(value):
    """Convert float to JSON-serializable value, handling NaN and infinite values."""
    if isinstance(value, (int, float)):
        if pd.isna(value) or np.isinf(value):
            return None
        return float(value)
    return value

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_app(test_mode: bool = False) -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="Market Analysis API",
        description="API for technical analysis and market state detection",
        version="1.0.0"
    )
    
    # Add start time for uptime tracking
    app.start_time = time.time()
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add rate limiter middleware
    if not test_mode:
        app.add_middleware(RateLimiter)

    # Initialize Redis client
    redis_client = RedisClient(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379))
    )

    # Initialize queue manager
    app.queue_manager = QueueManager(redis_client)

    # Add Prometheus instrumentation
    if not test_mode:
        Instrumentator().instrument(app).expose(app)

    # Include routers
    app.include_router(health.router, prefix="/health", tags=["health"])

    SUPPORTED_INDICATORS = {'RSI', 'MACD', 'BB', 'STOCH'}

    # Initialize custom metrics
    from prometheus_client import Counter
    analysis_counter = Counter(
        'market_analysis_total_analyses',
        'Total number of market analyses performed',
        ['symbol', 'status']
    )

    @app.get("/", response_model=Dict[str, str])
    async def root():
        """Root endpoint."""
        return {
            "service": "Market Analysis API",
            "status": "healthy",
            "version": "1.0.0"
        }

    @app.post("/analyze", response_model=AnalysisResult)
    async def analyze_market(request: AnalysisRequest) -> AnalysisResult:
        """Analyze market data for a given symbol."""
        try:
            # Initialize market analyzer
            analyzer = MarketAnalyzer(request.symbol, test_mode=True)

            # Fetch market data
            market_data = await analyzer.fetch_data(
                start_time=request.start_time,
                end_time=request.end_time
            )

            # Calculate technical indicators
            technical_indicators = {}
            for indicator in request.indicators:
                if indicator == "RSI":
                    technical_indicators["RSI"] = analyzer.calculate_rsi(market_data)
                elif indicator == "MACD":
                    technical_indicators["MACD"] = analyzer.calculate_macd(market_data)
                elif indicator == "BB":
                    technical_indicators["BB"] = analyzer.calculate_bollinger_bands(market_data)
                elif indicator == "STOCH":
                    technical_indicators["STOCH"] = analyzer.calculate_stochastic(market_data)

            # Generate trading signals
            try:
                signals = analyzer.generate_trading_signals(
                    technical_indicators=technical_indicators,
                    thresholds=request.thresholds
                )
            except Exception as e:
                logger.warning(f"Error generating trading signals: {str(e)}")
                signals = []

            # Create technical indicators list
            technical_indicators_list = [
                TechnicalIndicator(
                    name=name,
                    value=float(value.iloc[-1]) if hasattr(value, 'iloc') else float(value[-1]),
                    upper_threshold=request.thresholds.get(f"{name.lower()}_overbought") if request.thresholds else None,
                    lower_threshold=request.thresholds.get(f"{name.lower()}_oversold") if request.thresholds else None
                )
                for name, value in technical_indicators.items()
            ]

            # Perform state analysis if requested
            market_states = []
            if request.state_analysis:
                try:
                    market_states = analyzer.detect_market_states(
                        market_data,
                        num_states=request.num_states
                    )
                except Exception as e:
                    logger.warning(f"Error detecting market states: {str(e)}")

            # Create analysis result
            result = AnalysisResult(
                symbol=request.symbol,
                timestamp=datetime.now(timezone.utc),
                current_price=float(market_data['close'].iloc[-1]) if not market_data.empty else None,
                technical_indicators=technical_indicators_list,
                market_states=market_states,
                signals=signals
            )
            return result

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error creating analysis result: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.websocket("/ws/market/{market_id}")
    async def websocket_endpoint(websocket: WebSocket, market_id: str):
        """WebSocket endpoint for market data subscription."""
        await handle_market_subscription(websocket, market_id, app.queue_manager)

    return app

app = create_app(test_mode=True)
