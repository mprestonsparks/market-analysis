"""Rate limiter middleware."""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import logging

logger = logging.getLogger(__name__)

class RateLimiter(BaseHTTPMiddleware):
    """Rate limiter middleware."""

    def __init__(self, app, requests_per_minute: int = 100, test_mode: bool = False):
        """Initialize rate limiter."""
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # seconds
        self.requests = {}
        self.test_mode = test_mode

    def reset(self):
        """Reset rate limiter state. Used for testing."""
        self.requests.clear()

    async def dispatch(self, request: Request, call_next) -> Response:
        """Handle request."""
        client_id = "test_client" if self.test_mode else request.client.host
        current_time = time.time()

        # Clean up old requests
        if client_id in self.requests:
            self.requests[client_id] = [
                timestamp for timestamp in self.requests[client_id]
                if current_time - timestamp < self.window_size
            ]

        # Initialize request list for new clients
        if client_id not in self.requests:
            self.requests[client_id] = []

        # Check rate limit
        if len(self.requests[client_id]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for client {client_id}")
            response = Response(
                content='{"error": "Rate limit exceeded"}',
                status_code=429,
                headers={
                    "Content-Type": "application/json"
                }
            )
            reset_time = min(self.requests[client_id]) + self.window_size
            remaining = 0
        else:
            # Add current request
            self.requests[client_id].append(current_time)
            response = await call_next(request)
            reset_time = current_time + self.window_size
            remaining = self.requests_per_minute - len(self.requests[client_id])

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_time - current_time))
        response.headers["Retry-After"] = str(int(reset_time - current_time)) if remaining == 0 else "0"

        return response
