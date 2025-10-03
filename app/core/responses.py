"""
Unified response system for consistent API responses across the application.
Eliminates code duplication and provides standardized response formats.
"""

from typing import Any, Optional, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from app.core.constants import get_auth_constant, get_business_constant


class BaseResponse(BaseModel):
    """Base response model for all API responses"""
    success: bool = Field(..., description="Indicates if the operation was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(default=None, description="Response data")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Response timestamp")
    request_id: Optional[str] = Field(default=None, description="Unique request identifier")


class SuccessResponse(BaseResponse):
    """Standard success response"""
    success: bool = Field(default=True, description="Always true for success responses")
    
    @classmethod
    def create(
        cls, 
        message: str, 
        data: Any = None, 
        request_id: Optional[str] = None
    ) -> "SuccessResponse":
        """Create a success response with standardized message"""
        return cls(
            success=True,
            message=message,
            data=data,
            request_id=request_id
        )


class ErrorResponse(BaseResponse):
    """Standard error response"""
    success: bool = Field(default=False, description="Always false for error responses")
    error_code: Optional[str] = Field(default=None, description="Error code for client handling")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    
    @classmethod
    def create(
        cls, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> "ErrorResponse":
        """Create an error response with standardized message"""
        return cls(
            success=False,
            message=message,
            error_code=error_code,
            details=details,
            request_id=request_id
        )


class PaginatedResponse(BaseResponse):
    """Paginated response for list endpoints"""
    success: bool = Field(default=True)
    pagination: Dict[str, Any] = Field(..., description="Pagination metadata")
    
    @classmethod
    def create(
        cls,
        data: List[Any],
        page: int,
        page_size: int,
        total: int,
        message: str = "Data retrieved successfully",
        request_id: Optional[str] = None
    ) -> "PaginatedResponse":
        """Create a paginated response"""
        total_pages = (total + page_size - 1) // page_size
        
        pagination = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
        return cls(
            success=True,
            message=message,
            data=data,
            pagination=pagination,
            request_id=request_id
        )


class AuthTokenResponse(BaseModel):
    """Authentication token response"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class AuthResponse(SuccessResponse):
    """Authentication response with tokens"""
    data: Optional[AuthTokenResponse] = Field(None, description="Authentication tokens")


# Response factory functions for common operations
class ResponseFactory:
    """Factory class for creating standardized responses"""
    
    @staticmethod
    def success(
        message: str, 
        data: Any = None, 
        request_id: Optional[str] = None
    ) -> SuccessResponse:
        """Create a success response"""
        return SuccessResponse.create(message, data, request_id)
    
    @staticmethod
    def error(
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Create an error response"""
        return ErrorResponse.create(message, error_code, details, request_id)
    
    @staticmethod
    def auth_success(
        access_token: str,
        refresh_token: str,
        expires_in: int,
        request_id: Optional[str] = None
    ) -> AuthResponse:
        """Create an authentication success response"""
        token_data = AuthTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in
        )
        return AuthResponse(
            success=True,
            message="Authentication successful",
            data=token_data,
            request_id=request_id
        )
    
    @staticmethod
    def paginated(
        data: List[Any],
        page: int,
        page_size: int,
        total: int,
        message: str = "Data retrieved successfully",
        request_id: Optional[str] = None
    ) -> PaginatedResponse:
        """Create a paginated response"""
        return PaginatedResponse.create(data, page, page_size, total, message, request_id)
    
    @staticmethod
    def not_found(
        resource: str = "Resource",
        request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Create a not found error response"""
        return ErrorResponse.create(
            message=f"{resource} not found",
            error_code="NOT_FOUND",
            request_id=request_id
        )
    
    @staticmethod
    def validation_error(
        details: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Create a validation error response"""
        return ErrorResponse.create(
            message="Validation failed",
            error_code="VALIDATION_ERROR",
            details=details,
            request_id=request_id
        )
    
    @staticmethod
    def unauthorized(
        message: str = "Invalid or expired token",
        request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Create an unauthorized error response"""
        return ErrorResponse.create(
            message=message,
            error_code="UNAUTHORIZED",
            request_id=request_id
        )
    
    @staticmethod
    def forbidden(
        message: str = "Insufficient permissions",
        request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Create a forbidden error response"""
        return ErrorResponse.create(
            message=message,
            error_code="FORBIDDEN",
            request_id=request_id
        )
    
    @staticmethod
    def server_error(
        message: str = "Internal server error",
        request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Create a server error response"""
        return ErrorResponse.create(
            message=message,
            error_code="INTERNAL_SERVER_ERROR",
            request_id=request_id
        )

    @staticmethod
    def auth_error(
        message: str = "Authentication failed",
        error_code: str = "AUTH_ERROR",
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Create an authentication error response"""
        return ErrorResponse.create(
            message=message,
            error_code=error_code,
            details=details,
            request_id=request_id
        )

    @staticmethod
    def otp_error(
        message: str = "OTP verification failed",
        error_code: str = "OTP_ERROR",
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Create an OTP verification error response"""
        return ErrorResponse.create(
            message=message,
            error_code=error_code,
            details=details,
            request_id=request_id
        )

    @staticmethod
    def church_error(
        message: str = "Church operation failed",
        error_code: str = "CHURCH_ERROR",
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Create a church-related error response"""
        return ErrorResponse.create(
            message=message,
            error_code=error_code,
            details=details,
            request_id=request_id
        )

    @staticmethod
    def user_error(
        message: str = "User operation failed",
        error_code: str = "USER_ERROR",
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Create a user-related error response"""
        return ErrorResponse.create(
            message=message,
            error_code=error_code,
            details=details,
            request_id=request_id
        )
    
    @staticmethod
    def database_error(
        message: str = "Database operation failed",
        request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Create a database error response"""
        return ErrorResponse.create(
            message=message,
            error_code="DATABASE_ERROR",
            request_id=request_id
        )
    
    @staticmethod
    def external_service_error(
        service: str,
        message: str = "External service error",
        request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Create an external service error response"""
        return ErrorResponse.create(
            message=f"{service}: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service},
            request_id=request_id
        )
    
    @staticmethod
    def payment_error(
        message: str = "Payment processing failed",
        request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Create a payment error response"""
        return ErrorResponse.create(
            message=message,
            error_code="PAYMENT_ERROR",
            request_id=request_id
        )
    
    @staticmethod
    def file_upload_error(
        message: str = "File upload failed",
        request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Create a file upload error response"""
        return ErrorResponse.create(
            message=message,
            error_code="FILE_UPLOAD_ERROR",
            request_id=request_id
        )
    
    @staticmethod
    def rate_limit_error(
        message: str = "Rate limit exceeded",
        request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Create a rate limit error response"""
        return ErrorResponse.create(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            request_id=request_id
        )
    
    @staticmethod
    def timeout_error(
        message: str = "Request timed out",
        request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Create a timeout error response"""
        return ErrorResponse.create(
            message=message,
            error_code="TIMEOUT_ERROR",
            request_id=request_id
        )


# Convenience functions for common responses
def create_success_response(
    message: str, 
    data: Any = None, 
    request_id: Optional[str] = None
) -> SuccessResponse:
    """Create a success response"""
    return ResponseFactory.success(message, data, request_id)


def create_error_response(
    message: str, 
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> ErrorResponse:
    """Create an error response"""
    return ResponseFactory.error(message, error_code, details, request_id)


def create_auth_response(
    access_token: str,
    refresh_token: str,
    expires_in: int,
    request_id: Optional[str] = None
) -> AuthResponse:
    """Create an authentication response"""
    return ResponseFactory.auth_success(access_token, refresh_token, expires_in, request_id) 
