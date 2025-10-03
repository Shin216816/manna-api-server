"""
Pydantic schemas for the Manna Backend API.

This package contains all Pydantic models for:
- Request/Response validation
- API documentation
- Data serialization
- Type safety
"""

# Core responses
from app.schema.unified_schema import (
    BaseRequest,
    PaginationRequest,
    UserData,
    ChurchData,
    BankAccountData,
    TransactionData,
    DonationData,
    DonationPreferenceData,
    SchemaFactory
)

# Auth schemas
from app.schema.auth_schema import (
    AuthRegisterRequest,
    AuthRegisterConfirmRequest,
    AuthRegisterCodeResendRequest,
    AuthLoginRequest,
    AuthForgotPasswordRequest,
    AuthVerifyOtpRequest,
    AuthResetPasswordRequest,
    AuthChangePasswordRequest,
    AuthLogoutRequest,
    GoogleOAuthRequest,
    AppleOAuthRequest,
    RefreshTokenRequest,
    RegisterData,
    AccessCodeData,
    PasswordResetData,
    LogoutData,
    EmptyData,
    AuthRegisterResponse,
    AuthLoginResponse,
    AuthForgotPasswordResponse,
    AuthVerifyOtpResponse,
    AuthResetPasswordResponse,
    AuthChangePasswordResponse,
    AuthLogoutResponse,
    AuthRegisterConfirmResponse,
    AuthRegisterCodeResendResponse,
    GoogleOAuthResponse,
    AppleOAuthResponse,
    RefreshTokenResponse,
    MeResponse
)

# Bank schemas
from app.schema.bank_schema import (
    CreateLinkTokenRequest,
    ExchangePublicTokenRequest,
    GetTransactionsRequest,
    CalculateRoundupsRequest,
    UpsertPreferencesRequest,
    PublicTokenExchangeRequest,
    LinkedBankAccount,
    # RoundupTransaction removed - using DonationBatch instead
    DonationHistoryItem,
    LinkTokenResponse,
    AccountsResponse,
    RoundupResponse,
    PreferencesSaveResponse,
    DonationBatchResponse,
    DonationHistoryResponse,
    ExchangeTokenResponse,
    TransactionsResponse,
    DonationSummaryResponse,
    PaymentMethodResponse,
    PaymentMethodsListResponse,
    DonationDashboardResponse,
    MobileRoundupSettingsRequest,
    MobileRoundupSettingsResponse,
    MobileTransactionData,
    MobileTransactionsResponse,
    MobilePendingRoundupsResponse,
    MobileQuickToggleResponse,
    MobileDonationHistoryItem,
    MobileDonationHistoryResponse,
    MobileImpactSummaryResponse
)

# Church schemas
from app.schema.church_schema import (
    ChurchRegistrationRequest,
    ChurchKYCRequest
)

# Admin schemas
from app.schema.admin_schema import (
    AdminLoginRequest,
    ChurchKYCReviewRequest,
    UserSearchRequest,
    AnalyticsPeriodRequest,
    ReferralPayoutRequest,
    ChurchListResponse,
    ChurchDetailsResponse,
    KYCReviewResponse,
    UserListResponse,
    UserDetailsResponse,
    PlatformAnalyticsResponse,
    ReferralCommissionsResponse,
    ReferralPayoutsResponse,
    ChurchSummaryData,
    ChurchDetailsData,
    UserSummaryData,
    UserDetailsData
)

# Webhook schemas
from app.schema.webhook_schema import (
    WebhookEvent,
    PlaidWebhookEvent,
    StripeWebhookEvent,
    WebhookResponse
)

# Main exports
__all__ = [
    # Core schemas
    "BaseRequest",
    "PaginationRequest",
    "UserData",
    "ChurchData", 
    "BankAccountData",
    "TransactionData",
    "DonationData",
    "DonationPreferenceData",
    "SchemaFactory",
    
    # Auth schemas
    "AuthRegisterRequest",
    "AuthRegisterConfirmRequest",
    "AuthRegisterCodeResendRequest",
    "AuthLoginRequest",
    "AuthForgotPasswordRequest",
    "AuthVerifyOtpRequest",
    "AuthResetPasswordRequest",
    "AuthChangePasswordRequest",
    "AuthLogoutRequest",
    "GoogleOAuthRequest",
    "AppleOAuthRequest",
    "RefreshTokenRequest",
    "RegisterData",
    "AccessCodeData",
    "PasswordResetData",
    "LogoutData",
    "EmptyData",
    "AuthRegisterResponse",
    "AuthLoginResponse",
    "AuthForgotPasswordResponse",
    "AuthVerifyOtpResponse",
    "AuthResetPasswordResponse",
    "AuthChangePasswordResponse",
    "AuthLogoutResponse",
    "AuthRegisterConfirmResponse",
    "AuthRegisterCodeResendResponse",
    "GoogleOAuthResponse",
    "AppleOAuthResponse",
    "RefreshTokenResponse",
    "MeResponse",
    
    # Bank schemas
    "CreateLinkTokenRequest",
    "ExchangePublicTokenRequest",
    "GetTransactionsRequest",
    "CalculateRoundupsRequest",
    "UpsertPreferencesRequest",
    "PublicTokenExchangeRequest",
    "LinkedBankAccount",
    # "RoundupTransaction" removed
    "DonationHistoryItem",
    "LinkTokenResponse",
    "AccountsResponse",
    "RoundupResponse",
    "PreferencesSaveResponse",
    "DonationBatchResponse",
    "DonationHistoryResponse",
    "ExchangeTokenResponse",
    "TransactionsResponse",
    "DonationSummaryResponse",
    "PaymentMethodResponse",
    "PaymentMethodsListResponse",
    "DonationDashboardResponse",
    "MobileRoundupSettingsRequest",
    "MobileRoundupSettingsResponse",
    "MobileTransactionData",
    "MobileTransactionsResponse",
    "MobilePendingRoundupsResponse",
    "MobileQuickToggleResponse",
    "MobileDonationHistoryItem",
    "MobileDonationHistoryResponse",
    "MobileImpactSummaryResponse",
    
    # Church schemas
    "ChurchRegistrationRequest",
    "ChurchKYCRequest",
    
    # Admin schemas
    "ChurchKYCReviewRequest",
    "UserSearchRequest",
    "AnalyticsPeriodRequest",
    "ReferralPayoutRequest",
    "ChurchListResponse",
    "ChurchDetailsResponse",
    "KYCReviewResponse",
    "UserListResponse",
    "UserDetailsResponse",
    "PlatformAnalyticsResponse",
    "ReferralCommissionsResponse",
    "ReferralPayoutsResponse",
    "ChurchSummaryData",
    "ChurchDetailsData",
    "UserSummaryData",
    "UserDetailsData",
    "AdminLoginRequest",

    
    # Webhook schemas
    "WebhookEvent",
    "PlaidWebhookEvent",
    "StripeWebhookEvent",
    "WebhookResponse"
]
