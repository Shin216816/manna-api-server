from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.utils.database import Base

class MessageType(str, enum.Enum):
    ANNOUNCEMENT = "announcement"
    EVENT = "event"
    PRAYER_REQUEST = "prayer_request"
    WELCOME = "welcome"
    GENERAL = "general"

class MessagePriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class ChurchMessage(Base):
    __tablename__ = "church_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False)
    
    # Message content
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    type = Column(Enum(MessageType), default=MessageType.GENERAL)
    priority = Column(Enum(MessagePriority), default=MessagePriority.MEDIUM)
    
    # Message status
    is_active = Column(Boolean, default=True)
    is_published = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))
    
    # Relationships
    # church = relationship("Church", back_populates="messages")  # Commented out - messages property doesn't exist on Church
    # user_messages = relationship("UserMessage", back_populates="message")  # Commented out - message property doesn't exist on UserMessage
    
    def __repr__(self):
        return f"<ChurchMessage(id={self.id}, title='{self.title}')>"
