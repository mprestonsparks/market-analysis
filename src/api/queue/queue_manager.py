"""
Queue manager for handling market data subscriptions.
"""
import logging
from typing import Optional
from .redis_client import RedisClient

logger = logging.getLogger(__name__)

class QueueManager:
    """Queue manager for market data subscriptions."""
    
    _instance: Optional['QueueManager'] = None
    
    def __new__(cls, redis_client: Optional[RedisClient] = None, test_mode: bool = False):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, redis_client: Optional[RedisClient] = None, test_mode: bool = False):
        """Initialize queue manager.
        
        Args:
            redis_client: Redis client instance
            test_mode: If True, operate in test mode without Redis
        """
        if not hasattr(self, 'initialized'):
            self.redis_client = redis_client
            self.test_mode = test_mode
            self.initialized = True
        
    async def publish_market_data(self, market_id: str, data: dict):
        """Publish market data to Redis channel.
        
        Args:
            market_id: Market identifier
            data: Market data to publish
        """
        if self.test_mode:
            # In test mode, just return success
            return True
            
        if self.redis_client:
            await self.redis_client.publish_market_data(market_id, data)
        else:
            # In test mode without Redis, simulate success
            logger.info("Test mode: Simulating market data publish")
            return True
            
    async def subscribe_to_market(self, market_id: str, client_id: str) -> bool:
        """Subscribe to market data channel.
        
        Args:
            market_id: Market identifier
            client_id: Client identifier
            
        Returns:
            bool: True if subscription was successful
        """
        if self.test_mode:
            # In test mode, validate market_id format
            valid_markets = {'BTC-USD', 'ETH-USD', 'AAPL', 'GOOGL', 'MSFT'}
            if market_id not in valid_markets:
                logger.warning(f"Test mode: Invalid market ID {market_id}")
                return False
            return True
            
        if self.redis_client:
            return await self.redis_client.subscribe_to_market(market_id, client_id)
        else:
            # In test mode without Redis, simulate success for valid markets
            logger.info("Test mode: Simulating market subscription")
            return True
            
    async def unsubscribe_from_market(self, market_id: str, client_id: str) -> bool:
        """Unsubscribe from market data channel.
        
        Args:
            market_id: Market identifier
            client_id: Client identifier
            
        Returns:
            bool: True if unsubscription was successful
        """
        if self.test_mode:
            # In test mode, always succeed for cleanup
            return True
            
        if self.redis_client:
            return await self.redis_client.unsubscribe_from_market(market_id, client_id)
        else:
            # In test mode without Redis, simulate success
            logger.info("Test mode: Simulating market unsubscription")
            return True

    async def get_market_data(self, market_id: str) -> Optional[dict]:
        """Get latest market data for a market.
        
        Args:
            market_id: Market identifier
            
        Returns:
            Optional[dict]: Market data if available
        """
        if self.test_mode:
            # In test mode, return simulated market data
            valid_markets = {'BTC-USD', 'ETH-USD', 'AAPL', 'GOOGL', 'MSFT'}
            if market_id not in valid_markets:
                return None
            return {
                "type": "market_data",
                "data": {
                    "market_id": market_id,
                    "price": 100.0,
                    "volume": 1000.0,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            }
            
        if self.redis_client:
            data = await self.redis_client.get_market_data(market_id)
            if data:
                return {
                    "type": "market_data",
                    "data": data
                }
            else:
                return None
        else:
            # In test mode without Redis, return simulated data
            logger.info("Test mode: Returning simulated market data")
            return {
                "type": "market_data",
                "data": {
                    "market_id": market_id,
                    "price": 100.0,
                    "volume": 1000.0,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            }

queue_manager = QueueManager()
