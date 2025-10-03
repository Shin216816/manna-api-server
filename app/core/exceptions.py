"""
Unified exception handling system for consistent error management.
Eliminates code duplication and provides standardized error handling patterns.
"""

from typing import Any, Optional, Dict
from fastapi import HTTPException, status
from app.core.constants import ERROR_MESSAGES, HTTP_STATUS


class MannaException(Exception):
    """Base exception for all Manna application errors"""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(MannaException):
    """Authentication related errors"""
    
    def __init__(
        self, 
        message: str = ERROR_MESSAGES["AUTH_TOKEN_INVALID"],
        error_code: str = "AUTH_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=HTTP_STATUS["UNAUTHORIZED"],
            error_code=error_code,
            details=details
        )


class AuthorizationError(MannaException):
    """Authorization related errors"""
    
    def __init__(
        self, 
        message: str = ERROR_MESSAGES["AUTH_ROLE_FORBIDDEN"],
        error_code: str = "FORBIDDEN",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=HTTP_STATUS["FORBIDDEN"],
            error_code=error_code,
            details=details
        )


class ValidationError(MannaException):
    """Validation related errors"""
    
    def __init__(
        self, 
        message: str = "Validation failed",
        error_code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=HTTP_STATUS["BAD_REQUEST"],
            error_code=error_code,
            details=details
        )


class RoundupError(ValidationError):
    """Round-up processing errors"""
    
    def __init__(
        self, 
        message: str = "Round-up processing failed",
        error_code: str = "ROUNDUP_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details
        )


class NotFoundError(MannaException):
    """Resource not found errors"""
    
    def __init__(
        self, 
        resource: str = "Resource",
        error_code: str = "NOT_FOUND",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"{resource} not found",
            status_code=HTTP_STATUS["NOT_FOUND"],
            error_code=error_code,
            details=details
        )


class ConflictError(MannaException):
    """Resource conflict errors"""
    
    def __init__(
        self, 
        message: str = "Resource conflict",
        error_code: str = "CONFLICT",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=HTTP_STATUS["CONFLICT"],
            error_code=error_code,
            details=details
        )


class DatabaseError(MannaException):
    """Database related errors"""
    
    def __init__(
        self, 
        message: str = ERROR_MESSAGES["DB_ERROR"],
        error_code: str = "DATABASE_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            error_code=error_code,
            details=details
        )


class ExternalServiceError(MannaException):
    """External service integration errors"""
    
    def __init__(
        self, 
        service: str,
        message: str = "External service error",
        error_code: str = "EXTERNAL_SERVICE_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"{service}: {message}",
            status_code=HTTP_STATUS["SERVICE_UNAVAILABLE"],
            error_code=error_code,
            details=details
        )


class RateLimitError(MannaException):
    """Rate limiting errors"""
    
    def __init__(
        self, 
        message: str = "Rate limit exceeded",
        error_code: str = "RATE_LIMIT_EXCEEDED",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=HTTP_STATUS["TOO_MANY_REQUESTS"],
            error_code=error_code,
            details=details
        )


# Specific business logic exceptions
class UserNotFoundError(NotFoundError):
    """User not found error"""
    
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            resource="User",
            error_code="USER_NOT_FOUND",
            details=details
        )


class UserExistsError(ConflictError):
    """User already exists error"""
    
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=ERROR_MESSAGES["USER_REGISTER_EXISTS"],
            error_code="USER_EXISTS",
            details=details
        )


class InvalidCredentialsError(AuthenticationError):
    """Invalid credentials error"""
    
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=ERROR_MESSAGES["AUTH_LOGIN_FAILED"],
            error_code="INVALID_CREDENTIALS",
            details=details
        )


class TokenExpiredError(AuthenticationError):
    """Token expired error"""
    
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=ERROR_MESSAGES["AUTH_TOKEN_INVALID"],
            error_code="TOKEN_EXPIRED",
            details=details
        )


