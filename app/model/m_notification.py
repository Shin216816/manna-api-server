"""
Notification Models

Stores notification data and user preferences
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum
from sqlalchemy.sql import func
from datetime import datetime, timezone
from app.utils.database import Base

class Notification(Base):
    """Notification model"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    type = Column(String(50), nullable=False)  # email, sms, push, in_app
    template_name = Column(String(100), nullable=False)
    subject = Column(String(255), nullable=True)
    body = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default='pending')  # pending, sent, failed
    priority = Column(String(20), nullable=False, default='normal')  # low, normal, high, urgent
    additional_data = Column(Text, nullable=True)  # JSON metadata
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# NotificationPreference model removed - using UserSettings for notification preferences
