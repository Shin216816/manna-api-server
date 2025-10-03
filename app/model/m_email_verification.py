"""
Email Verification Model

Stores email verification and password reset tokens.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
from app.utils.database import Base


class EmailVerification(Base):
    """
    Email verification and password reset tokens
    """
    __tablename__ = "email_verifications"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to User
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Token details
    token = Column(String(255), unique=True, nullable=False, index=True)
    type = Column(String(50), nullable=False)  # email_verification, password_reset
    
    # Status and timing
    status = Column(String(20), default="pending", nullable=False)  # pending, verified, expired, used
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<EmailVerification(id={self.id}, user_id={self.user_id}, type={self.type}, status={self.status})>"
    
    @classmethod
    def get_by_token(cls, db, token: str):
        """Get verification record by token"""
        return db.query(cls).filter(cls.token == token).first()
    
    @classmethod
    def get_pending_by_user(cls, db, user_id: int, verification_type: str):
        """Get pending verification record for user"""
        return db.query(cls).filter(
            cls.user_id == user_id,
            cls.type == verification_type,
            cls.status == 'pending'
        ).first()
    
    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.now(timezone.utc) > self.expires_at
    
    def mark_verified(self, db):
        """Mark token as verified"""
        self.status = 'verified'
        self.verified_at = datetime.now(timezone.utc)
        db.commit()
    
    def mark_expired(self, db):
        """Mark token as expired"""
        self.status = 'expired'
        db.commit()