class AccessCodeError(ValidationError):
    """Access code related errors"""
    
    def __init__(
        self, 
        message: str = ERROR_MESSAGES["ACCESS_CODE_INVALID"],
        error_code: str = "ACCESS_CODE_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details
        )


class ChurchNotFoundError(NotFoundError):
    """Church not found error"""
    
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            resource="Church",
            error_code="CHURCH_NOT_FOUND",
            details=details
        )


class PaymentError(ExternalServiceError):
    """Payment processing errors"""
    
    def __init__(
        self, 
        message: str = ERROR_MESSAGES["PAYMENT_FAILED"],
        error_code: str = "PAYMENT_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            service="Payment",
            message=message,
            error_code=error_code,
            details=details
        )


class PlaidError(ExternalServiceError):
    """Plaid integration errors"""
    
    def __init__(
        self, 
        message: str = "Plaid service error",
        error_code: str = "PLAID_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            service="Plaid",
            message=message,
            error_code=error_code,
            details=details
        )


class EmailError(ExternalServiceError):
    """Email service errors"""
    
    def __init__(
        self, 
        message: str = ERROR_MESSAGES["EMAIL_SEND_FAILED"],
        error_code: str = "EMAIL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            service="Email",
            message=message,
            error_code=error_code,
            details=details
        )


class StripeError(ExternalServiceError):
    """Stripe payment service errors"""
    
    def __init__(
        self, 
        message: str = "Stripe payment processing error",
        error_code: str = "STRIPE_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            service="Stripe",
            message=message,
            error_code=error_code,
            details=details
        )


class SMSError(ExternalServiceError):
    """SMS service errors"""
    
    def __init__(
        self, 
        message: str = "SMS sending failed",
        error_code: str = "SMS_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            service="SMS",
            message=message,
            error_code=error_code,
            details=details
        )


class FileUploadError(ValidationError):
    """File upload related errors"""
    
    def __init__(
        self, 
        message: str = "File upload failed",
        error_code: str = "FILE_UPLOAD_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details
        )


class KYCError(ValidationError):
    """KYC validation errors"""
    
    def __init__(
        self, 
        message: str = "KYC validation failed",
        error_code: str = "KYC_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details
        )


class BankAccountError(ExternalServiceError):
    """Bank account related errors"""
    
    def __init__(
        self, 
        message: str = "Bank account operation failed",
        error_code: str = "BANK_ACCOUNT_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            service="Banking",
            message=message,
            error_code=error_code,
            details=details
        )


class DonationError(ValidationError):
    """Donation processing errors"""
    
    def __init__(
        self, 
        message: str = "Donation processing failed",
        error_code: str = "DONATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details
        )


class ReferralError(ValidationError):
    """Referral system errors"""
    
    def __init__(
        self, 
        message: str = "Referral operation failed",
        error_code: str = "REFERRAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details
        )


# Exception handler utilities
def handle_exception(func):
    """Decorator to handle exceptions and convert them to HTTPException"""
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MannaException as e:
            raise HTTPException(
                status_code=e.status_code,
                detail={
                    "success": False,
                    "message": e.message,
                    "error_code": e.error_code,
                    "details": e.details
                }
            )
        except Exception as e:
            # Log unexpected errors
            import logging
            raise HTTPException(
                status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
                detail={
                    "success": False,
                    "message": "Internal server error",
                    "error_code": "INTERNAL_ERROR",
                    "details": {"error": str(e)}
                }
            )
    
    return wrapper


def raise_if_not_found(resource, condition: bool, resource_name: str = "Resource"):
    """Raise NotFoundError if condition is False"""
    if not condition:
        raise NotFoundError(resource=resource_name)


def raise_if_exists(resource, condition: bool, resource_name: str = "Resource"):
    """Raise ConflictError if condition is True"""
    if condition:
        raise ConflictError(message=f"{resource_name} already exists")


def raise_if_invalid(condition: bool, message: str, error_code: str = "VALIDATION_ERROR"):
    """Raise ValidationError if condition is False"""
    if not condition:
        raise ValidationError(message=message, error_code=error_code) 
