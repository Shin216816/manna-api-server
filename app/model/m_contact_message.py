from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.sql import func
import enum
from app.utils.database import Base

class ContactCategory(str, enum.Enum):
    GENERAL = "general"
    SUPPORT = "support"
    PARTNERSHIP = "partnership"
    TECHNICAL = "technical"
    FEEDBACK = "feedback"

class ContactPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class ContactMessage(Base):
    __tablename__ = "contact_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Visitor information
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    
    # Message content
    subject = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(Enum(ContactCategory), default=ContactCategory.GENERAL)
    priority = Column(Enum(ContactPriority), default=ContactPriority.MEDIUM)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ContactMessage(id={self.id}, subject='{self.subject}', email='{self.email}')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "subject": self.subject,
            "message": self.message,
            "category": self.category.value if self.category else None,
            "priority": self.priority.value if self.priority else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
