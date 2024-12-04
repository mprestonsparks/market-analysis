"""
Error handling middleware for API request error handling and logging.
"""
import logging
import traceback
from typing import Union, Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
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
            "error": {
                "status_code": status_code,
                "message": message,
                "type": error_type or "UnknownError"
            }
        }
        if details:
            response["error"]["details"] = details
        return response

class ErrorHandler(BaseHTTPMiddleware):
    """Middleware for handling API errors."""
    
    async def dispatch(self, request: Request, call_next) -> Union[JSONResponse, Any]:
        """
        Process the request and handle any errors.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware in chain
            
        Returns:
            Response object
        """
        try:
            response = await call_next(request)
            return response
            
        except ValidationError as e:
            logger.warning(f"Validation error: {str(e)}")
            return JSONResponse(
                status_code=422,
                content=ErrorResponse.create(
                    status_code=422,
                    message="Validation error",
                    error_type="ValidationError",
                    details={"errors": e.errors()}
                )
            )
            
        except HTTPException as e:
            logger.warning(f"HTTP error {e.status_code}: {str(e.detail)}")
            return JSONResponse(
                status_code=e.status_code,
                content=ErrorResponse.create(
                    status_code=e.status_code,
                    message=str(e.detail),
                    error_type="HTTPException"
                )
            )
            
        except Exception as e:
            # Log the full traceback for unexpected errors
            logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
            return JSONResponse(
                status_code=500,
                content=ErrorResponse.create(
                    status_code=500,
                    message="Internal server error",
                    error_type=e.__class__.__name__,
                    details={"error": str(e)} if not isinstance(e, HTTPException) else None
                )
            )
