"""
FastAPI application implementation for market analysis.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import logging
from datetime import datetime, timezone, timedelta
import uuid
import json

from src.api.models import MarketDataRequest, AnalysisResponse
from src.market_analysis import MarketAnalyzer
from src.api.queue.queue_manager import QueueManager
from .middleware.rate_limiter import RateLimiter
from .middleware.error_handler import ErrorHandler
from .websocket.handlers import handle_market_subscription

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

# Initialize global queue manager
queue_manager = None

# Add middleware in the correct order
app.add_middleware(ErrorHandler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_queue_manager() -> QueueManager:
    """
    FastAPI dependency for getting the queue manager instance.
    
    Returns:
        QueueManager: The global queue manager instance
    """
    if queue_manager is None:
        raise HTTPException(
            status_code=503,
            detail="Queue manager not initialized"
        )
    return queue_manager

@app.on_event("startup")
async def startup_event():
    """Initialize connections and middleware on startup."""
    global queue_manager
    try:
        # Initialize queue manager
        queue_manager = QueueManager()
        await queue_manager.initialize_rabbitmq()
        logger.info("Successfully initialized queue connections")
        
        # Add rate limiter after Redis connection is established
        app.add_middleware(
            RateLimiter,
            redis_client=queue_manager.redis_client.redis_client,
            rate_limit=100,  # 100 requests per minute
            window=60  # 1 minute window
        )
        
    except Exception as e:
        logger.error(f"Failed to initialize connections: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on shutdown."""
    await queue_manager.cleanup()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        queue_status = await queue_manager.check_health()
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "queues": queue_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Store analyzer instances
market_analyzers = {}

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_market(
    request: MarketDataRequest,
    background_tasks: BackgroundTasks,
    queue_manager: QueueManager = Depends(get_queue_manager)
) -> AnalysisResponse:
    """
    Analyze market data and return insights.
    
    Args:
        request (MarketDataRequest): Market data analysis request
        background_tasks (BackgroundTasks): FastAPI background tasks
        queue_manager (QueueManager): Queue manager for message handling
        
    Returns:
        AnalysisResponse: Analysis results and insights
    """
    try:
        # Check cache first
        cache_key = f"analysis:{request.symbol}:{request.interval}"
        cached_result = await queue_manager.redis_client.get(cache_key)
        
        if cached_result:
            return AnalysisResponse(**json.loads(cached_result))
        
        # Get or create analyzer for this market
        analyzer = market_analyzers.get(request.symbol)
        if not analyzer:
            analyzer = MarketAnalyzer(request.symbol)
            market_analyzers[request.symbol] = analyzer
        
        # Process the analysis
        signals = await analyzer.analyze(
            interval=request.interval,
            period=request.period
        )
        
        # Create response
        result = create_analysis_response(analyzer, signals)

        # Cache the result
        await queue_manager.redis_client.set(
            cache_key,
            json.dumps(result.dict()),
            expire=300  # 5 minutes cache
        )
        
        # Publish update to subscribers
        await queue_manager.redis_client.publish_market_update(
            market_id=request.symbol,
            data=result.dict()
        )
        
        # Schedule cleanup task
        background_tasks.add_task(cleanup_old_analyzers)
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing market analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing market analysis: {str(e)}"
        )

def create_analysis_response(analyzer: MarketAnalyzer, signals: dict) -> AnalysisResponse:
    """Convert analyzer results to API response model"""
    return AnalysisResponse(
        symbol=analyzer.symbol,
        signals=[{
            'timestamp': analyzer.data.index[i],
            'composite_signal': signals['composite_signal'][i],
            'confidence': signals['confidence'][i],
            'state': signals['current_state']
        } for i in range(len(signals['composite_signal']))],
        states=[{
            'state': state,
            **characteristics
        } for state, characteristics in signals['state_characteristics'].items()],
        metadata={
            'analysis_timestamp': datetime.now(timezone.utc).timestamp(),
            'data_points': len(analyzer.data),
            'signal_strength': float(signals['composite_signal'][-1]),
            'current_confidence': float(signals['confidence'][-1])
        }
    )

async def cleanup_old_analyzers():
    """Remove analyzers that haven't been used recently"""
    # TODO: Implement cleanup logic
    pass

@app.websocket("/ws/market/{market_id}")
async def market_websocket(
    websocket: WebSocket,
    market_id: str,
    client_id: str = None,
    queue_manager: QueueManager = Depends(get_queue_manager)
):
    """
    WebSocket endpoint for real-time market data streaming.
    
    Args:
        websocket (WebSocket): The WebSocket connection
        market_id (str): Market identifier for the subscription
        client_id (str, optional): Client identifier. Defaults to None.
        queue_manager (QueueManager): Queue manager instance
    """
    if client_id is None:
        client_id = str(uuid.uuid4())
    
    await handle_market_subscription(
        websocket=websocket,
        client_id=client_id,
        market_id=market_id,
        queue_manager=queue_manager
    )
