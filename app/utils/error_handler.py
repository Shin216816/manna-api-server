"""
Error handling utilities for controllers

Provides decorators and utilities to standardize error handling across controllers
and ensure consistent error responses to the frontend.
"""

import logging
import traceback
from functools import wraps
from typing import Callable, Any, Optional, Dict
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    MannaException, DatabaseError, ValidationError, 
    UserExistsError, UserNotFoundError, InvalidCredentialsError,
    StripeError, PlaidError, EmailError, SMSError, 
    BankAccountError, DonationError, ReferralError
)
from app.core.responses import ResponseFactory


def handle_controller_errors(func: Callable) -> Callable:
    """
    Decorator to handle common controller errors and convert them to appropriate exceptions
    
    This decorator catches common exceptions in controllers and converts them to
    proper MannaException instances that the global exception handler can process.
    """
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        
        except MannaException:
            # Re-raise our custom exceptions as-is
            raise
        
        except SQLAlchemyError as e:
            
            if isinstance(e, IntegrityError):
                error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
                
                if "UNIQUE constraint failed" in error_msg or "duplicate key" in error_msg.lower():
                    if "email" in error_msg.lower():
                        raise UserExistsError(details={"field": "email"})
                    elif "phone" in error_msg.lower():
                        raise UserExistsError(details={"field": "phone"})
                    else:
                        raise ValidationError(
                            message="A record with this information already exists",
                            error_code="DUPLICATE_RECORD"
                        )
                
                elif "FOREIGN KEY constraint failed" in error_msg:
                    raise ValidationError(
                        message="Referenced record does not exist",
                        error_code="INVALID_REFERENCE"
                    )
                
                elif "NOT NULL constraint failed" in error_msg:
                    # Extract field name from error message
                    field_name = "field"
                    if "." in error_msg:
                        try:
                            field_name = error_msg.split(".")[-1].split()[0]
                        except:
                            pass
                    
                    raise ValidationError(
                        message=f"Required field '{field_name}' is missing",
                        error_code="MISSING_REQUIRED_FIELD",
                        details={"field": field_name}
                    )
            
            # Generic database error
            raise DatabaseError(
                message="Database operation failed. Please try again.",
                details={"error_type": type(e).__name__}
            )
        
        except ValueError as e:
            raise ValidationError(
                message=f"Invalid input value: {str(e)}",
                error_code="INVALID_VALUE"
            )
        
        except PermissionError as e:
            raise ValidationError(
                message="Insufficient permissions to perform this action",
                error_code="PERMISSION_DENIED"
            )
        
        except FileNotFoundError as e:
            raise ValidationError(
                message="Requested file or resource not found",
                error_code="FILE_NOT_FOUND"
            )
        
        except Exception as e:
            # Log unexpected errors with full traceback
            logging.error(f"Unexpected error in {func.__name__}: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            
            # Check for specific service errors in the exception message
            error_msg = str(e).lower()
            
            if "stripe" in error_msg:
                raise StripeError(
                    message=f"Payment processing error: {str(e)}",
                    details={"original_error": str(e), "function": func.__name__}
                )
            
            elif "plaid" in error_msg:
                raise PlaidError(
                    message=f"Banking service error: {str(e)}",
                    details={"original_error": str(e), "function": func.__name__}
                )
            
            elif "email" in error_msg and ("send" in error_msg or "smtp" in error_msg):
                raise EmailError(
                    message=f"Email service error: {str(e)}",
                    details={"original_error": str(e), "function": func.__name__}
                )
            
            elif "sms" in error_msg or "twilio" in error_msg:
                raise SMSError(
                    message=f"SMS service error: {str(e)}",
                    details={"original_error": str(e), "function": func.__name__}
                )
            
            elif "connection" in error_msg:
                raise MannaException(
                    message="Connection error. Please refresh the page.",
                    error_code="CONNECTION_ERROR",
                    details={"original_error": str(e), "function": func.__name__}
                )
            
            elif "kyc" in error_msg or "compliance" in error_msg:
                raise MannaException(
                    message="Compliance verification error. Please check your information and try again.",
                    error_code="KYC_ERROR",
                    details={"original_error": str(e), "function": func.__name__}
                )
            
            elif "referral" in error_msg:
                raise ReferralError(
                    message=f"Referral system error: {str(e)}",
                    details={"original_error": str(e), "function": func.__name__}
                )
            
            # Re-raise as generic internal error
            raise MannaException(
                message="An unexpected error occurred. Please try again later.",
                error_code="INTERNAL_ERROR",
                details={"error_type": type(e).__name__, "function": func.__name__}
            )
    
    return wrapper


def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """
    Validate that required fields are present and not empty
    
    Args:
        data: Dictionary containing the data to validate
        required_fields: List of field names that are required
        
    Raises:
        ValidationError: If any required field is missing or empty
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(
            message=f"Required fields are missing: {', '.join(missing_fields)}",
            error_code="MISSING_REQUIRED_FIELDS",
            details={"missing_fields": missing_fields}
        )


def validate_user_exists(user: Optional[Any], user_identifier: str = "User") -> None:
    """
    Validate that a user exists, raise UserNotFoundError if not
    
    Args:
        user: User object or None
        user_identifier: Description of the user for error message
        
    Raises:
        UserNotFoundError: If user is None
    """
    if not user:
        raise UserNotFoundError(details={"identifier": user_identifier})


def validate_user_permissions(user: Dict[str, Any], required_role: Optional[str] = None) -> None:
    """
    Validate user permissions
    
    Args:
        user: User data dictionary
        required_role: Required role for the operation
        
    Raises:
        ValidationError: If user doesn't have required permissions
    """
    if not user:
        raise ValidationError(
            message="Authentication required",
            error_code="AUTHENTICATION_REQUIRED"
        )
    
    if required_role and user.get('role') != required_role:
        raise ValidationError(
            message=f"Required role '{required_role}' not found",
            error_code="INSUFFICIENT_PERMISSIONS",
            details={"required_role": required_role, "user_role": user.get('role')}
        )


def handle_db_session_errors(db: Session) -> Callable:
    """
    Decorator to handle database session errors
    
    Ensures proper session cleanup and error handling for database operations
    """
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result
            
            except Exception as e:
                # Rollback the transaction on any error
                try:
                    db.rollback()
                except:
                    pass  # If rollback fails, we can't do much
                
                # Re-raise the exception to be handled by other decorators
                raise
        
        return wrapper
    return decorator


def handle_service_errors(func: Callable) -> Callable:
    """
    Decorator to handle service-level errors with enhanced logging and error context
    
    This decorator is specifically designed for service functions and provides
    better error context and logging for debugging.
    """
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        
        except MannaException:
            # Re-raise our custom exceptions as-is
            raise
        
        except SQLAlchemyError as e:
            logging.error(f"Database error in service {func.__name__}: {str(e)}")
            raise DatabaseError(
                message="Database operation failed in service",
                details={"service": func.__name__, "error_type": type(e).__name__}
            )
        
        except Exception as e:
            # Enhanced logging for service errors
            logging.error(f"Service error in {func.__name__}: {str(e)}")
            logging.error(f"Service traceback: {traceback.format_exc()}")
            
            # Check for specific service errors
            error_msg = str(e).lower()
            
            if "stripe" in error_msg:
                raise StripeError(
                    message=f"Payment service error: {str(e)}",
                    details={"service": func.__name__, "original_error": str(e)}
                )
            
            elif "plaid" in error_msg:
                raise PlaidError(
                    message=f"Banking service error: {str(e)}",
                    details={"service": func.__name__, "original_error": str(e)}
                )
            
            elif "service" in error_msg:
                raise MannaException(
                    message="Service error. Please try again.",
                    error_code="SERVICE_ERROR",
                    details={"service": func.__name__, "original_error": str(e)}
                )
            
            # Re-raise as service error
            raise MannaException(
                message="Service operation failed. Please try again later.",
                error_code="SERVICE_ERROR",
                details={"service": func.__name__, "error_type": type(e).__name__}
            )
    
    return wrapper


# Convenience functions for common validation patterns
def require_email_or_phone(email: Optional[str], phone: Optional[str]) -> None:
    """Validate that either email or phone is provided"""
    if not email and not phone:
        raise ValidationError(
            message="Either email or phone number is required",
            error_code="EMAIL_OR_PHONE_REQUIRED"
        )


def require_authentication(current_user: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate that user is authenticated"""
    if not current_user:
        raise ValidationError(
            message="Authentication required",
            error_code="AUTHENTICATION_REQUIRED"
        )
    return current_user


def safe_get_user_id(current_user: Dict[str, Any]) -> int:
    """Safely extract user ID from current_user"""
    user_id = current_user.get('id')
    if not user_id:
        raise ValidationError(
            message="Invalid user token - user ID not found",
            error_code="INVALID_USER_TOKEN"
        )
    return user_id


# Example usage patterns for controllers:
"""
# Basic error handling
@handle_controller_errors
def my_controller_function(data, current_user, db):
    # Your controller logic here
    pass

# With database session handling
@handle_controller_errors
@handle_db_session_errors(db)
def my_db_controller_function(data, current_user, db):
    # Your database operations here
    pass

# With validation
@handle_controller_errors
def register_user(data, db):
    validate_required_fields(data.dict(), ['email', 'password', 'first_name'])
    require_email_or_phone(data.email, data.phone)
    # Rest of the logic
"""
