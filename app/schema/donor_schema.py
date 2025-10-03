from pydantic import BaseModel, Field, EmailStr, validator, model_validator, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.core.responses import BaseResponse, SuccessResponse, ErrorResponse

# ============================
# Donor Authentication Request Schemas
# ============================

class DonorRegisterRequest(BaseModel):
    """
    Donor registration request
    
    Request schema for registering a new donor account.
    Either email or phone number is required.
    """
    first_name: str = Field(..., min_length=1, max_length=50, description="First name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name")
    middle_name: Optional[str] = Field(None, max_length=50, description="Middle name")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    password: str = Field(..., min_length=8, description="Password")
    church_id: Optional[int] = Field(None, description="Church ID to associate with")
    
    @field_validator('phone')
    def validate_phone(cls, v):
        if v is not None and not v.strip():
            return None
        return v
    
    @model_validator(mode='after')
    def validate_email_or_phone(self):
        if not self.email and not self.phone:
            raise ValueError("Either email or phone is required")
        return self

class DonorRegisterConfirmRequest(BaseModel):
    """
    Confirm donor registration
    
    Request schema for confirming donor registration using
    the access code sent via email or SMS.
    """
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    access_code: str = Field(..., description="Access code sent via email/SMS")

class DonorRegisterCodeResendRequest(BaseModel):
    """Resend registration access code"""
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    
    @model_validator(mode='after')
    def validate_contact_method(self):
        if not self.email and not self.phone:
            raise ValueError("Either email or phone is required")
        return self

class DonorLoginRequest(BaseModel):
    """
    Donor login request
    
    Request schema for authenticating a donor account.
    Supports both email and phone number login.
    """
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    password: Optional[str] = Field(None, description="Password")
    oauth_provider: Optional[str] = Field(None, description="OAuth provider (google, apple)")
    

    
    @model_validator(mode='after')
    def validate_authentication_method(self):
        # Ensure either password or oauth_provider is provided
        if self.password and self.oauth_provider:
            raise ValueError("Cannot use both password and oauth_provider")
        if not self.password and not self.oauth_provider:
            raise ValueError("Either password or oauth_provider is required")
        
        # For password-based login, require either email or phone
        if not self.oauth_provider:
            if not self.email and not self.phone:
                raise ValueError("Either email or phone is required")
            if not self.password:
                raise ValueError("Password is required for non-OAuth login")
        
        return self

class DonorLogoutRequest(BaseModel):
    """Donor logout request"""
    refresh_token: Optional[str] = Field(None, description="Refresh token to invalidate")

class DonorForgotPasswordRequest(BaseModel):
    """Forgot password request for donor web app"""
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    
    @model_validator(mode='after')
    def validate_email_or_phone(self):
        if not self.email and not self.phone:
            raise ValueError("Either email or phone is required")
        return self

class DonorVerifyOtpRequest(BaseModel):
    """Verify OTP for password reset"""
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    otp: str = Field(..., description="OTP code")
    
    @model_validator(mode='after')
    def validate_email_or_phone(self):
        if not self.email and not self.phone:
            raise ValueError("Either email or phone is required")
        return self

class DonorResetPasswordRequest(BaseModel):
    """Reset password request"""
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    otp: str = Field(..., description="OTP code")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @model_validator(mode='after')
    def validate_email_or_phone(self):
        if not self.email and not self.phone:
            raise ValueError("Either email or phone is required")
        return self

class DonorChangePasswordRequest(BaseModel):
    """Change donor password"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

class DonorGoogleOAuthRequest(BaseModel):
    """Request to authenticate or create donor account using Google OAuth"""
    id_token: str = Field(..., description="Google ID token")
    invite_token: str = Field(..., description="Invite token for church association")

class DonorSendPhoneVerificationRequest(BaseModel):
    """Request to send phone verification code"""
    phone: str = Field(..., description="Phone number to verify")

class DonorVerifyPhoneVerificationRequest(BaseModel):
    """Request to verify phone number with OTP code"""
    phone: str = Field(..., description="Phone number to verify")
    access_code: str = Field(..., description="OTP verification code")

class DonorAppleOAuthRequest(BaseModel):
    """Apple OAuth request for donor web app"""
    id_token: str = Field(..., description="Apple ID token")
    church_id: Optional[int] = Field(None, description="Church ID to associate with")

class DonorRefreshTokenRequest(BaseModel):
    """Refresh token request for donor web app"""
    refresh_token: str = Field(..., description="Refresh token")

class DonorVerifyEmailRequest(BaseModel):
    """Verify email address for donor"""
    access_code: str = Field(..., description="Access code sent via email")

class DonorVerifyPhoneRequest(BaseModel):
    """Verify phone number for donor"""
    otp: str = Field(..., description="OTP code sent via SMS")

class DonorResendVerificationRequest(BaseModel):
    """Resend verification code for donor"""
    type: str = Field(..., description="Verification type: email or phone")

class DonorChangePasswordRequest(BaseModel):
    """Change password for authenticated donor"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

