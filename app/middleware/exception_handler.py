"""
Global Exception Handler Middleware

Comprehensive error handling system that catches all exceptions and provides
meaningful error responses to the frontend instead of generic 500 errors.
"""

import logging
import traceback
import uuid
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError as PydanticValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import MannaException
from app.core.responses import ResponseFactory
from app.core.constants import HTTP_STATUS


class GlobalExceptionHandler(BaseHTTPMiddleware):
    """Global exception handler middleware for consistent error responses"""


    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Catch ALL exceptions, including MannaException
            if isinstance(exc, MannaException):
                pass
            return await self.handle_exception(request, exc, request_id)

    async def handle_exception(self, request: Request, exc: Exception, request_id: str) -> JSONResponse:
        """Handle different types of exceptions and return appropriate responses"""
        
        # Log the error for debugging
        self._log_exception(exc, request, request_id)
        
        # Handle MannaException (our custom exceptions) - this should catch UserExistsError
        if isinstance(exc, MannaException):
            return self._create_json_response(
                status_code=200,  # Always return 200 OK for consistency
                message=exc.message,
                error_code=exc.error_code or "MANNA_ERROR",
                details=exc.details,
                request_id=request_id,
                request=request
            )
        
        # Handle FastAPI HTTPException
        if isinstance(exc, HTTPException):
            return await self._handle_http_exception(exc, request_id, request)
        
        # Handle Pydantic validation errors
        if isinstance(exc, PydanticValidationError):
            return await self._handle_validation_exc(exc, request_id, request)
        
        # Handle SQLAlchemy database errors
        if isinstance(exc, SQLAlchemyError):
            return await self._handle_database_exc(exc, request_id, request)
        
        # Handle permission/authentication errors
        if isinstance(exc, PermissionError):
            return self._create_json_response(
                status_code=200,  # Always return 200 OK for consistency
                message="Insufficient permissions to access this resource",
                error_code="PERMISSION_DENIED",
                request_id=request_id
            )
        
        # Handle file not found errors
        if isinstance(exc, FileNotFoundError):
            return self._create_json_response(
                status_code=200,  # Always return 200 OK for consistency
                message="Requested file or resource not found",
                error_code="FILE_NOT_FOUND",
                request_id=request_id
            )
        
        # Handle value errors (often from invalid input)
        if isinstance(exc, ValueError):
            return self._create_json_response(
                status_code=200,  # Always return 200 OK for consistency
                message=f"Invalid input value: {str(exc)}",
                error_code="INVALID_VALUE",
                request_id=request_id
            )
        
        # Handle timeout errors
        if isinstance(exc, TimeoutError):
            return self._create_json_response(
                status_code=200,  # Always return 200 OK for consistency
                message="Request timed out. Please try again.",
                error_code="TIMEOUT_ERROR",
                request_id=request_id
            )
        
        # Handle all other unexpected errors
        return await self._handle_unexpected_exc(exc, request_id)

    async def _handle_http_exception(self, exc: HTTPException, request_id: str, request: Request) -> JSONResponse:
        """Handle FastAPI HTTPException with enhanced error details"""
        
        # Extract meaningful error information
        detail = exc.detail
        error_code = f"HTTP_{exc.status_code}"
        
        # Try to parse detail if it's a dict (from ResponseFactory errors)
        if isinstance(detail, dict):
            message = detail.get("message", "An error occurred")
            error_code = detail.get("error_code", error_code)
            details = detail.get("details")
        else:
            message = str(detail)
            details = None
        
        # For authentication errors, preserve the original status code
        if exc.status_code in [401, 403]:
            status_code = exc.status_code
        else:
            status_code = 200  # Return 200 OK for other errors for consistency
        
        return self._create_json_response(
            status_code=status_code,
            message=message,
            error_code=error_code,
            details=details,
            request_id=request_id,
            request=request
        )

    async def _handle_validation_exc(self, exc: PydanticValidationError, request_id: str, request: Request) -> JSONResponse:
        """Handle Pydantic validation errors with detailed field information"""
        
        validation_errors = []
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            validation_errors.append({
                "field": field_path,
                "message": error["msg"],
                "type": error["type"],
                "input": error.get("input")
            })
        
        return self._create_json_response(
            status_code=200,  # Always return 200 OK for consistency
            message="Request validation failed",
            error_code="VALIDATION_ERROR",
            details={"validation_errors": validation_errors},
            request_id=request_id,
            request=request
        )

    async def _handle_database_exc(self, exc: SQLAlchemyError, request_id: str, request: Request) -> JSONResponse:
        """Handle SQLAlchemy database errors with appropriate messages"""
        
        if isinstance(exc, IntegrityError):
            # Handle unique constraint violations
            error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
            
            if "UNIQUE constraint failed" in error_msg or "duplicate key" in error_msg.lower():
                return self._create_json_response(
                    status_code=200,  # Always return 200 OK for consistency
                    message="A record with this information already exists",
                    error_code="DUPLICATE_RECORD",
                    details={"database_error": "Unique constraint violation"},
                    request_id=request_id
                )
            elif "FOREIGN KEY constraint failed" in error_msg:
                return self._create_json_response(
                    status_code=200,  # Always return 200 OK for consistency
                    message="Referenced record does not exist",
                    error_code="INVALID_REFERENCE",
                    details={"database_error": "Foreign key constraint violation"},
                    request_id=request_id
                )
            elif "NOT NULL constraint failed" in error_msg:
                return self._create_json_response(
                    status_code=200,  # Always return 200 OK for consistency
                    message="Required field is missing",
                    error_code="MISSING_REQUIRED_FIELD",
                    details={"database_error": "Not null constraint violation"},
                    request_id=request_id
                )
        
        # Generic database error
        return self._create_json_response(
            status_code=200,  # Always return 200 OK for consistency
            message="Database operation failed. Please try again.",
            error_code="DATABASE_ERROR",
            details={"error_type": type(exc).__name__},
            request_id=request_id
        )

    async def _handle_unexpected_exc(self, exc: Exception, request_id: str) -> JSONResponse:
        """Handle unexpected exceptions with safe error messages"""
        
        # Return safe error message to client
        return self._create_json_response(
            status_code=200,  # Always return 200 OK for consistency
            message="An unexpected error occurred. Please try again later.",
            error_code="INTERNAL_ERROR",
            details={"error_type": type(exc).__name__},
            request_id=request_id
        )

    def _create_json_response(
        self,
        status_code: int,
        message: str,
        error_code: str,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        request: Optional[Request] = None
    ) -> JSONResponse:
        """Create standardized JSON error response with CORS headers"""
        
        error_response = ResponseFactory.error(
            message=message,
            error_code=error_code,
            details=details,
            request_id=request_id
        )
        
        # Add CORS headers for error responses
        headers = {}
        if request:
            origin = request.headers.get("origin", "*")
            headers.update({
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
                "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers, X-API-Key, X-Client-Version, User-Agent, Cache-Control, Pragma, Expires",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Max-Age": "86400"
            })
        
        # Serialize the response to ensure proper Content-Length calculation
        response_data = error_response.model_dump(mode='json')
        
        return JSONResponse(
            status_code=status_code,
            content=response_data,
            headers=headers
        )

    def _log_exception(self, exc: Exception, request: Request, request_id: str):
        """Log exception details for debugging"""
        
        # Extract request information
        method = request.method
        url = str(request.url)
        headers = dict(request.headers)
        
        # Remove sensitive headers
        sensitive_headers = ["authorization", "cookie", "x-api-key"]
        for header in sensitive_headers:
            if header in headers:
                headers[header] = "[REDACTED]"
        
        # Log error details
        error_context = {
            "request_id": request_id,
            "method": method,
            "url": url,
            "headers": headers,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)
        }
        
        if isinstance(exc, MannaException):
            pass
        elif isinstance(exc, HTTPException):
            pass
        else:
            pass


