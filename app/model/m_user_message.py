from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.utils.database import Base

class UserMessage(Base):
    __tablename__ = "user_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("church_messages.id"), nullable=False)
    
    # Message interaction
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    # message = relationship("ChurchMessage", back_populates="user_messages")  # Commented out - user_messages property doesn't exist on ChurchMessage
    
    def __repr__(self):
        return f"<UserMessage(user_id={self.user_id}, message_id={self.message_id})>"
