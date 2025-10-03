from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.core.responses import BaseResponse, SuccessResponse, ErrorResponse

# ============================
# Request Schemas
# ============================

class CreateLinkTokenRequest(BaseModel):
    user_id: Optional[int] = None
    client_name: str = "Manna Church"
    country_codes: List[str] = ["US"]
    language: str = "en"
    account_filters: Optional[Dict[str, Any]] = None

class ExchangePublicTokenRequest(BaseModel):
    public_token: str

class GetTransactionsRequest(BaseModel):
    start_date: str
    end_date: str
    account_ids: Optional[List[str]] = None

class CalculateRoundupsRequest(BaseModel):
    start_date: str
    end_date: str
    multiplier: str = Field(default="2x", description="Roundup multiplier: 2x or 3x")

class UpsertPreferencesRequest(BaseModel):
    frequency: str = Field(default="biweekly", description="Donation frequency: biweekly or monthly")
    multiplier: str = Field(default="2x", description="Roundup multiplier: 2x or 3x")
    church_id: Optional[int] = Field(None, description="Church ID to donate to")
    pause: bool = Field(default=False, description="Pause roundup giving")
    cover_processing_fees: bool = Field(default=False, description="Cover processing fees")

class PublicTokenExchangeRequest(BaseModel):
    """
    Request schema for exchanging a Plaid public token for an access token.
    """
    public_token: str = Field(..., description="Plaid public token")

# ============================
# Mobile Bank Request Schemas
# ============================

class LinkTokenRequest(BaseModel):
    """Request for creating Plaid link token"""
    client_name: Optional[str] = Field("Manna", description="Client name")
    country_codes: Optional[List[str]] = Field(["US"], description="Country codes")
    language: Optional[str] = Field("en", description="Language")

class PublicTokenRequest(BaseModel):
    """Request for exchanging public token"""
    public_token: str = Field(..., description="Plaid public token")

class TransactionRequest(BaseModel):
    """Request for getting transactions"""
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")

class MobileTransactionRequest(BaseModel):
    """Request for getting mobile transactions - automatically fetches from last donation to now"""
    pass

class RoundupSettingsRequest(BaseModel):
    """Request for updating roundup settings"""
    frequency: Optional[str] = Field(None, description="Collection frequency: biweekly or monthly")
    multiplier: Optional[str] = Field(None, description="Roundup multiplier: 1x, 2x or 3x")
    church_id: Optional[int] = Field(None, description="Church ID to donate to")
    pause: Optional[bool] = Field(None, description="Pause roundup giving")
    cover_processing_fees: Optional[bool] = Field(None, description="Cover processing fees")

class RoundupToggleRequest(BaseModel):
    """Request for toggling roundups"""
    pause: bool = Field(..., description="Pause roundup giving")

class RoundupCalculationRequest(BaseModel):
    """Request for calculating roundups"""
    multiplier: Optional[str] = Field("2x", description="Roundup multiplier: 2x or 3x")

class PaymentMethodRequest(BaseModel):
    """Request for saving payment method"""
    payment_method_id: str = Field(..., description="Stripe payment method ID")

# ============================
# Data Models
# ============================

class LinkedBankAccount(BaseModel):
    account_id: str
    name: str
    mask: str
    type: str
    subtype: str
    institution: str
    is_active: bool

# RoundupTransaction schema removed - using DonationBatch instead

class DonationHistoryItem(BaseModel):
    id: int
    amount: float
    status: str
    created_at: datetime
    executed_at: Optional[datetime]

# ============================
# Response Schemas
# ============================

class LinkTokenResponse(SuccessResponse):
    data: Optional[Dict[str, str]] = None  # Contains link_token

class AccountsResponse(SuccessResponse):
    data: Optional[List[LinkedBankAccount]] = None

class RoundupResponse(SuccessResponse):
    data: Optional[List[dict]] = None  # Using dict instead of RoundupTransaction

class PreferencesSaveResponse(SuccessResponse):
    data: Optional[Dict[str, Any]] = None  # Contains saved preferences

class DonationBatchResponse(SuccessResponse):
    data: Optional[Dict[str, Any]] = None  # Contains donation batch details

class DonationHistoryResponse(SuccessResponse):
    data: Optional[List[DonationHistoryItem]] = None

class ExchangeTokenResponse(SuccessResponse):
    data: Optional[Dict[str, Any]] = None

class TransactionsResponse(SuccessResponse):
    data: Optional[Dict[str, Any]] = None

class DonationSummaryResponse(SuccessResponse):
    data: Optional[Dict[str, Any]] = None

class PaymentMethodResponse(SuccessResponse):
    data: Optional[Dict[str, str]] = None  # Contains payment_method_id

class PaymentMethodsListResponse(SuccessResponse):
    data: Optional[List[Dict[str, Any]]] = None

class DonationDashboardResponse(SuccessResponse):
    data: Optional[Dict[str, Any]] = None  # Contains comprehensive dashboard data


# ============================
# Mobile App Schemas
# ============================

class MobileRoundupSettingsRequest(BaseModel):
    """Mobile roundup settings request"""
    collection_frequency: Optional[str] = Field(None, description="Collection frequency: bi-weekly, monthly")
    roundup_multiplier: Optional[float] = Field(None, description="Roundup multiplier: 0.1-10.0")
    roundup_threshold: Optional[float] = Field(None, description="Roundup threshold: 0.01-10.0")
    monthly_cap: Optional[float] = Field(None, description="Monthly cap: >= 0")
    pause_giving: Optional[bool] = Field(None, description="Pause roundup giving")
    cover_processing_fees: Optional[bool] = Field(None, description="Cover processing fees")


class MobileRoundupSettingsResponse(SuccessResponse):
    """Mobile roundup settings response"""
    data: Optional[Dict[str, Any]] = Field(None, description="Roundup settings data")


class MobileTransactionData(BaseModel):
    """Mobile transaction data"""
    id: str = Field(..., description="Transaction ID")
    merchant: str = Field(..., description="Merchant name")
    amount: float = Field(..., description="Transaction amount")
    roundup_amount: float = Field(..., description="Calculated roundup amount")
    date: str = Field(..., description="Transaction date")
    category: List[str] = Field(default_factory=list, description="Transaction categories")
    account_name: str = Field(..., description="Bank account name")


class MobileTransactionsResponse(SuccessResponse):
    """Mobile transactions response"""
    data: Optional[Dict[str, Any]] = Field(None, description="Transactions data")


class MobilePendingRoundupsResponse(SuccessResponse):
    """Mobile pending roundups response"""
    data: Optional[Dict[str, Any]] = Field(None, description="Pending roundups data")


class MobileQuickToggleResponse(SuccessResponse):
    """Mobile quick toggle response"""
    data: Optional[Dict[str, Any]] = Field(None, description="Toggle response data")


class MobileDonationHistoryItem(BaseModel):
    """Mobile donation history item"""
    id: int = Field(..., description="Donation ID")
    amount: float = Field(..., description="Donation amount")
    church_name: str = Field(..., description="Church name")
    date: str = Field(..., description="Donation date")
    status: str = Field(..., description="Donation status")
    type: str = Field(..., description="Donation type")


class MobileDonationHistoryResponse(SuccessResponse):
    """Mobile donation history response"""
    data: Optional[Dict[str, Any]] = Field(None, description="Donation history data")


class MobileImpactSummaryResponse(SuccessResponse):
    """Mobile impact summary response"""
    data: Optional[Dict[str, Any]] = Field(None, description="Impact summary data")
