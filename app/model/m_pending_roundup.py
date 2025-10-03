"""
Pending Roundup Model

Stores pending roundup amounts before collection.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
from app.utils.database import Base


class PendingRoundup(Base):
    """
    Pending roundup amounts before collection
    """
    __tablename__ = "pending_roundups"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # User and transaction references
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    transaction_id = Column(String(255), nullable=False, index=True)  # Plaid transaction ID
    account_id = Column(String(255), nullable=False)  # Plaid account ID
    payout_id = Column(Integer, ForeignKey("donor_payouts.id"), nullable=True)  # Set when collected
    
    # Transaction details
    original_amount = Column(Numeric(10, 2), nullable=False)
    roundup_amount = Column(Numeric(10, 2), nullable=False)
    merchant_name = Column(String(255), nullable=True)
    category = Column(JSON, nullable=True)  # Store category array as JSON
    
    # Dates
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    collected_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(String(20), default="pending", nullable=False)  # pending, collected, cancelled
    
    # Relationships
    user = relationship("User", back_populates="pending_roundups")
    payout = relationship("DonorPayout", back_populates="pending_roundups")
    
    def __repr__(self):
        return f"<PendingRoundup(id={self.id}, user_id={self.user_id}, amount={self.roundup_amount})>"
