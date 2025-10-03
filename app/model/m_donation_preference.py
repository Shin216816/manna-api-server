from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.utils.database import Base

class DonationFrequency(str, enum.Enum):
    biweekly = "biweekly"  # Bi-weekly
    monthly = "monthly"    # 1-month

class RoundupMultiplier(str, enum.Enum):
    one_x = "1x"
    two_x = "2x"
    three_x = "3x"
    five_x = "5x"
    
    @classmethod
    def _missing__(cls, value):
        for member in cls.__members__.values():
            if member.value == value:
                return member
        return None

class DonationPreference(Base):
    __tablename__ = "donation_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    church_id = Column(Integer, ForeignKey("churches.id"), unique=True, nullable=True)

    frequency = Column(String, default="biweekly")
    multiplier = Column(String, default="1x")
    target_church_id = Column(Integer, ForeignKey("churches.id"), nullable=True)
    pause = Column(Boolean, default=False)
    cover_processing_fees = Column(Boolean, default=False)
    roundups_enabled = Column(Boolean, default=True, nullable=False)
    minimum_roundup = Column(Numeric(10, 2), default=1.00, nullable=False)
    monthly_cap = Column(Numeric(10, 2), nullable=True)
    exclude_categories = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=datetime.now)

    user = relationship("User", foreign_keys=[user_id])
    church = relationship("Church", foreign_keys=[church_id])
    target_church = relationship("Church", foreign_keys=[target_church_id])
