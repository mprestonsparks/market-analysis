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
            return
            
        if self.redis_client:
            await self.redis_client.publish_market_data(market_id, data)
        else:
            logger.warning("No Redis client available for publishing market data")
            
    async def subscribe_to_market(self, market_id: str, client_id: str) -> bool:
        """Subscribe to market data channel.
        
        Args:
            market_id: Market identifier
            client_id: Client identifier
            
        Returns:
            bool: True if subscription was successful
        """
        if self.test_mode:
            return True
            
        if self.redis_client:
            return await self.redis_client.subscribe_to_market(market_id, client_id)
        else:
            logger.warning("No Redis client available for market subscription")
            return False
            
    async def unsubscribe_from_market(self, market_id: str, client_id: str) -> bool:
        """Unsubscribe from market data channel.
        
        Args:
            market_id: Market identifier
            client_id: Client identifier
            
        Returns:
            bool: True if unsubscription was successful
        """
        if self.test_mode:
            return True
            
        if self.redis_client:
            return await self.redis_client.unsubscribe_from_market(market_id, client_id)
        else:
            logger.warning("No Redis client available for market unsubscription")
            return False

queue_manager = QueueManager()
