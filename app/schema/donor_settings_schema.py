from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PauseResumeRequest(BaseModel):
    reason: Optional[str] = None
    pause_date: Optional[datetime] = None
    resume_date: Optional[datetime] = None

class PauseResumeData(BaseModel):
    pause: bool
    pause_date: Optional[datetime] = None
    resume_date: Optional[datetime] = None
    pause_reason: Optional[str] = None

class PauseResumeResponse(BaseModel):
    success: bool
    message: str
    data: PauseResumeData

class DonorSettingsData(BaseModel):
    pause: bool
    frequency: str
    multiplier: str
    monthly_cap: Optional[float] = None
    minimum_roundup: float
    cover_processing_fees: bool
    pause_date: Optional[datetime] = None
    resume_date: Optional[datetime] = None
    pause_reason: Optional[str] = None

class DonorSettingsResponse(BaseModel):
    success: bool
    data: DonorSettingsData
