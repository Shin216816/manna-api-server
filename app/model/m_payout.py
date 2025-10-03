from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.utils.database import Base

class Payout(Base):
    __tablename__ = "payouts"
    
    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False)
    
    # Payout details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    
    # Stripe Connect details
    stripe_transfer_id = Column(String(255), unique=True)
    stripe_account_id = Column(String(255))
    
    # Payout period
    period_start = Column(DateTime(timezone=True))
    period_end = Column(DateTime(timezone=True))
    
    # Processing details
    processed_at = Column(DateTime(timezone=True))
    failed_at = Column(DateTime(timezone=True))
    failure_reason = Column(Text)
    
    # Metadata
    description = Column(String(500))
    payout_metadata = Column(Text)  # JSON string for additional data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    church = relationship("Church")
    # referral_commissions = relationship("ReferralCommission", back_populates="payout")  # Commented out - no foreign key relationship
    
    def __repr__(self):
        return f"<Payout(id={self.id}, church_id={self.church_id}, amount={self.amount}, status='{self.status}')>"
