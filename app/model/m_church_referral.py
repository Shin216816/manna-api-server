"""
Church Referral Model

Handles church referral tracking and commission management
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.utils.database import Base
from datetime import datetime, timezone
import uuid


class ChurchReferral(Base):
    __tablename__ = "church_referrals"

    id = Column(Integer, primary_key=True, index=True)
    referring_church_id = Column(Integer, ForeignKey("churches.id"), nullable=False)
    referred_church_id = Column(Integer, ForeignKey("churches.id"), nullable=True)
    referral_code = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(20), default="active")  # active, inactive, expired
    commission_rate = Column(Float, default=0.05)  # 5% commission
    total_commission_earned = Column(Float, default=0.0)
    last_commission_payout = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))
    notes = Column(Text)

    # Relationships
    referring_church = relationship("Church", foreign_keys=[referring_church_id], back_populates="referring_referrals")
    referred_church = relationship("Church", foreign_keys=[referred_church_id], back_populates="referred_referrals")


# ReferralCommission class removed - using the one from m_referral.py to avoid table name conflicts