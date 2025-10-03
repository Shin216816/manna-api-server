"""
Donation Schemas

Defines request and response schemas for donation endpoints:
- Donation preferences (roundup settings)
- Donation management
- Roundup calculations
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DonationPreferencesRequest(BaseModel):
    """Donation preferences update request"""
    multiplier: Optional[str] = Field(None, description="Roundup multiplier (1x, 2x, 3x)")
    frequency: Optional[str] = Field(None, description="Collection frequency (weekly, bi-weekly, monthly)")
    pause: Optional[bool] = Field(None, description="Pause roundups")
    cover_processing_fees: Optional[bool] = Field(None, description="Cover processing fees")
    church_id: Optional[int] = Field(None, description="Default church ID")


# REMOVED: DonationScheduleRequest class
# Not needed for roundup-only donation system.
# All donation settings are handled by DonationPreferencesRequest.


class DonationHistoryResponse(BaseModel):
    """Donation history response"""
    id: int = Field(..., description="Donation ID")
    amount: float = Field(..., description="Donation amount")
    date: Optional[str] = Field(None, description="Donation date")
    status: str = Field(..., description="Donation status")
    type: str = Field(..., description="Donation type")
    church_name: Optional[str] = Field(None, description="Church name")


class DonationSummaryResponse(BaseModel):
    """Donation summary response"""
    total_donated: float = Field(..., description="Total amount donated")
    total_donations: int = Field(..., description="Total number of donations")
    this_month: float = Field(..., description="Amount donated this month")
    average_per_donation: float = Field(..., description="Average amount per donation")
    last_donation_date: Optional[str] = Field(None, description="Last donation date")


class RoundupCalculationRequest(BaseModel):
    """Roundup calculation request"""
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    multiplier: str = Field(default="1x", description="Roundup multiplier")


class RoundupCalculationResponse(BaseModel):
    """Roundup calculation response"""
    user_id: int = Field(..., description="User ID")
    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    multiplier: str = Field(..., description="Applied multiplier")
    estimated_transactions: int = Field(..., description="Estimated number of transactions")
    estimated_roundup_per_transaction: float = Field(..., description="Estimated roundup per transaction")
    total_roundup: float = Field(..., description="Total calculated roundup")
    calculation_date: str = Field(..., description="Calculation timestamp")
