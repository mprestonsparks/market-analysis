"""
FastAPI application implementation for market analysis.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Tuple
import logging
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np

from src.market_analysis import MarketAnalyzer
from src.api.models.analysis import AnalysisRequest, AnalysisResult, TechnicalIndicator, MarketState, TradingSignal

def clean_float(value):
    """Convert float to JSON-serializable value, handling NaN and infinite values."""
    if isinstance(value, (int, float)):
        if np.isnan(value) or np.isinf(value):
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
app = FastAPI(
    title="Market Analysis API",
    description="API for market analysis and trading signals",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store analyzer instances with their last used timestamp
market_analyzers: Dict[str, Tuple[MarketAnalyzer, datetime]] = {}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc),
        "version": "1.0.0"
    }

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
        logger.info(f"Starting analysis for symbol {request.symbol}")
        
        # Get or create analyzer for this market
        analyzer, last_used = market_analyzers.get(request.symbol, (None, None))
        if not analyzer:
            logger.info("Creating new MarketAnalyzer instance")
            analyzer = MarketAnalyzer(request.symbol)
            market_analyzers[request.symbol] = (analyzer, datetime.now(timezone.utc))
        
        # Fetch market data
        end_time = request.end_time or datetime.now(timezone.utc)
        start_time = request.start_time or (end_time - timedelta(days=30))
        
        # Convert to naive datetime for yfinance
        end_time = end_time.replace(tzinfo=None)
        start_time = start_time.replace(tzinfo=None)
        
        logger.info(f"Fetching data for {request.symbol} from {start_time} to {end_time}")
        try:
            analyzer.fetch_data(start_time, end_time)
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching market data: {str(e)}"
            )
        
        if analyzer.data is None or len(analyzer.data) == 0:
            logger.error(f"No data available for {request.symbol}")
            raise HTTPException(
                status_code=400,
                detail=f"No data available for symbol {request.symbol} in the specified date range"
            )
        
        logger.info("Calculating technical indicators")
        try:
            analyzer.calculate_technical_indicators()
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error calculating technical indicators: {str(e)}"
            )
        
        # Identify market states if requested
        current_state = None
        if request.state_analysis:
            logger.info("Performing market state analysis")
            try:
                state_info = analyzer.identify_market_states(n_states=request.num_states)
                if analyzer.current_state is not None:
                    # Convert state characteristics to a simple dict of floats
                    characteristics = {}
                    if analyzer.state_characteristics is not None:
                        for key, value_dict in analyzer.state_characteristics.items():
                            # Convert each dictionary to a single float value (e.g., average of all values)
                            if isinstance(value_dict, dict):
                                value = float(np.mean(list(value_dict.values())))
                            else:
                                value = float(value_dict)
                            characteristics[str(key)] = value
                    
                    current_state = MarketState(
                        state_id=int(analyzer.current_state),
                        description=analyzer.state_description or "Unknown",
                        characteristics=characteristics,
                        confidence=0.8  # Default confidence
                    )
            except Exception as e:
                logger.error(f"Error in market state analysis: {str(e)}", exc_info=True)
                # Continue without state analysis
                pass
        
        # Generate trading signals
        logger.info("Generating trading signals")
        try:
            signals_data = analyzer.generate_trading_signals()
            trading_signals = []
            
            # Extract signals from the dictionary
            composite_signals = signals_data['composite_signal']
            confidence_values = signals_data['confidence']
            
            # Convert the signals to TradingSignal objects
            for i in range(len(analyzer.data)):
                signal_value = composite_signals[i]
                confidence = confidence_values[i]
                
                if abs(signal_value) > 0.1:  # Only include significant signals
                    signal = TradingSignal(
                        timestamp=analyzer.data.index[i],
                        signal_type="BUY" if signal_value > 0 else "SELL",
                        strength=abs(signal_value),
                        confidence=confidence,
                        indicators=request.indicators  # Add the requested indicators
                    )
                    trading_signals.append(signal)
        except Exception as e:
            logger.error(f"Error generating trading signals: {str(e)}", exc_info=True)
            # Continue without signals
            trading_signals = []
        
        # Convert technical indicators to API model
        technical_indicators = []
        base_config = analyzer.indicator_config['base_config']
        for name in request.indicators:
            if name.lower() in analyzer.technical_indicators:
                data = analyzer.technical_indicators[name.lower()]
                config = base_config.get(name.lower(), {})
                
                value = clean_float(data.iloc[-1])
                if value is not None:
                    indicator = TechnicalIndicator(
                        name=name,
                        value=value,
                        upper_threshold=clean_float(config.get('upper_threshold')),
                        lower_threshold=clean_float(config.get('lower_threshold'))
                    )
                    technical_indicators.append(indicator)
        
        # Create response
        try:
            current_price = clean_float(analyzer.data['close'].iloc[-1])
            if current_price is None:
                raise ValueError("Invalid current price")
            
            result = AnalysisResult(
                symbol=request.symbol,
                timestamp=datetime.now(timezone.utc),
                current_price=current_price,
                technical_indicators=technical_indicators,
                market_state=current_state,
                latest_signal=trading_signals[-1] if trading_signals else None,
                historical_signals=trading_signals
            )
            return result
        except Exception as e:
            logger.error(f"Error creating analysis result: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error creating analysis result: {str(e)}"
            )
        
    except Exception as e:
        logger.error(f"Error processing market analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing market analysis: {str(e)}"
        )
