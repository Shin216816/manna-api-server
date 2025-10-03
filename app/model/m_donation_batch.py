from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
from app.utils.database import Base

class DonationBatch(Base):
    """
    Donation batch model for tracking collected round-ups
    """
    __tablename__ = "donation_batches"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # User and church references
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    
    # Batch details
    batch_number = Column(String(50), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    # total_amount = Column(Numeric(10, 2), nullable=False)  # Total amount including fees - removed as it doesn't exist in DB
    transaction_count = Column(Integer, default=0, nullable=False)
    
    # Status tracking
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending, processing, completed, failed
    collection_date = Column(DateTime(timezone=True), nullable=False, index=True)
    payout_date = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Processing details
    stripe_transfer_id = Column(String(255), nullable=True, index=True)
    processing_fee = Column(Numeric(10, 2), default=0.0, nullable=False)
    net_amount = Column(Numeric(10, 2), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=datetime.now, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="donation_batches")
    church = relationship("Church", back_populates="donation_batches")
    # roundup_transactions relationship removed - data is now stored directly in DonationBatch

    def __repr__(self):
        return f"<DonationBatch(id={self.id}, amount={self.amount}, status={self.status})>"