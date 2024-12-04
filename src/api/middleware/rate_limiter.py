"""
Rate limiting middleware for API request throttling.
"""
import time
from typing import Dict, Tuple
import logging
from fastapi import Request, HTTPException
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class RateLimiter(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis for distributed rate limiting."""
    
    def __init__(
        self,
        app,
        redis_client: Redis,
        rate_limit: int = 100,  # requests per window
        window: int = 60,  # window in seconds
    ):
        """
        Initialize rate limiter.
        
        Args:
            app: FastAPI application
            redis_client: Redis client instance
            rate_limit: Maximum number of requests per window
            window: Time window in seconds
        """
        super().__init__(app)
        self.redis = redis_client
        self.rate_limit = rate_limit
        self.window = window
        self.logger = logging.getLogger(__name__)

    async def get_rate_limit_key(self, request: Request) -> str:
        """
        Generate rate limit key based on client IP and endpoint.
        
        Args:
            request: FastAPI request object
            
        Returns:
            str: Rate limit key
        """
        client_ip = request.client.host
        endpoint = request.url.path
        return f"rate_limit:{client_ip}:{endpoint}"

    async def check_rate_limit(self, key: str) -> Tuple[bool, int]:
        """
        Check if request is within rate limit.
        
        Args:
            key: Rate limit key
            
        Returns:
            Tuple[bool, int]: (is_allowed, remaining_requests)
        """
        try:
            pipeline = self.redis.pipeline()
            current_time = int(time.time())
            window_start = current_time - self.window
            
            # Remove old requests
            await pipeline.zremrangebyscore(key, 0, window_start)
            
            # Count requests in current window
            await pipeline.zcard(key)
            
            # Add current request
            await pipeline.zadd(key, {str(current_time): current_time})
            
            # Set expiry
            await pipeline.expire(key, self.window)
            
            # Execute pipeline
            _, request_count, *_ = await pipeline.execute()
            
            is_allowed = request_count <= self.rate_limit
            remaining = max(0, self.rate_limit - request_count)
            
            return is_allowed, remaining
            
        except Exception as e:
            self.logger.error(f"Error checking rate limit: {str(e)}")
            # If Redis fails, allow the request but log the error
            return True, self.rate_limit

    async def dispatch(self, request: Request, call_next):
        """
        Process the request with rate limiting.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware in chain
            
        Returns:
            Response object
        """
        # Skip rate limiting for WebSocket connections
        if request.url.path.startswith("/ws"):
            return await call_next(request)
            
        key = await self.get_rate_limit_key(request)
        is_allowed, remaining = await self.check_rate_limit(key)
        
        if not is_allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later."
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.window)
        
        return response
