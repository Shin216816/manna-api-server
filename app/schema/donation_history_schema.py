from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DonationData(BaseModel):
    id: int
    amount: float
    status: str
    type: str
    frequency: Optional[str] = None
    multiplier: Optional[str] = None
    created_at: datetime
    collection_date: Optional[datetime] = None
    payout_date: Optional[datetime] = None
    church_name: str
    transaction_count: int
    processing_fees: Optional[float] = None

class MonthlyTrendData(BaseModel):
    month: str
    amount: float
    donation_count: int
    growth: float

class ImpactStoryData(BaseModel):
    title: str
    description: str
    impact_description: str

class DonationHistoryData(BaseModel):
    donations: List[DonationData]
    total_amount: float
    total_batches: int
    average_per_batch: float
    impact_score: int
    monthly_trends: List[MonthlyTrendData]
    impact_stories: List[ImpactStoryData]

class PaginationData(BaseModel):
    page: int
    limit: int
    total: int
    pages: int

class DonationHistoryResponse(BaseModel):
    success: bool
    data: DonationHistoryData
    pagination: PaginationData