class DonorUpdateProfileRequest(BaseModel):
    """Update donor profile information"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="First name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Last name")
    middle_name: Optional[str] = Field(None, max_length=50, description="Middle name")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    church_id: Optional[int] = Field(None, description="Church ID to associate with")

# ============================
# Donor Dashboard Request Schemas
# ============================

class DonorDashboardRequest(BaseModel):
    """Get donor dashboard data"""
    include_transactions: bool = Field(True, description="Include recent transactions")
    include_roundups: bool = Field(True, description="Include roundup calculations")
    include_impact: bool = Field(True, description="Include impact analytics")

class DonorImpactRequest(BaseModel):
    """Get donor impact analytics"""
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    group_by: str = Field("month", description="Group by: day, week, month, year")

# ============================
# Donor Roundup Request Schemas
# ============================

class DonorRoundupSettingsRequest(BaseModel):
    """Update donor roundup settings"""
    frequency: Optional[str] = Field(
        None, 
        description="Collection frequency: weekly, biweekly or monthly",
        pattern="^(weekly|biweekly|monthly)$"
    )
    multiplier: Optional[str] = Field(
        None, 
        description="Roundup multiplier: 1x, 2x, 3x or 5x",
        pattern="^[1-5]x$"
    )
    church_id: Optional[int] = Field(None, description="Church ID to donate to")
    pause: Optional[bool] = Field(None, description="Pause roundup giving")
    cover_processing_fees: Optional[bool] = Field(None, description="Cover processing fees")
    monthly_cap: Optional[float] = Field(None, description="Monthly cap amount")
    minimum_roundup: Optional[float] = Field(None, description="Minimum roundup threshold")

class DonorPendingRoundupsRequest(BaseModel):
    """Request for getting pending roundups"""
    include_transactions: Optional[bool] = Field(False, description="Include transaction details")
    days_back: Optional[int] = Field(7, description="Number of days to look back for transactions")

class DonorToggleRoundupsRequest(BaseModel):
    """Request to toggle roundup donations"""
    enable: bool = Field(..., description="Enable or disable roundup donations")

class DonorCalculateRoundupsRequest(BaseModel):
    """Request to calculate roundups for a period"""
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    days: Optional[int] = Field(30, description="Number of days to calculate")

class DonorRoundupHistoryRequest(BaseModel):
    """Request for getting roundup history"""
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    status: Optional[str] = Field(None, description="Filter by status")
    frequency: Optional[str] = Field(None, description="Filter by frequency")
    limit: Optional[int] = Field(50, description="Number of records to fetch")

class DonorProfileUpdateRequest(BaseModel):
    """Update donor profile information"""
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    middle_name: Optional[str] = Field(None, description="Middle name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    church_id: Optional[int] = Field(None, description="Church ID for association")
    
    @field_validator('phone')
    def validate_phone(cls, v):
        """Convert empty strings to None for phone numbers"""
        if v is not None and not v.strip():
            return None
        return v

class DonorProfilePictureRequest(BaseModel):
    """Request for profile picture operations"""
    action: str = Field(..., description="Action: upload or delete")

class DonorPreferencesUpdateRequest(BaseModel):
    """Update donor preferences"""
    language: Optional[str] = Field(None, description="Language preference")
    timezone: Optional[str] = Field(None, description="Timezone preference")
    currency: Optional[str] = Field(None, description="Currency preference")
    theme: Optional[str] = Field(None, description="Theme preference")
    # Notification preferences
    email_notifications: Optional[bool] = Field(None, description="Enable email notifications")
    sms_notifications: Optional[bool] = Field(None, description="Enable SMS notifications")
    push_notifications: Optional[bool] = Field(None, description="Enable push notifications")

class DonorDonationSettingsRequest(BaseModel):
    """Update donor donation settings"""
    frequency: Optional[str] = Field(None, description="Donation frequency: biweekly or monthly")
    multiplier: Optional[str] = Field(None, description="Roundup multiplier")
    pause: Optional[bool] = Field(None, description="Pause roundup giving")
    cover_processing_fees: Optional[bool] = Field(None, description="Cover processing fees")
    minimum_roundup: Optional[float] = Field(None, description="Minimum roundup threshold")
    monthly_cap: Optional[float] = Field(None, description="Monthly donation cap")

class DonorRoundupCalculationRequest(BaseModel):
    """Calculate roundups for donor"""
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    multiplier: Optional[str] = Field("2x", description="Roundup multiplier: 1x, 2x or 3x")

class DonorRoundupToggleRequest(BaseModel):
    """Toggle roundups on/off for donor"""
    pause: bool = Field(..., description="Pause roundup giving")

# ============================
# Donor Banking Request Schemas
# ============================

class DonorLinkTokenRequest(BaseModel):
    """Request for creating Plaid link token for donor"""
    client_name: Optional[str] = Field("Manna Donor", description="Client name")
    country_codes: Optional[List[str]] = Field(["US"], description="Country codes")
    language: Optional[str] = Field("en", description="Language")

class DonorPublicTokenRequest(BaseModel):
    """Request for exchanging public token for donor"""
    public_token: str = Field(..., description="Plaid public token")

class DonorTransactionRequest(BaseModel):
    """Request for getting transactions for donor"""
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    limit: Optional[int] = Field(50, description="Number of transactions to fetch")

# ============================
# Donor Settings Request Schemas
# ============================

class DonorNotificationSettingsRequest(BaseModel):
    """Update donor notification settings"""
    email_notifications: bool = Field(True, description="Enable email notifications")
    sms_notifications: bool = Field(True, description="Enable SMS notifications")
    push_notifications: bool = Field(True, description="Enable push notifications")
    roundup_reminders: bool = Field(True, description="Enable roundup reminders")
    donation_receipts: bool = Field(True, description="Enable donation receipts")
    impact_updates: bool = Field(True, description="Enable impact updates")

class DonorPrivacySettingsRequest(BaseModel):
    """Update donor privacy settings"""
    share_impact_data: bool = Field(True, description="Share impact data with church")
    share_transaction_categories: bool = Field(True, description="Share transaction categories")
    share_donation_amounts: bool = Field(True, description="Share donation amounts with church")

# ============================
# Donor Response Data Models
# ============================

class DonorProfileData(BaseModel):
    """Donor profile data"""
    id: int
    first_name: str
    last_name: str
    middle_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    is_email_verified: bool
    is_phone_verified: bool
    church_id: Optional[int]
    church_name: Optional[str]
    profile_picture_url: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]

class DonorDashboardData(BaseModel):
    """Donor dashboard data"""
    profile: DonorProfileData
    pending_roundups: float
    total_donated: float
    this_month_donated: float
    donation_count: int
    next_collection_date: Optional[str]
    recent_transactions: List[Dict[str, Any]]
    impact_summary: Dict[str, Any]

class DonorRoundupSettingsData(BaseModel):
    """Donor roundup settings data"""
    roundup_enabled: bool
    multiplier: str
    frequency: str
    cover_processing_fees: bool
    monthly_cap: float
    church_id: Optional[int]
    church_name: Optional[str]
    next_collection_date: Optional[str]

class DonorTransactionData(BaseModel):
    """Donor transaction data"""
    transaction_id: str
    amount: float
    date: str
    merchant: str
    category: List[str]
    roundup_amount: float
    total_with_roundup: float

class DonorDonationData(BaseModel):
    """Donor donation data"""
    id: int
    amount: float
    status: str
    church_name: str
    church_id: int
    created_at: str
    processed_at: Optional[str]
    transaction_count: int

class DonorImpactData(BaseModel):
    """Donor impact data"""
    total_donated: float
    donation_count: int
    this_month_donated: float
    average_donation: float
    currency: str
    impact_breakdown: Dict[str, Any]

# ============================
# Donor Response Schemas
# ============================

class DonorAuthResponse(BaseModel):
    """Donor authentication response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: DonorProfileData

