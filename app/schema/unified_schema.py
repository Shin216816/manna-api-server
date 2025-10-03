"""
Unified schema system for all API requests and responses.
Eliminates code duplication and provides consistent schema definitions.
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from datetime import datetime
from app.core.responses import BaseResponse, SuccessResponse, ErrorResponse, AuthTokenResponse


# ============================
# Base Request Schemas
# ============================

class BaseRequest(BaseModel):
    """Base request model with common validation"""
    model_config = ConfigDict(extra="forbid")


class PaginationRequest(BaseRequest):
    """Base pagination request"""
    page: int = 1
    page_size: int = 10


# ============================
# Authentication Schemas
# ============================

class AuthRegisterRequest(BaseRequest):
    """User registration request"""
    first_name: str = Field(..., min_length=1, max_length=50, description="User's first name")
    middle_name: Optional[str] = Field(None, max_length=50, description="User's middle name")
    last_name: Optional[str] = Field(None, max_length=50, description="User's last name")
    email: Optional[EmailStr] = Field(None, description="User's email address")
    password: str = Field(..., min_length=8, description="User's password (must be at least 8 characters long)")
    
    @field_validator('email')
    @staticmethod
    def email_or_phone_required(v, values):
        if not v and not values.get('phone'):
            raise ValueError('Either email or phone must be provided.')
        return v


class AuthLoginRequest(BaseRequest):
    """User login request"""
    email: Optional[EmailStr] = Field(None, description="User's email address")
    password: str = Field(..., description="User's password")


class AuthRegisterConfirmRequest(BaseRequest):
    """Registration confirmation request"""
    email: Optional[EmailStr] = Field(None, description="User's email address")
    phone: Optional[str] = Field(None, description="User's phone number")
    access_code: str = Field(..., min_length=6, max_length=6, description="6-character alphanumeric verification code")


class AuthRegisterCodeResendRequest(BaseRequest):
    """Access code resend request"""
    email: Optional[EmailStr] = Field(None, description="User's email address")
    phone: Optional[str] = Field(None, description="User's phone number")


class AuthForgotPasswordRequest(BaseRequest):
    """Forgot password request"""
    email: Optional[EmailStr] = Field(None, description="User's email address")


class AuthResetPasswordRequest(BaseRequest):
    """Password reset request"""
    email: Optional[EmailStr] = Field(None, description="User's email address")
    access_code: str = Field(..., min_length=6, max_length=6, description="6-character alphanumeric verification code")
    new_password: str = Field(..., min_length=8, description="New password (must be at least 8 characters long)")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @field_validator('confirm_password')
    @staticmethod
    def passwords_match(v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class AuthChangePasswordRequest(BaseRequest):
    """Password change request"""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (must be at least 8 characters long)")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @field_validator('confirm_password')
    @staticmethod
    def passwords_match(v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class AuthLogoutRequest(BaseRequest):
    """Logout request"""
    token: Optional[str] = Field(None, description="Access token to revoke")
    refresh_token: Optional[str] = Field(None, description="Refresh token to revoke")


class GoogleOAuthRequest(BaseRequest):
    """Google OAuth request"""
    auth_code: str = Field(..., description="Google authorization code")


class AppleOAuthRequest(BaseRequest):
    """Apple OAuth request"""
    auth_code: str = Field(..., description="Apple authorization code")


class RefreshTokenRequest(BaseRequest):
    """Token refresh request"""
    refresh_token: str = Field(..., description="Refresh token")


# ============================
# Bank & Payment Schemas
# ============================

class PlaidLinkTokenRequest(BaseRequest):
    """Plaid link token request"""
    user_id: str = Field(..., description="User ID for Plaid link")


class PlaidExchangeTokenRequest(BaseRequest):
    """Plaid token exchange request"""
    public_token: str = Field(..., description="Plaid public token")


class DonationPreferenceRequest(BaseRequest):
    """Donation preference request"""
    roundup_multiplier: float = 1.0
    max_donation_amount: float = 100.0
    is_active: bool = True


class DonationBatchRequest(BaseRequest):
    """Donation batch request"""
    user_id: int
    total_amount: float


# ============================
# Church Schemas
# ============================

class ChurchRegisterRequest(BaseRequest):
    """Church registration request"""
    name: str = Field(..., min_length=1, max_length=100, description="Church name")
    address: str = Field(..., description="Church address")
    city: str = Field(..., description="Church city")
    state: str = Field(..., description="Church state")
    zip_code: str = Field(..., description="Church zip code")
    phone: Optional[str] = Field(None, description="Church phone number")
    email: Optional[EmailStr] = Field(None, description="Church email")
    website: Optional[str] = Field(None, description="Church website")


class ChurchAdminLoginRequest(BaseRequest):
    """Church admin login request"""
    email: EmailStr = Field(..., description="Admin email")
    password: str = Field(..., description="Admin password")


class ChurchKYCUploadRequest(BaseRequest):
    """Church KYC document upload request"""
    church_id: int = Field(..., description="Church ID")
    document_type: str = Field(..., description="Type of document being uploaded")


# ============================
# Admin Schemas
# ============================

class AdminLoginRequest(BaseRequest):
    """Admin login request"""
    email: EmailStr = Field(..., description="Admin email")
    password: str = Field(..., description="Admin password")


class ToggleChurchStatusRequest(BaseRequest):
    """Toggle church status request"""
    church_id: int = Field(..., description="Church ID to toggle")
    is_active: bool = Field(..., description="New active status")


class ProcessReferralPayoutRequest(BaseRequest):
    """Process referral payout request"""
    referral_id: int = Field(..., description="Referral ID to process")


# ============================
# Response Data Schemas
# ============================

class UserData(BaseModel):
    """
    User data for API responses.
    Represents a user profile as returned by authentication and profile endpoints.
    """
    id: int = Field(..., description="Unique user ID")
    user_id: int = Field(..., alias="id", description="Alias for unique user ID (for legacy compatibility)")
    first_name: str = Field(..., description="User's first name")
    middle_name: Optional[str] = Field(None, description="User's middle name (optional)")
    last_name: Optional[str] = Field(None, description="User's last name (optional)")
    email: Optional[str] = Field(None, description="User's email address (optional)")
    phone: Optional[str] = Field(None, description="User's phone number (optional)")
    is_email_verified: bool = Field(..., description="Whether the user's email is verified")
    is_phone_verified: bool = Field(..., description="Whether the user's phone is verified")
    is_active: bool = Field(..., description="Whether the user account is active")
    church_id: Optional[int] = Field(None, description="ID of the church the user is associated with (optional)")
    stripe_customer_id: Optional[str] = Field(None, description="Stripe customer ID for payment methods (donors only)")
    created_at: datetime = Field(..., description="Timestamp when the user was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the user was last updated")
    last_login: Optional[datetime] = Field(None, description="Timestamp when the user last logged in (optional)")


class ChurchData(BaseModel):
    """
    Church data for API responses.
    Represents a church as returned by church endpoints.
    """
    id: int = Field(..., description="Unique church ID")
    name: str = Field(..., description="Church name")
    address: str = Field(..., description="Church address")
    city: str = Field(..., description="Church city")
    state: str = Field(..., description="Church state abbreviation (e.g., 'CA')")
    zip_code: str = Field(..., description="Church zip/postal code")
    phone: Optional[str] = Field(None, description="Church phone number (optional)")
    email: Optional[str] = Field(None, description="Church email address (optional)")
    website: Optional[str] = Field(None, description="Church website URL (optional)")
    is_active: bool = Field(..., description="Whether the church is active")
    created_at: datetime = Field(..., description="Timestamp when the church was created")


class BankAccountData(BaseModel):
    """
    Bank account data for API responses.
    Represents a user's linked bank account.
    """
    id: int = Field(..., description="Unique bank account ID")
    account_id: str = Field(..., description="Plaid/Stripe account identifier")
    name: str = Field(..., description="Bank account name")
    mask: str = Field(..., description="Last 4 digits of the account number")
    type: str = Field(..., description="Account type (e.g., 'checking', 'savings')")
    subtype: str = Field(..., description="Account subtype (e.g., 'personal', 'business')")
    is_active: bool = Field(..., description="Whether the bank account is active")


class TransactionData(BaseModel):
    """
    Transaction data for API responses.
    Represents a bank transaction as returned by Plaid.
    """
    id: str = Field(..., description="Unique transaction ID")
    amount: float = Field(..., description="Transaction amount")
    date: datetime = Field(..., description="Transaction date")
    name: str = Field(..., description="Transaction name or description")
    category: List[str] = Field(..., description="Transaction categories")
    pending: bool = Field(..., description="Whether the transaction is pending")


class DonationData(BaseModel):
    """
    Donation data for API responses.
    Represents a donation record.
    """
    id: int = Field(..., description="Unique donation ID")
    amount: float = Field(..., description="Donation amount")
    status: str = Field(..., description="Donation status (e.g., 'success', 'pending')")
    created_at: datetime = Field(..., description="Timestamp when the donation was created")
    executed_at: Optional[datetime] = Field(None, description="Timestamp when the donation was executed (optional)")


class DonationPreferenceData(BaseModel):
    """
    Donation preference data for API responses.
    Represents a user's donation settings.
    """
    id: int = Field(..., description="Unique preference ID")
    user_id: int = Field(..., description="User ID for the preference")
    roundup_multiplier: float = Field(..., description="Multiplier for roundups (e.g., 1.0 for normal)")
    max_donation_amount: float = Field(..., description="Maximum allowed donation amount")
    is_active: bool = Field(..., description="Whether the preference is active")
    created_at: datetime = Field(..., description="Timestamp when the preference was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the preference was last updated (optional)")


# ============================
# Response Schemas
# ============================

class AuthResponse(SuccessResponse):
    """Authentication response"""
    data: Optional[AuthTokenResponse] = None        


class UserResponse(SuccessResponse):
    """User response"""
    data: Optional[UserData] = None


class ChurchResponse(SuccessResponse):
    """Church response"""
    data: Optional[ChurchData] = None


class BankAccountsResponse(SuccessResponse):
    """Bank accounts response"""
    data: Optional[List[BankAccountData]] = None


class TransactionsResponse(SuccessResponse):
    """Transactions response"""
    data: Optional[List[TransactionData]] = None


class DonationsResponse(SuccessResponse):
    """Donations response"""
    data: Optional[List[DonationData]] = None   


class DonationPreferencesResponse(SuccessResponse):
    """Donation preferences response"""
    data: Optional[DonationPreferenceData] = None


class PlaidLinkTokenResponse(SuccessResponse):
    """Plaid link token response"""
    data: Optional[Dict[str, str]] = None


class GenericSuccessResponse(SuccessResponse):
    """Generic success response"""
    data: Optional[Dict[str, Any]] = Field(default=None)


# ============================
# Schema Factory
# ============================

class SchemaFactory:
    """Factory for creating common schema instances"""
    
    @staticmethod
    def auth_response(access_token: str, refresh_token: str, expires_in: int) -> AuthResponse:
        """Create authentication response"""
        token_data = AuthTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in
        )
        return AuthResponse(
            success=True,
            message="Authentication successful",
            data=token_data
        )
    
    @staticmethod
    def user_response(user: Any) -> UserResponse:
        """Create user response"""
        user_data = UserData(
            id=user.id,
            first_name=user.first_name,
            middle_name=user.middle_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            is_email_verified=user.is_email_verified,
            is_phone_verified=user.is_phone_verified,
            is_active=user.is_active,
            church_id=user.church_id,
            stripe_customer_id=user.stripe_customer_id,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )
        return UserResponse(
            success=True,
            message="User data retrieved",
            data=user_data
        )
    
    @staticmethod
    def church_response(church: Any) -> ChurchResponse:
        """Create church response"""
        church_data = ChurchData(
            id=church.id,
            name=church.name,
            address=church.address,
            city=church.city,
            state=church.state,
            zip_code=church.zip_code,
            phone=church.phone,
            email=church.email,
            website=church.website,
            is_active=church.is_active,
            created_at=church.created_at
        )
        return ChurchResponse(
            success=True,
            message="Church data retrieved",
            data=church_data
        )
    
    @staticmethod
    def bank_accounts_response(accounts: List[Any]) -> BankAccountsResponse:
        """Create bank accounts response"""
        accounts_data = [
            BankAccountData(
                id=account.id,
                account_id=account.account_id,
                name=account.name,
                mask=account.mask,
                type=account.type,
                subtype=account.subtype,
                is_active=account.is_active
            ) for account in accounts
        ]
        return BankAccountsResponse(
            success=True,
            message="Bank accounts retrieved",
            data=accounts_data
        )
    
    @staticmethod
    def transactions_response(transactions: List[Any]) -> TransactionsResponse:
        """Create transactions response"""
        transactions_data = [
            TransactionData(
                id=txn.id,
                amount=txn.amount,
                date=txn.date,
                name=txn.name,
                category=txn.category,
                pending=txn.pending
            ) for txn in transactions
        ]
        return TransactionsResponse(
            success=True,
            message="Transactions retrieved",
            data=transactions_data
        )
    
    @staticmethod
    def donations_response(donations: List[Any]) -> DonationsResponse:
        """Create donations response"""
        donations_data = [
            DonationData(
                id=donation.id,
                amount=donation.amount,
                status=donation.status,
                created_at=donation.created_at,
                executed_at=donation.executed_at
            ) for donation in donations
        ]
        return DonationsResponse(
            success=True,
            message="Donations retrieved",
            data=donations_data
        )
    
    @staticmethod
    def donation_preferences_response(preferences: Any) -> DonationPreferencesResponse:
        """Create donation preferences response"""
        preferences_data = DonationPreferenceData(
            id=preferences.id,
            user_id=preferences.user_id,
            roundup_multiplier=preferences.roundup_multiplier,
            max_donation_amount=preferences.max_donation_amount,
            is_active=preferences.is_active,
            created_at=preferences.created_at,
            updated_at=preferences.updated_at
        )
        return DonationPreferencesResponse(
            success=True,
            message="Donation preferences retrieved",
            data=preferences_data
        )
    
    @staticmethod
    def plaid_link_token_response(link_token: str) -> PlaidLinkTokenResponse:
        """Create Plaid link token response"""
        return PlaidLinkTokenResponse(
            success=True,
            message="Plaid link token created",
            data={"link_token": link_token}
        )
    
    @staticmethod
    def generic_success(message: str, data: Optional[Dict[str, Any]] = None) -> GenericSuccessResponse:
        """Create generic success response"""
        return GenericSuccessResponse(
            success=True,
            message=message,
            data=data
        ) 
