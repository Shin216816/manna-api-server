"""
Authentication Schemas

Defines request and response schemas for authentication endpoints:
- User registration and login
- Password management
- OAuth integration
- Token management
"""

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from app.schema.unified_schema import UserData
from app.core.responses import SuccessResponse

# ============================
# Request Payload Models
# ============================

class AuthRegisterRequest(BaseModel):
    """
    Request schema for user registration.
    """
    first_name: str = Field(..., min_length=1, max_length=50, description="User's first name")
    middle_name: Optional[str] = Field(None, max_length=50, description="User's middle name (optional)")
    last_name: Optional[str] = Field(None, max_length=50, description="User's last name (optional)")
    email: Optional[EmailStr] = Field(None, description="User's email address (optional)")
    phone: Optional[str] = Field(None, description="User's phone number (optional)")
    password: str = Field(..., min_length=8, description="User's password (must be at least 8 characters long)")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        # Convert empty string to None to avoid EmailStr validation error
        if v == "":
            return None
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        # Convert empty string to None
        if v == "":
            return None
        return v

    @field_validator('*', mode='before')
    @classmethod
    def check_email_or_phone_confirm(cls, values):
        if isinstance(values, dict):
            email = values.get('email')
            phone = values.get('phone')
            
            # Convert empty strings to None
            if email == "":
                values['email'] = None
            if phone == "":
                values['phone'] = None
                
            # Check if at least one is provided
            if not values.get('email') and not values.get('phone'):
                raise ValueError('Either email or phone must be provided.')
        return values

class AuthRegisterConfirmRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    access_code: str = Field(..., min_length=6, max_length=6, description="6-character alphanumeric verification code")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v == "":
            return None
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v == "":
            return None
        return v

    @field_validator('*', mode='before')
    @classmethod
    def check_email_or_phone_required(cls, values):
        if isinstance(values, dict):
            email = values.get('email')
            phone = values.get('phone')
            
            if email == "":
                values['email'] = None
            if phone == "":
                values['phone'] = None
                
            if not values.get('email') and not values.get('phone'):
                raise ValueError('Either email or phone must be provided.')
        return values

class AuthRegisterCodeResendRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v == "":
            return None
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v == "":
            return None
        return v

    @field_validator('*', mode='before')
    @classmethod
    def check_email_or_phone_required(cls, values):
        if isinstance(values, dict):
            email = values.get('email')
            phone = values.get('phone')
            
            if email == "":
                values['email'] = None
            if phone == "":
                values['phone'] = None
                
            if not values.get('email') and not values.get('phone'):
                raise ValueError('Either email or phone must be provided.')
        return values

class AuthLoginRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v == "":
            return None
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v == "":
            return None
        return v

    @field_validator('*', mode='before')
    @classmethod
    def check_email_or_phone_required(cls, values):
        if isinstance(values, dict):
            email = values.get('email')
            phone = values.get('phone')
            
            if email == "":
                values['email'] = None
            if phone == "":
                values['phone'] = None
                
            if not values.get('email') and not values.get('phone'):
                raise ValueError('Either email or phone must be provided.')
        return values

class AuthForgotPasswordRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v == "":
            return None
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v == "":
            return None
        return v

    @field_validator('*', mode='before')
    @classmethod
    def check_email_or_phone_required(cls, values):
        if isinstance(values, dict):
            email = values.get('email')
            phone = values.get('phone')
            
            if email == "":
                values['email'] = None
            if phone == "":
                values['phone'] = None
                
            if not values.get('email') and not values.get('phone'):
                raise ValueError('Either email or phone must be provided.')
        return values

class AuthVerifyOtpRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    access_code: str = Field(..., min_length=6, max_length=6, description="6-character alphanumeric verification code")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v == "":
            return None
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v == "":
            return None
        return v

    @field_validator('*', mode='before')
    @classmethod
    def check_email_or_phone_required(cls, values):
        if isinstance(values, dict):
            email = values.get('email')
            phone = values.get('phone')
            
            if email == "":
                values['email'] = None
            if phone == "":
                values['phone'] = None
                
            if not values.get('email') and not values.get('phone'):
                raise ValueError('Either email or phone must be provided.')
        return values

class AuthResetPasswordRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    access_code: str = Field(..., min_length=6, max_length=6, description="6-character alphanumeric verification code")
    new_password: str = Field(..., min_length=8, description="New password (must be at least 8 characters long)")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v == "":
            return None
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v == "":
            return None
        return v

    @field_validator('*', mode='before')
    @classmethod
    def check_email_or_phone_required(cls, values):
        if isinstance(values, dict):
            email = values.get('email')
            phone = values.get('phone')
            
            if email == "":
                values['email'] = None
            if phone == "":
                values['phone'] = None
                
            if not values.get('email') and not values.get('phone'):
                raise ValueError('Either email or phone must be provided.')
        return values

class AuthChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (must be at least 8 characters long)")
    confirm_password: str = Field(..., min_length=8, description="Confirm new password")

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v

class SetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="Password (must be at least 8 characters long)")
    confirm_password: str = Field(..., min_length=8, description="Confirm password")

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v

class UserProfileUpdateRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="User's first name")
    middle_name: Optional[str] = Field(None, max_length=50, description="User's middle name")
    last_name: Optional[str] = Field(None, max_length=50, description="User's last name")
    email: Optional[EmailStr] = Field(None, description="User's email address")
    phone: Optional[str] = Field(None, description="User's phone number")
    church_id: Optional[int] = Field(None, description="Church ID to associate with user")

    @field_validator('first_name')
    @classmethod
    def validate_first_name(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('First name cannot be empty')
        return v.strip() if v else v

    @field_validator('middle_name')
    @classmethod
    def validate_middle_name(cls, v):
        return v.strip() if v else v

    @field_validator('last_name')
    @classmethod
    def validate_last_name(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('Last name cannot be empty')
        return v.strip() if v else v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('Email cannot be empty')
        return v.strip() if v else v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is not None:
            cleaned = v.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
            if not cleaned.isdigit():
                raise ValueError('Phone number must contain only digits, spaces, hyphens, parentheses, and plus sign.')
            if len(cleaned) < 10:
                raise ValueError('Phone number must be at least 10 digits long.')
        return v

    @field_validator('church_id')
    @classmethod
    def validate_church_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Church ID must be a positive integer.')
        return v

    @classmethod
    def check_at_least_one_field(cls, values):
        if not any([
            values.get('first_name') is not None,
            values.get('middle_name') is not None,
            values.get('last_name') is not None,
            values.get('email') is not None,
            values.get('phone') is not None,
            values.get('church_id') is not None,
        ]):
            raise ValueError('At least one field must be provided for update')
        return values

class AuthLogoutRequest(BaseModel):
    token: Optional[str] = None
    refresh_token: Optional[str] = None

class GoogleOAuthRequest(BaseModel):
    id_token: str = Field(..., description="Google ID token from mobile app")

class AppleOAuthRequest(BaseModel):
    auth_code: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# ============================
# JWT Token Models
# ============================

class AuthJWTToken(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

# ============================
# Response Payload Models
# ============================

class RegisterData(BaseModel):
    user_id: int
    access_code: str = Field(..., description="6-character alphanumeric verification code")
    email: Optional[str] = None
    phone: Optional[str] = None
    expires_at: datetime
    message: str = "Please check your email/phone for verification code"

class AccessCodeData(BaseModel):
    access_code: str = Field(..., description="6-character alphanumeric verification code")
    expires_at: datetime
    message: str = "Access code sent successfully"

class PasswordResetData(BaseModel):
    message: str = "Password reset instructions sent"
    expires_at: Optional[datetime] = None
    access_code: Optional[str] = Field(None, description="6-character alphanumeric verification code")

class LogoutData(BaseModel):
    message: str = "Logout successful"
    tokens_revoked: int = 0

class EmptyData(BaseModel):
    pass

# ============================
# Response Schemas
# ============================

class AuthRegisterResponse(SuccessResponse):
    data: Optional[RegisterData] = None

class AuthLoginResponse(SuccessResponse):
    data: Optional[Dict[str, Any]] = None  # Contains AuthTokenResponse and UserData

class AuthForgotPasswordResponse(SuccessResponse):
    data: Optional[PasswordResetData] = None

class AuthVerifyOtpResponse(SuccessResponse):
    data: Optional[EmptyData] = None

class AuthResetPasswordResponse(SuccessResponse):
    data: Optional[EmptyData] = None

class AuthChangePasswordResponse(SuccessResponse):
    data: Optional[EmptyData] = None

class SetPasswordResponse(SuccessResponse):
    data: Optional[EmptyData] = None

class AuthLogoutResponse(SuccessResponse):
    data: Optional[LogoutData] = None

class AuthRegisterConfirmResponse(SuccessResponse):
    data: Optional[Dict[str, Any]] = None  # Contains AuthTokenResponse and UserData

class AuthRegisterCodeResendResponse(SuccessResponse):
    data: Optional[AccessCodeData] = None

class GoogleOAuthResponse(SuccessResponse):
    data: Optional[Dict[str, Any]] = None  # Contains AuthTokenResponse and UserData

class AppleOAuthResponse(SuccessResponse):
    data: Optional[Dict[str, Any]] = None  # Contains AuthTokenResponse and UserData

class RefreshTokenResponse(SuccessResponse):
    data: Optional[Dict[str, Any]] = None  # Contains AuthJWTToken in tokens wrapper

class MeResponse(SuccessResponse):
    data: Optional[UserData] = None

class UserChurchUpdateResponse(SuccessResponse):
    data: Optional[Dict[str, Any]] = None

class UserChurchInfoResponse(SuccessResponse):
    data: Optional[Dict[str, Any]] = None

class UserProfileUpdateResponse(SuccessResponse):
    data: Optional[Dict[str, Any]] = None
