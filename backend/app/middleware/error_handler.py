"""
Error Handling Middleware

Global error handling for FastAPI application with structured
error responses and logging.
"""

import logging
import traceback
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from opensearchpy import exceptions as opensearch_exceptions

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: dict = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(APIError):
    """Resource not found error."""
    
    def __init__(self, message: str = "Resource not found", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details=details,
        )


class ValidationError(APIError):
    """Validation error."""
    
    def __init__(self, message: str = "Validation failed", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class ConflictError(APIError):
    """Resource conflict error."""
    
    def __init__(self, message: str = "Resource conflict", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
            details=details,
        )


class DatabaseError(APIError):
    """Database operation error."""
    
    def __init__(self, message: str = "Database error", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            details=details,
        )


async def error_handler_middleware(request: Request, call_next: Callable) -> Response:
    """
    Global error handling middleware.
    
    Catches all exceptions and returns structured error responses.
    Logs errors with appropriate context for debugging.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/route handler
        
    Returns:
        Response with error details if exception occurred
    """
    try:
        response = await call_next(request)
        return response
        
    except APIError as e:
        # Handle custom API errors
        logger.warning(
            f"API Error: {e.error_code} - {e.message}",
            extra={
                "error_code": e.error_code,
                "status_code": e.status_code,
                "path": request.url.path,
                "method": request.method,
                "details": e.details,
            },
        )
        
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": {
                    "code": e.error_code,
                    "message": e.message,
                    "details": e.details,
                },
            },
        )
    
    except opensearch_exceptions.NotFoundError as e:
        # Handle OpenSearch not found errors
        logger.warning(
            f"OpenSearch resource not found: {str(e)}",
            extra={
                "path": request.url.path,
                "method": request.method,
            },
        )
        
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Resource not found",
                    "details": {},
                },
            },
        )
    
    except opensearch_exceptions.ConflictError as e:
        # Handle OpenSearch conflict errors
        logger.warning(
            f"OpenSearch conflict: {str(e)}",
            extra={
                "path": request.url.path,
                "method": request.method,
            },
        )
        
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": "CONFLICT",
                    "message": "Resource conflict",
                    "details": {"opensearch_error": str(e)},
                },
            },
        )
    
    except opensearch_exceptions.ConnectionError as e:
        # Handle OpenSearch connection errors
        logger.error(
            f"OpenSearch connection error: {str(e)}",
            extra={
                "path": request.url.path,
                "method": request.method,
            },
        )
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Database connection error",
                    "details": {},
                },
            },
        )
    
    except opensearch_exceptions.RequestError as e:
        # Handle OpenSearch request errors
        logger.error(
            f"OpenSearch request error: {str(e)}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error": e.error,
            },
        )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "BAD_REQUEST",
                    "message": "Invalid request",
                    "details": {"opensearch_error": e.error},
                },
            },
        )
    
    except ValueError as e:
        # Handle value errors (typically validation)
        logger.warning(
            f"Value error: {str(e)}",
            extra={
                "path": request.url.path,
                "method": request.method,
            },
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(e),
                    "details": {},
                },
            },
        )
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(
            f"Unexpected error: {str(e)}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "traceback": traceback.format_exc(),
            },
            exc_info=True,
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {},
                },
            },
        )

# Made with Bob
