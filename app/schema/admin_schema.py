"""
Admin Platform Schemas

Defines request and response schemas for admin platform endpoints:
- Church management and oversight
- User management and support
- Platform analytics and reporting
- KYC review and approval
- Referral commission management
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.core.responses import SuccessResponse


# ============================
# Request Schemas
# ============================

class AdminLoginRequest(BaseModel):
    """Admin login request"""
    email: EmailStr
    password: str

class AdminInvitationRequest(BaseModel):
    """Admin registration request with invitation code"""
    first_name: str = Field(..., min_length=2, max_length=50, description="First name")
    last_name: str = Field(..., min_length=2, max_length=50, description="Last name")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    confirm_password: str = Field(..., description="Confirm password")
    invitation_code: str = Field(..., description="Invitation code required for admin signup")

class AdminProfileUpdate(BaseModel):
    """Admin profile update request"""
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    current_password: Optional[str] = Field(None, description="Current password for verification")
    new_password: Optional[str] = Field(None, min_length=8, max_length=128)


class ChurchKYCReviewRequest(BaseModel):
    """Church KYC review request"""
    notes: Optional[str] = Field(None, description="Internal notes")
    reason: Optional[str] = Field(None, description="Reason for rejection")

class KYCAdditionalInfoRequest(BaseModel):
    """KYC additional information request"""
    required_info: str = Field(..., description="Required information description")
    notes: Optional[str] = Field(None, description="Additional notes")

class KYCNotesUpdateRequest(BaseModel):
    """KYC notes update request"""
    notes: str = Field(..., description="Internal notes")

class KYCStatisticsResponse(BaseModel):
    """KYC statistics response"""
    total_applications: int
    pending_count: int
    approved_count: int
    rejected_count: int
    needs_info_count: int
    recent_applications: int
    avg_processing_time_hours: float
    approval_rate: float


class UserSearchRequest(BaseModel):
    """User search request"""
    search_term: str = Field(..., description="Search term (name or email)")
    limit: int = Field(default=20, description="Number of results to return")
    offset: int = Field(default=0, description="Number of results to skip")


class AnalyticsPeriodRequest(BaseModel):
    """Analytics period request"""
    period: str = Field(default="month", description="Analytics period: week, month, year")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")


class ReferralPayoutRequest(BaseModel):
    """Referral payout request"""
    church_id: int = Field(..., description="Church ID")
    amount: float = Field(..., description="Payout amount")
    notes: Optional[str] = Field(None, description="Payout notes")


class InvitationValidationRequest(BaseModel):
    """Request to validate invitation code"""
    invitation_code: str = Field(..., description="Invitation code to validate")


# ============================
# Response Schemas
# ============================

class ChurchListResponse(SuccessResponse):
    """Church list response"""
    data: Any = Field(..., description="Church list data")


class ChurchDetailsResponse(SuccessResponse):
    """Church details response"""
    data: Any = Field(..., description="Church details data")


class KYCReviewResponse(SuccessResponse):
    """KYC review response"""
    data: Any = Field(..., description="KYC review data")


class UserListResponse(SuccessResponse):
    """User list response"""
    data: Any = Field(..., description="User list data")


class UserDetailsResponse(SuccessResponse):
    """User details response"""
    data: Any = Field(..., description="User details data")


class PlatformAnalyticsResponse(SuccessResponse):
    """Platform analytics response"""
    data: Any = Field(..., description="Platform analytics data")


class ReferralCommissionsResponse(SuccessResponse):
    """Referral commissions response"""
    data: Any = Field(..., description="Referral commissions data")


class ReferralPayoutsResponse(SuccessResponse):
    """Referral payouts response"""
    data: Any = Field(..., description="Referral payouts data")


# ============================
# Data Models
# ============================

class ChurchSummaryData(BaseModel):
    """Church summary data for admin list"""
    id: int = Field(..., description="Church ID")
    name: str = Field(..., description="Church name")
    admin_email: str = Field(..., description="Admin email")
    status: str = Field(..., description="Church status")
    registration_date: datetime = Field(..., description="Registration date")
    total_revenue: float = Field(..., description="Total revenue")
    active_givers: int = Field(..., description="Number of active givers")
    kyc_status: str = Field(..., description="KYC status")


class ChurchDetailsData(BaseModel):
    """Detailed church data for admin view"""
    id: int = Field(..., description="Church ID")
    name: str = Field(..., description="Church name")
    email: str = Field(..., description="Admin email")
    phone: str = Field(..., description="Contact phone")
    address: str = Field(..., description="Church address")
    ein: str = Field(..., description="Tax ID")
    website: Optional[str] = Field(None, description="Church website")
    status: str = Field(..., description="Church status")
    kyc_info: Dict[str, Any] = Field(..., description="KYC information")
    analytics: Dict[str, Any] = Field(..., description="Church analytics")
    created_at: datetime = Field(..., description="Registration date")
    updated_at: datetime = Field(..., description="Last updated date")


class UserSummaryData(BaseModel):
    """User summary data for admin list"""
    id: int = Field(..., description="User ID")
    name: str = Field(..., description="User name")
    email: str = Field(..., description="User email")
    church_name: Optional[str] = Field(None, description="Associated church")
    total_donated: float = Field(..., description="Total donated amount")
    last_active: datetime = Field(..., description="Last active date")
    status: str = Field(..., description="User status")


class UserDetailsData(BaseModel):
    """Detailed user data for admin view"""
    id: int = Field(..., description="User ID")
    name: str = Field(..., description="User name")
    email: str = Field(..., description="User email")
    phone: Optional[str] = Field(None, description="Phone number")
    church_name: Optional[str] = Field(None, description="Associated church")
    donation_history: List[Dict[str, Any]] = Field(..., description="Donation history")
    bank_accounts: List[Dict[str, Any]] = Field(..., description="Bank accounts")
    preferences: Dict[str, Any] = Field(..., description="User preferences")
    created_at: datetime = Field(..., description="Registration date")
    last_login: Optional[datetime] = Field(None, description="Last login date")


# Note: PlatformAnalyticsData, ReferralCommissionData, and ReferralPayoutData schemas removed
# as they are unused in the API
