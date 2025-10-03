"""
Donor Settings Model

Stores donor-specific settings for roundup processing and donation preferences.
"""

from sqlalchemy import Column, Integer, String, DateTime, Numeric, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.utils.database import Base


class DonorSettings(Base):
    __tablename__ = "donor_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Roundup settings
    frequency = Column(String(20), default="biweekly", nullable=False)  # biweekly, monthly
    multiplier = Column(String(10), default="1x", nullable=False)  # 1x, 2x, 3x, etc.
    monthly_cap = Column(Numeric(10, 2), nullable=True)  # Monthly cap in dollars
    pause_giving = Column(Boolean, default=False, nullable=False)
    
    # Processing settings
    cover_processing_fees = Column(Boolean, default=False, nullable=False)
    auto_collect = Column(Boolean, default=True, nullable=False)
    
    # Notification settings
    email_notifications = Column(Boolean, default=True, nullable=False)
    sms_notifications = Column(Boolean, default=False, nullable=False)
    collection_reminders = Column(Boolean, default=True, nullable=False)
    
    # Privacy settings
    share_impact_data = Column(Boolean, default=True, nullable=False)
    anonymous_donations = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="donor_settings")