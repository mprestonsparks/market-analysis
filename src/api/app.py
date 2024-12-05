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
from decimal import Decimal

from src.market_analysis import MarketAnalyzer
from src.api.models.analysis import (
    AnalysisRequest, AnalysisResult, TechnicalIndicator, 
    MarketState, TradingSignal
)

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
app = FastAPI(
    title="Market Analysis API",
    description="API for technical analysis and market state detection",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPPORTED_INDICATORS = {'RSI', 'MACD', 'BB', 'STOCH'}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}

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
                detail=f"Invalid indicators: {invalid_indicators}. Supported indicators are: {SUPPORTED_INDICATORS}"
            )

        # Initialize analyzer
        analyzer = MarketAnalyzer(request.symbol)
        
        try:
            # Fetch data
            end_time = request.end_time or datetime.now(timezone.utc)
            start_time = request.start_time or (end_time - timedelta(days=30))
            
            # Convert to naive datetime for yfinance
            end_time = end_time.replace(tzinfo=None) if end_time.tzinfo else end_time
            start_time = start_time.replace(tzinfo=None) if start_time.tzinfo else start_time
            
            data = analyzer.fetch_data(start_time, end_time)
        except Exception as e:
            logger.error(f"Error fetching data for {request.symbol}: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch data for {request.symbol}: {str(e)}"
            )
            
        if data is None or len(data) == 0:
            logger.error(f"No data available for {request.symbol}")
            raise HTTPException(
                status_code=404,
                detail=f"No data available for {request.symbol}"
            )

        # Calculate indicators
        analyzer.data = data
        analyzer.calculate_technical_indicators()
        
        # Analyze market state if requested
        market_state = None
        if request.state_analysis:
            state_info = analyzer.identify_market_states(n_states=request.num_states)
            if analyzer.current_state is not None:
                # Convert state characteristics to a simple dict of floats
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
        
        # Generate trading signals
        signals_data = analyzer.generate_trading_signals(request.thresholds) if request.thresholds else []
        trading_signals = []
        
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
                        indicators=request.indicators,
                        state_context=market_state
                    )
                    trading_signals.append(signal)
        
        # Prepare technical indicators result
        technical_indicators = []
        for name in request.indicators:
            if name.lower() in analyzer.technical_indicators:
                data = analyzer.technical_indicators[name.lower()]
                value = clean_float(data.iloc[-1]) if not data.empty else None
                
                if value is not None:
                    indicator = TechnicalIndicator(
                        name=name,
                        value=value
                    )
                    technical_indicators.append(indicator)
        
        # Create response
        try:
            current_price = clean_float(analyzer.data['Close'].iloc[-1])
            if current_price is None:
                raise ValueError("Invalid current price")
            
            result = AnalysisResult(
                symbol=request.symbol,
                timestamp=datetime.now(timezone.utc),
                current_price=Decimal(str(current_price)),
                technical_indicators=technical_indicators,
                market_state=market_state,
                latest_signal=trading_signals[-1] if trading_signals else None,
                historical_signals=trading_signals
            )
            return result
        except Exception as e:
            logger.error(f"Error creating analysis result: {str(e)}")
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
