"""
Queue manager for handling Redis and RabbitMQ connections.
"""
import os
import logging
from typing import Optional
from .redis_client import RedisClient
from .rabbitmq_client import RabbitMQClient

logger = logging.getLogger(__name__)

class QueueManager:
    """Manager class for message queue connections."""
    
    _instance: Optional['QueueManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize queue connections if not already initialized."""
        if not hasattr(self, 'initialized'):
            self.redis_client = RedisClient(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379))
            )
            
            self.rabbitmq_client = RabbitMQClient(
                host=os.getenv('RABBITMQ_HOST', 'localhost'),
                port=int(os.getenv('RABBITMQ_PORT', 5672))
            )
            
            self.initialized = True
            
    async def check_health(self) -> dict:
        """Check health of all queue connections.
        
        Returns:
            dict: Health status of each connection
        """
        redis_health = self.redis_client.health_check()
        rabbitmq_health = await self.rabbitmq_client.health_check()
        
        return {
            'redis': 'healthy' if redis_health else 'unhealthy',
            'rabbitmq': 'healthy' if rabbitmq_health else 'unhealthy'
        }
        
    async def initialize_rabbitmq(self):
        """Initialize RabbitMQ connection and declare queues."""
        try:
            await self.rabbitmq_client.connect()
            # Declare necessary queues
            queues = ['market_data', 'analysis_results', 'trading_signals']
            for queue in queues:
                await self.rabbitmq_client.declare_queue(queue)
        except Exception as e:
            logger.error(f"Failed to initialize RabbitMQ: {e}")
            raise
            
    async def cleanup(self):
        """Cleanup queue connections."""
        try:
            await self.rabbitmq_client.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            
queue_manager = QueueManager()
