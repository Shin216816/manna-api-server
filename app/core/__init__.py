"""
Core components for the Manna Backend API.

This package contains core application components:
- Response models and factories
- Message management
- Constants and configuration
- Core business logic
"""

# Response models
from app.core.responses import (
    BaseResponse,
    SuccessResponse,
    ErrorResponse,
    PaginatedResponse,
    AuthTokenResponse,
    AuthResponse,
    ResponseFactory,
    create_success_response,
    create_error_response,
    create_auth_response
)

# Message management
from app.core.messages import (
    get_auth_message,
    get_bank_message,
    get_church_message,
    get_admin_message
)

# Constants
from app.core.constants import (
    AUTH_CONSTANTS,
    BUSINESS_CONSTANTS,
    FILE_CONSTANTS,
    RATE_LIMIT_CONSTANTS,
    DATABASE_CONSTANTS,
    EMAIL_CONSTANTS,
    PAYMENT_CONSTANTS,
    NOTIFICATION_CONSTANTS,
    get_auth_constant,
    get_business_constant,
    get_file_constant,
    get_rate_limit_constant,
    get_database_constant,
    get_email_constant,
    get_payment_constant,
    get_notification_constant
)

# Main exports
__all__ = [
    # Response models
    "BaseResponse",
    "SuccessResponse",
    "ErrorResponse", 
    "PaginatedResponse",
    "AuthTokenResponse",
    "AuthResponse",
    "ResponseFactory",
    "create_success_response",
    "create_error_response",
    "create_auth_response",
    
    # Message management
    "get_auth_message",
    "get_bank_message",
    "get_church_message",
    "get_admin_message",
    
    # Constants
    "AUTH_CONSTANTS",
    "BUSINESS_CONSTANTS",
    "FILE_CONSTANTS",
    "RATE_LIMIT_CONSTANTS",
    "DATABASE_CONSTANTS",
    "EMAIL_CONSTANTS",
    "PAYMENT_CONSTANTS",
    "NOTIFICATION_CONSTANTS",
    "get_auth_constant",
    "get_business_constant",
    "get_file_constant",
    "get_rate_limit_constant",
    "get_database_constant",
    "get_email_constant",
    "get_payment_constant",
    "get_notification_constant"
] 
