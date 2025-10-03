from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.utils.database import Base

class Consent(Base):
    __tablename__ = "consents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    version = Column(String(50), nullable=False)
    accepted_at = Column(DateTime(timezone=True), server_default=func.now())
    ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    text_snapshot = Column(Text, nullable=True)
    
    user = relationship("User")
    
    # Ensure only one consent per user
    __table_args__ = (
        UniqueConstraint('user_id', name='uq_consent_user_id'),
    )
