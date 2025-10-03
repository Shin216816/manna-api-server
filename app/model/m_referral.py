from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.utils.database import Base
from datetime import datetime

# ReferralCode class removed - using ChurchReferral table instead
class ReferralCommission(Base):
    __tablename__ = "referral_commissions"
    
    id = Column(Integer, primary_key=True, index=True)
    referring_church_id = Column(Integer, ForeignKey("churches.id"), nullable=False)
    referred_church_id = Column(Integer, ForeignKey("churches.id"), nullable=False)
    amount = Column(Float, nullable=False, default=0.0)
    commission_rate = Column(Float, nullable=False, default=0.05)  # 5% commission
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships removed - can be queried directly via foreign keys if needed