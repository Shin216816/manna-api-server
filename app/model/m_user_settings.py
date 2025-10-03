from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.utils.database import Base

class UserSettings(Base):
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Notification settings
    notifications_enabled = Column(Boolean, default=True)
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    push_notifications = Column(Boolean, default=True)
    
    # Preference settings
    language = Column(String(10), default="en")  # en, es, fr
    timezone = Column(String(50), default="UTC")
    currency = Column(String(3), default="USD")  # USD, EUR, GBP, CAD
    theme = Column(String(10), default="light")  # light, dark, auto
    
    # Privacy settings
    privacy_share_analytics = Column(Boolean, default=True)
    privacy_share_profile = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserSettings(user_id={self.user_id})>"
