"""
Error handling middleware for API request error handling and logging.
"""
import logging
import traceback
from typing import Union, Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class ErrorResponse:
    """Standard error response format."""
    
    @staticmethod
    def create(
        status_code: int,
        message: str,
        error_type: str = None,
        details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create standardized error response.
        
        Args:
            status_code: HTTP status code
            message: Error message
            error_type: Type of error
            details: Additional error details
            
        Returns:
            Dict containing error information
        """
        response = {
            "error": message,
            "type": error_type or "UnknownError",
            "status_code": status_code
        }
        if details:
            response.update(details)
        return response

class ErrorHandler(BaseHTTPMiddleware):
    """Middleware for handling API errors."""
    
    async def dispatch(self, request: Request, call_next):
        """Process each request and handle errors."""
        try:
            return await call_next(request)
        except ValidationError as e:
            return JSONResponse(
                status_code=422,
                content={"error": "Validation error", "details": e.errors()}
            )
        except RequestValidationError as e:
            return JSONResponse(
                status_code=422,
                content={"error": "Request validation error", "details": e.errors()}
            )
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"error": e.detail}
            )
        except Exception as e:
            logger.error(f"Unhandled error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )
