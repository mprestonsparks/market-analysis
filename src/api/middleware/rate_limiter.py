"""Rate limiting middleware for FastAPI."""
import time
import math
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class RateLimiter(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute: int = 100, test_mode: bool = False):
        """Initialize rate limiter.
        
        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute
            test_mode: If True, use test mode settings
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1 minute window
        self.test_mode = test_mode
        self.request_counts: Dict[str, Dict[float, int]] = defaultdict(lambda: defaultdict(int))
        self.last_cleanup = time.time()
    
    def reset(self):
        """Reset rate limiter state. Used for testing."""
        self.request_counts.clear()
        self.last_cleanup = time.time()
    
    def _get_window_stats(self, client_id: str) -> Tuple[int, int, int]:
        """Get current window statistics.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Tuple of (total requests, remaining requests, seconds until reset)
        """
        now = time.time()
        window_start = now - self.window_size
        
        # Clean up old windows
        if now - self.last_cleanup > self.window_size:
            for client in list(self.request_counts.keys()):
                for timestamp in list(self.request_counts[client].keys()):
                    if timestamp < window_start:
                        del self.request_counts[client][timestamp]
                if not self.request_counts[client]:
                    del self.request_counts[client]
            self.last_cleanup = now
        
        # Count requests in current window
        total = sum(
            count for timestamp, count in self.request_counts[client_id].items()
            if timestamp > window_start
        )
        
        remaining = max(0, self.requests_per_minute - total)
        reset_in = int(self.window_size - (now - window_start))
        
        return total, remaining, reset_in
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request and apply rate limiting.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response with rate limit headers
        """
        if self.test_mode:
            # Skip rate limiting in test mode
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(self.requests_per_minute - 1)
            response.headers["X-RateLimit-Reset"] = str(60)  # Reset after 60 seconds in test mode
            return response

        client_id = request.client.host
        current_time = time.time()
        reset_time = math.ceil(current_time / 60.0) * 60

        # Get current window stats
        total, remaining, _ = self._get_window_stats(client_id)
        
        if total >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for client {client_id}")
            return Response(
                content='{"error": "Rate limit exceeded"}',
                status_code=429,
                headers={
                    "Content-Type": "application/json",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_time - current_time)),
                    "Retry-After": str(int(reset_time - current_time))
                }
            )
        
        # Record the request
        now = time.time()
        self.request_counts[client_id][now] += 1
        
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining - 1)
        response.headers["X-RateLimit-Reset"] = str(int(reset_time - current_time))
        
        return response