class DonorProfileResponse(BaseModel):
    """Donor profile response"""
    profile: DonorProfileData

class DonorDashboardResponse(BaseModel):
    """Donor dashboard response"""
    dashboard: DonorDashboardData

class DonorRoundupSettingsResponse(BaseModel):
    """Donor roundup settings response"""
    settings: DonorRoundupSettingsData

class DonorTransactionsResponse(BaseModel):
    """Donor transactions response"""
    transactions: List[DonorTransactionData]
    total_roundups: float

class DonorDonationsResponse(BaseModel):
    """Donor donations response"""
    donations: List[DonorDonationData]

class DonorImpactResponse(BaseModel):
    """Donor impact response"""
    impact: DonorImpactData

# ============================
# Donor Invite Schemas
# ============================

class InviteCreateRequest(BaseModel):
    church_id: int
    expires_in_minutes: Optional[int] = 10

class DonorSignupRequest(BaseModel):
    """Request to create a donor account with invite token"""
    first_name: str = Field(..., min_length=1, max_length=50, description="First name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name")
    email: str = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    password: Optional[str] = Field(None, min_length=8, description="Password (required if not using OAuth)")
    oauth_provider: Optional[str] = Field(None, description="OAuth provider: 'google' or 'apple'")
    invite_token: Optional[str] = Field(None, description="Invite token from church selection")
    
    @model_validator(mode='after')
    def validate_password_or_oauth(self):
        if not self.password and not self.oauth_provider:
            raise ValueError("Either password or oauth_provider is required")
        if self.password and self.oauth_provider:
            raise ValueError("Cannot use both password and oauth_provider")
        return self

class DonorGoogleOAuthRequest(BaseModel):
    """Request to authenticate or create donor account using Google OAuth"""
    id_token: str = Field(..., description="Google ID token")
    invite_token: str = Field(..., description="Invite token for church association")

class DonorSendPhoneVerificationRequest(BaseModel):
    """Request to send phone verification code"""
    phone: str = Field(..., description="Phone number to verify")

class DonorVerifyPhoneVerificationRequest(BaseModel):
    """Request to verify phone number with OTP code"""
    phone: str = Field(..., description="Phone number to verify")
    access_code: str = Field(..., description="OTP verification code")
