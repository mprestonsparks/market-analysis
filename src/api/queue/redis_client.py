"""
Redis client for caching and pub/sub messaging.
"""
import redis
import json
import logging
from typing import Any, Optional
from datetime import timedelta

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis client wrapper for market analysis."""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        """Initialize Redis client.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
        """
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )
        
    def health_check(self) -> bool:
        """Check Redis connection health.
        
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            return self.redis_client.ping()
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error: {e}")
            return False
            
    def set_data(self, key: str, value: Any, expiry: Optional[timedelta] = None) -> bool:
        """Set data in Redis with optional expiry.
        
        Args:
            key: Redis key
            value: Data to store
            expiry: Optional expiry duration
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            serialized_value = json.dumps(value)
            return self.redis_client.set(key, serialized_value, ex=expiry)
        except Exception as e:
            logger.error(f"Error setting data in Redis: {e}")
            return False
            
    def get_data(self, key: str) -> Optional[Any]:
        """Get data from Redis.
        
        Args:
            key: Redis key
            
        Returns:
            Optional[Any]: Retrieved data or None if not found
        """
        try:
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error getting data from Redis: {e}")
            return None
            
    def publish(self, channel: str, message: Any) -> bool:
        """Publish message to Redis channel.
        
        Args:
            channel: Channel name
            message: Message to publish
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            serialized_message = json.dumps(message)
            return bool(self.redis_client.publish(channel, serialized_message))
        except Exception as e:
            logger.error(f"Error publishing message to Redis: {e}")
            return False
            
    def subscribe(self, channel: str):
        """Subscribe to Redis channel.
        
        Args:
            channel: Channel name
            
        Returns:
            redis.client.PubSub: Subscription object
        """
        try:
            pubsub = self.redis_client.pubsub()
            pubsub.subscribe(channel)
            return pubsub
        except Exception as e:
            logger.error(f"Error subscribing to Redis channel: {e}")
            raise

    async def publish_market_update(self, market_id: str, data: dict) -> None:
        """
        Publish a market update to Redis.
        
        Args:
            market_id (str): Market identifier
            data (dict): Market data to publish
        """
        try:
            channel = f"market:{market_id}"
            await self.redis_client.publish(channel, json.dumps(data))
        except Exception as e:
            logger.error(f"Failed to publish market update: {str(e)}")
            raise

    async def subscribe_to_market(self, market_id: str):
        """
        Subscribe to market updates from Redis.
        
        Args:
            market_id (str): Market identifier to subscribe to
            
        Returns:
            aioredis.client.PubSub: Redis pubsub object
        """
        try:
            pubsub = self.redis_client.pubsub()
            channel = f"market:{market_id}"
            await pubsub.subscribe(channel)
            return pubsub
        except Exception as e:
            logger.error(f"Failed to subscribe to market: {str(e)}")
            raise

    async def unsubscribe_from_market(self, market_id: str):
        """
        Unsubscribe from market updates.
        
        Args:
            market_id (str): Market identifier to unsubscribe from
        """
        try:
            channel = f"market:{market_id}"
            await self.redis_client.pubsub().unsubscribe(channel)
        except Exception as e:
            logger.error(f"Failed to unsubscribe from market: {str(e)}")
            raise
