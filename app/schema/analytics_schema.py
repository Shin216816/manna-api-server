from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DonationTrendData(BaseModel):
    date: str
    amount: float

class SpendingCategoryData(BaseModel):
    name: str
    amount: float
    percentage: float
    transaction_count: int
    color: str

class TopMerchantData(BaseModel):
    name: str
    total_amount: float
    transaction_count: int

class ChurchAnalyticsData(BaseModel):
    total_donations: float
    donation_growth: float
    active_givers: int
    giver_growth: float
    avg_donation: float
    total_transactions: int
    this_month_donations: float
    monthly_growth: float
    donation_trends: List[DonationTrendData]
    spending_categories: List[SpendingCategoryData]
    top_merchants: List[TopMerchantData]

class ChurchAnalyticsResponse(BaseModel):
    success: bool
    data: ChurchAnalyticsData
