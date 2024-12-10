"""
FastAPI application implementation for market analysis.
"""
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
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

# Initialize FastAPI app
def create_app(test_mode: bool = False) -> FastAPI:
    """Create FastAPI application.
    
    Args:
        test_mode: If True, run in test mode without Redis/RabbitMQ
        
    Returns:
        FastAPI application
    """
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

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Enhanced health check endpoint."""
        return app.health_service.get_health(version=app.version)

    @app.post("/analyze", response_model=AnalysisResult)
    async def analyze_market(request: AnalysisRequest) -> AnalysisResult:
        """
        Analyze market data and return insights.
        
        Args:
            request (AnalysisRequest): Market data analysis request
        
        Returns:
            AnalysisResult: Analysis results and insights
        """
        try:
            # Input validation
            invalid_indicators = [ind for ind in request.indicators if ind.upper() not in SUPPORTED_INDICATORS]
            if invalid_indicators:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported indicators: {', '.join(invalid_indicators)}. Supported indicators are: {', '.join(SUPPORTED_INDICATORS)}"
                )

            # Initialize analyzer
            analyzer = MarketAnalyzer(request.symbol, test_mode=test_mode)
            
            # Fetch data with proper error handling
            try:
                end_time = request.end_time or datetime.now(timezone.utc)
                start_time = request.start_time or (end_time - timedelta(days=30))
                
                # Convert to naive datetime for yfinance
                end_time = end_time.replace(tzinfo=None) if end_time.tzinfo else end_time
                start_time = start_time.replace(tzinfo=None) if start_time.tzinfo else start_time
                
                analyzer.fetch_data(start_time, end_time)
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to fetch data for {request.symbol}: {str(e)}"
                )
                
            # Calculate indicators
            try:
                analyzer.calculate_technical_indicators()
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error calculating technical indicators: {str(e)}"
                )
            
            # Analyze market state if requested
            market_state = None
            if request.state_analysis:
                try:
                    analyzer.identify_market_states(n_states=request.num_states)
                    if analyzer.current_state is not None:
                        characteristics = {}
                        if analyzer.state_characteristics is not None:
                            state_data = analyzer.state_characteristics[analyzer.current_state]
                            characteristics = {
                                'volatility': clean_float(state_data.get('volatility', 0.0)),
                                'trend_strength': clean_float(state_data.get('trend_strength', 0.0)),
                                'volume': clean_float(state_data.get('volume', 0.0)),
                                'return_dispersion': clean_float(state_data.get('return_dispersion', 0.0))
                            }
                        
                        market_state = MarketState(
                            state_id=int(analyzer.current_state),
                            description=analyzer.state_description or "Unknown",
                            characteristics=characteristics,
                            confidence=0.8  # Default confidence
                        )
                except Exception as e:
                    logger.warning(f"Error analyzing market state: {str(e)}")
                    # Continue without market state analysis
            
            # Generate trading signals
            trading_signals = []
            try:
                if request.thresholds:
                    signals_data = analyzer.generate_trading_signals(
                        thresholds={
                            'rsi_oversold': request.thresholds.rsi_oversold,
                            'rsi_overbought': request.thresholds.rsi_overbought,
                            'rsi_weight': request.thresholds.rsi_weight,
                            'macd_threshold_std': request.thresholds.macd_threshold_std,
                            'macd_weight': request.thresholds.macd_weight,
                            'stoch_oversold': request.thresholds.stoch_oversold,
                            'stoch_overbought': request.thresholds.stoch_overbought,
                            'stoch_weight': request.thresholds.stoch_weight,
                            'min_signal_strength': request.thresholds.min_signal_strength,
                            'min_confidence': request.thresholds.min_confidence
                        }
                    )
                else:
                    signals_data = analyzer.generate_trading_signals()

                # Extract signals from the dictionary
                composite_signals = signals_data.get('composite_signal', [])
                confidence_values = signals_data.get('confidence', [])
                
                # Convert the signals to TradingSignal objects
                for i in range(len(analyzer.data)):
                    if i < len(composite_signals) and i < len(confidence_values):
                        signal_value = composite_signals[i]
                        confidence = confidence_values[i]
                        
                        min_strength = request.thresholds.min_signal_strength if request.thresholds else 0.1
                        
                        if abs(signal_value) > min_strength:  # Only include significant signals
                            signal = TradingSignal(
                                timestamp=analyzer.data.index[i],
                                signal_type="BUY" if signal_value > 0 else "SELL",
                                confidence=float(confidence),
                                strength=abs(float(signal_value))
                            )
                            trading_signals.append(signal)
            except Exception as e:
                logger.warning(f"Error generating trading signals: {str(e)}")
                # Continue without trading signals
            
            # Prepare technical indicators result
            technical_indicators = []
            for name in request.indicators:
                name_upper = name.upper()
                if name_upper not in SUPPORTED_INDICATORS:
                    continue
                    
                name_lower = name.lower()
                if name_lower in analyzer.technical_indicators:
                    data = analyzer.technical_indicators[name_lower]
                    value = clean_float(data.iloc[-1]) if not data.empty else None
                    
                    if value is not None:
                        # Get thresholds for the indicator if available
                        upper_threshold = None
                        lower_threshold = None
                        signal = None
                        
                        if request.thresholds:
                            if name_upper == 'RSI':
                                upper_threshold = request.thresholds.rsi_overbought
                                lower_threshold = request.thresholds.rsi_oversold
                                if value >= upper_threshold:
                                    signal = "OVERBOUGHT"
                                elif value <= lower_threshold:
                                    signal = "OVERSOLD"
                            elif name_upper == 'STOCH':
                                upper_threshold = request.thresholds.stoch_overbought
                                lower_threshold = request.thresholds.stoch_oversold
                                if value >= upper_threshold:
                                    signal = "OVERBOUGHT"
                                elif value <= lower_threshold:
                                    signal = "OVERSOLD"
                        
                        indicator = TechnicalIndicator(
                            name=name_upper,
                            value=value,
                            upper_threshold=upper_threshold,
                            lower_threshold=lower_threshold,
                            signal=signal
                        )
                        technical_indicators.append(indicator)
            
            # Create response
            try:
                # Get current price
                current_price = None
                if not analyzer.data.empty:
                    current_price = float(analyzer.data['close'].iloc[-1])

                # Get latest signal
                latest_signal = trading_signals[-1] if trading_signals else None

                # Create response
                response = AnalysisResult(
                    symbol=request.symbol,
                    current_price=current_price,
                    technical_indicators=technical_indicators,
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

    # Add WebSocket route
    @app.websocket("/ws/market/{market_id}")
    async def websocket_endpoint(websocket: WebSocket, market_id: str):
        """WebSocket endpoint for market data subscription."""
        client_id = "test-client"  # For testing
        
        # In test mode, we don't need Redis
        queue_manager = getattr(app, 'queue_manager', None)
        await handle_market_subscription(websocket, client_id, market_id, queue_manager)

    return app

app = create_app(test_mode=True)
