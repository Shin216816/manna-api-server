from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# ReferralCodeData and ReferralCodeResponse removed - using ChurchReferral instead

class ReferredChurchData(BaseModel):
    id: int
    name: str
    joined_at: datetime
    commission_earned: float

class ReferralCommissionsData(BaseModel):
    total_referrals: int
    total_commissions: float
    this_year_commissions: float
    referred_churches: List[ReferredChurchData]

class ReferralCommissionsResponse(BaseModel):
    success: bool
    data: ReferralCommissionsData
