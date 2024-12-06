"""Rate limiting middleware for FastAPI."""
import time
from typing import Dict
from fastapi import Request, Response
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import HTTPException
from typing import Callable

class RateLimiter(BaseHTTPMiddleware):
    """Rate limiting middleware."""

    def __init__(
        self,
        app: Callable,
        requests_per_minute: int = 100,
        test_mode: bool = False
    ):
        """Initialize rate limiter."""
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.test_mode = test_mode
        self._request_counts: Dict[str, int] = {}
        self._last_reset: Dict[str, float] = {}

    def _get_client_id(self, request: Request) -> str:
        """Get client ID from request."""
        if self.test_mode:
            return "test_client"
        return request.client.host if request.client else "unknown"

    def _get_remaining(self, client_id: str) -> int:
        """Get remaining requests for client."""
        now = time.time()
        if client_id not in self._last_reset or \
           now - self._last_reset[client_id] >= 60:
            self._request_counts[client_id] = 0
            self._last_reset[client_id] = now
        
        return self.requests_per_minute - self._request_counts[client_id]

    def _update_count(self, client_id: str):
        """Update request count for client."""
        now = time.time()
        if client_id not in self._last_reset or \
           now - self._last_reset[client_id] >= 60:
            self._request_counts[client_id] = 1
            self._last_reset[client_id] = now
        else:
            self._request_counts[client_id] = self._request_counts.get(client_id, 0) + 1

    async def dispatch(
        self, request: Request, call_next
    ):
        """Handle request and apply rate limiting."""
        # Skip WebSocket connections
        if request.scope["type"] == "websocket":
            return await call_next(request)
            
        client_id = self._get_client_id(request)
        remaining = self._get_remaining(client_id)

        if remaining <= 0:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later."
                }
            )

        self._update_count(client_id)
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining - 1)
        response.headers["X-RateLimit-Reset"] = str(
            int(self._last_reset[client_id] + 60)
        )

        return response