def setup_global_exception_handler(app):
    """Setup global exception handler for the FastAPI app"""
    
    # Add our custom middleware as a backup
    app.add_middleware(GlobalExceptionHandler)
    
    # Primary exception handlers for FastAPI - these should catch all exceptions
    @app.exception_handler(MannaException)
    async def manna_exception_handler(request: Request, exc: MannaException):
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Always return 200 OK with error details in response body
        # This ensures frontend gets consistent response format
        error_response = ResponseFactory.error(
            message=exc.message,
            error_code=exc.error_code,
            details=exc.details,
            request_id=request_id
        )
        
        # Serialize the response to ensure proper Content-Length calculation
        response_data = error_response.model_dump(mode='json')
        
        return JSONResponse(
            status_code=200,  # Always return 200 OK
            content=response_data
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Handle HTTPException detail format
        if isinstance(exc.detail, dict):
            message = exc.detail.get("message", "An error occurred")
            error_code = exc.detail.get("error_code", f"HTTP_{exc.status_code}")
            details = exc.detail.get("details")
        else:
            message = str(exc.detail)
            error_code = f"HTTP_{exc.status_code}"
            details = None
        
        error_response = ResponseFactory.error(
            message=message,
            error_code=error_code,
            details=details,
            request_id=request_id
        )
        
        # Serialize the response to ensure proper Content-Length calculation
        response_data = error_response.model_dump(mode='json')
        
        # Always return 200 OK with error details in response body
        return JSONResponse(
            status_code=200,  # Always return 200 OK
            content=response_data
        )
    
    @app.exception_handler(PydanticValidationError)
    async def validation_exception_handler(request: Request, exc: PydanticValidationError):
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        validation_errors = []
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            validation_errors.append({
                "field": field_path,
                "message": error["msg"],
                "type": error["type"]
            })
        
        error_response = ResponseFactory.error(
            message="Request validation failed",
            error_code="VALIDATION_ERROR",
            details={"validation_errors": validation_errors},
            request_id=request_id
        )
        
        # Serialize the response to ensure proper Content-Length calculation
        response_data = error_response.model_dump(mode='json')
        
        # Always return 200 OK with error details in response body
        return JSONResponse(
            status_code=200,  # Always return 200 OK
            content=response_data
        )

    # Add a catch-all exception handler for any other exceptions
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Check if it's a MannaException that wasn't caught by the specific handler
        if isinstance(exc, MannaException):
            error_response = ResponseFactory.error(
                message=exc.message,
                error_code=exc.error_code,
                details=exc.details,
                request_id=request_id
            )
            # Serialize the response to ensure proper Content-Length calculation
            response_data = error_response.model_dump(mode='json')
            
        return JSONResponse(
            status_code=200,  # Always return 200 OK
            content=response_data
        )
        
        # Handle any other exception
        error_response = ResponseFactory.error(
            message="An unexpected error occurred. Please try again later.",
            error_code="INTERNAL_ERROR",
            details={"error_type": type(exc).__name__},
            request_id=request_id
        )
        
        # Serialize the response to ensure proper Content-Length calculation
        response_data = error_response.model_dump(mode='json')
        
        # Always return 200 OK with error details in response body
        return JSONResponse(
            status_code=200,  # Always return 200 OK
            content=response_data
        )
