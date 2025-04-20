"""
RabbitMQ client for reliable message queuing.
"""
import aio_pika
import json
import logging
from typing import Any, Callable, Optional
import asyncio

logger = logging.getLogger(__name__)

class RabbitMQClient:
    """RabbitMQ client wrapper for market analysis."""
    
    def __init__(self, host: str = 'localhost', port: int = 5672):
        """Initialize RabbitMQ client.
        
        Args:
            host: RabbitMQ host
            port: RabbitMQ port
        """
        self.host = host
        self.port = port
        self.connection = None
        self.channel = None
        
    async def connect(self):
        """Establish connection to RabbitMQ."""
        try:
            if not self.connection or self.connection.is_closed:
                self.connection = await aio_pika.connect_robust(
                    host=self.host,
                    port=self.port
                )
                self.channel = await self.connection.channel()
                logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Error connecting to RabbitMQ: {e}")
            raise
            
    async def health_check(self) -> bool:
        """Check RabbitMQ connection health.
        
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            if not self.connection or self.connection.is_closed:
                await self.connect()
            return not self.connection.is_closed
        except Exception as e:
            logger.error(f"RabbitMQ health check failed: {e}")
            return False
            
    async def declare_queue(self, queue_name: str):
        """Declare a queue.
        
        Args:
            queue_name: Name of the queue
        """
        try:
            await self.channel.declare_queue(queue_name, durable=True)
        except Exception as e:
            logger.error(f"Error declaring queue: {e}")
            raise
            
    async def publish(self, queue_name: str, message: Any):
        """Publish message to queue.
        
        Args:
            queue_name: Name of the queue
            message: Message to publish
        """
        try:
            if not self.channel:
                await self.connect()
                
            serialized_message = json.dumps(message)
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=serialized_message.encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=queue_name
            )
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            raise
            
    async def consume(self, queue_name: str, callback: Callable):
        """Consume messages from queue.
        
        Args:
            queue_name: Name of the queue
            callback: Callback function to process messages
        """
        try:
            if not self.channel:
                await self.connect()
                
            queue = await self.channel.declare_queue(queue_name, durable=True)
            
            async def process_message(message: aio_pika.IncomingMessage):
                async with message.process():
                    try:
                        decoded_message = json.loads(message.body.decode())
                        await callback(decoded_message)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        
            await queue.consume(process_message)
            
            try:
                await asyncio.Future()  # run forever
            except Exception as e:
                logger.error(f"Consumer interrupted: {e}")
                
        except Exception as e:
            logger.error(f"Error setting up consumer: {e}")
            raise
            
    async def close(self):
        """Close RabbitMQ connection."""
        try:
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
                logger.info("Closed RabbitMQ connection")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")
            raise
