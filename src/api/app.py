"""
FastAPI application implementation for market analysis.
"""
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from typing import Dict, Tuple
import logging
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np
from decimal import Decimal

from src.market_analysis import MarketAnalyzer
from src.api.models.analysis import (
    AnalysisRequest, AnalysisResult, TechnicalIndicator, 
    MarketState, TradingSignal, SignalThresholds
)
from src.api.middleware.rate_limiter import RateLimiter
from src.api.websocket.handlers import handle_market_subscription
from src.api.queue.queue_manager import QueueManager
from src.api.queue.redis_client import RedisClient
from src.api.services.health_service import HealthService
from src.api.models.health import HealthResponse

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
logger = logging.getLogger(__name__)

def create_app(test_mode: bool = False) -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="Market Analysis API",
        description="API for technical analysis and market state detection",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add rate limiter middleware
    app.add_middleware(
        RateLimiter,
        requests_per_minute=100,
        test_mode=test_mode
    )

    # Initialize queue manager
    app.queue_manager = QueueManager(
        redis_client=RedisClient(test_mode=test_mode),
        test_mode=test_mode
    )

    # Initialize health service
    app.health_service = HealthService(
        redis_client=app.queue_manager.redis_client,
        queue_manager=app.queue_manager
    )

    SUPPORTED_INDICATORS = {'RSI', 'MACD', 'BB', 'STOCH'}

    # Setup Prometheus instrumentation
    instrumentator = Instrumentator()
    instrumentator.instrument(app)
    instrumentator.expose(app, include_in_schema=True, tags=["Monitoring"])

    # Initialize custom metrics
    from prometheus_client import Counter
    analysis_counter = Counter(
        'market_analysis_total_analyses',
        'Total number of market analyses performed',
        ['symbol', 'status']
    )

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        health = app.health_service.get_health(version="1.0.0")
        if health.status == "healthy":
            return health
        else:
            raise HTTPException(status_code=500, detail=health.message)

    @app.post("/analyze", response_model=AnalysisResult)
    async def analyze_market(request: AnalysisRequest) -> AnalysisResult:
        """Analyze market data for a given symbol."""
        try:
            # Validate indicators
            invalid_indicators = set(request.indicators) - SUPPORTED_INDICATORS
            if invalid_indicators:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported indicators: {invalid_indicators}"
                )

            try:
                # Fetch and analyze data
                end_time = request.end_time or datetime.now(timezone.utc)
                start_time = request.start_time or (end_time - timedelta(days=30))
                
                analyzer = MarketAnalyzer(symbol=request.symbol)
                market_data = analyzer.fetch_data(
                    start_date=start_time,
                    end_date=end_time
                )
                
                if market_data.empty:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No market data found for symbol {request.symbol}"
                    )

                try:
                    # Calculate indicators
                    indicators_data = analyzer.calculate_technical_indicators()
                    
                    # Determine market state
                    market_state = analyzer.identify_market_states(
                        n_states=request.num_states
                    ) if request.state_analysis else None
                    
                    # Get current price
                    current_price = market_data['close'].iloc[-1]

                    # Generate trading signals if thresholds provided
                    trading_signals = []
                    try:
                        if request.thresholds:
                            signals_data = analyzer.generate_signals(
                                thresholds={
                                    "rsi_overbought": request.thresholds.rsi_overbought if request.thresholds else 70.0,
                                    "rsi_oversold": request.thresholds.rsi_oversold if request.thresholds else 30.0,
                                    "macd_threshold": request.thresholds.macd_threshold_std if request.thresholds else 1.5,
                                    "stoch_overbought": request.thresholds.stoch_overbought if request.thresholds else 80.0,
                                    "stoch_oversold": request.thresholds.stoch_oversold if request.thresholds else 20.0
                                },
                                market_data=market_data,
                                indicators=indicators_data
                            )
                            
                            if signals_data:
                                for timestamp, signal_type in signals_data:
                                    trading_signals.append(
                                        TradingSignal(
                                            timestamp=timestamp,
                                            signal_type=signal_type
                                        )
                                    )
                    
                    except Exception as e:
                        logger.warning(f"Error generating trading signals: {str(e)}")
                        # Continue without signals
                        pass

                    latest_signal = trading_signals[-1] if trading_signals else None

                    # Create response with properly constructed technical indicators
                    technical_indicators_list = [
                        TechnicalIndicator(
                            name=name,
                            value=value,
                            upper_threshold=request.thresholds.get(f"{name.lower()}_overbought") if request.thresholds else None,
                            lower_threshold=request.thresholds.get(f"{name.lower()}_oversold") if request.thresholds else None
                        ) for name, value in indicators_data.items()
                    ]

                    response = AnalysisResult(
                        symbol=request.symbol,
                        current_price=current_price,
                        technical_indicators=technical_indicators_list,
                        market_state=market_state,
                        latest_signal=latest_signal,
                        historical_signals=trading_signals
                    )
                    return response

                except Exception as e:
                    logger.error(f"Error creating analysis result: {str(e)}", exc_info=True)
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error creating analysis result: {str(e)}"
                    )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error analyzing market data: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal server error: {str(e)}"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error validating analysis request: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid analysis request: {str(e)}"
            )

    @app.websocket("/ws/market/{market_id}")
    async def websocket_endpoint(websocket: WebSocket, market_id: str):
        """WebSocket endpoint for market data subscription."""
        await handle_market_subscription(websocket, market_id, app.queue_manager)

    return app

app = create_app(test_mode=True)
