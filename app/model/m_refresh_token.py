from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta, timezone
from app.utils.database import Base
from typing import Optional
import secrets
import json


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, nullable=False)
    
    # Relationships
    user = relationship("User")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_used = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Session tracking
    device_info = Column(Text, nullable=True)  # JSON: device, OS, browser
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Security features
    rotation_count = Column(Integer, default=0, nullable=False)  # Track how many times rotated
    parent_token_id = Column(Integer, nullable=True)  # Link to previous token in rotation chain

    @staticmethod
    def create_token(user_id: int, db, generator=None, device_info: Optional[dict] = None, 
                    ip_address: Optional[str] = None, user_agent: Optional[str] = None,
                    parent_token_id: Optional[int] = None) -> 'RefreshToken':
        """Create a new refresh token with enhanced security"""
        if generator is None:
            token = secrets.token_urlsafe(32)
        else:
            token = generator()
            
        expires = datetime.now(timezone.utc) + timedelta(days=30)
        
        record = RefreshToken(
            user_id=user_id, 
            token=token, 
            expires_at=expires,
            device_info=json.dumps(device_info) if device_info else None,
            ip_address=ip_address,
            user_agent=user_agent,
            parent_token_id=parent_token_id
        )
        db.add(record)
        db.commit()
        return record

    @staticmethod
    def rotate_token(old_token: str, db, device_info: Optional[dict] = None, 
                    ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Optional['RefreshToken']:
        """Rotate refresh token - invalidate old and create new"""
        old_record = db.query(RefreshToken).filter(
            RefreshToken.token == old_token,
            RefreshToken.is_active == True,
            RefreshToken.expires_at > datetime.now(timezone.utc)
        ).first()
        
        if not old_record:
            return None
            
        # Mark old token as inactive
        old_record.is_active = False
        old_record.last_used = datetime.now(timezone.utc)
        
        # Create new token
        new_token = RefreshToken.create_token(
            user_id=old_record.user_id,
            db=db,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
            parent_token_id=old_record.id
        )
        new_token.rotation_count = old_record.rotation_count + 1
        
        db.commit()
        return new_token

    @staticmethod
    def invalidate_token_chain(token: str, db):
        """Invalidate entire token rotation chain for security"""
        token_record = db.query(RefreshToken).filter(RefreshToken.token == token).first()
        if not token_record:
            return
            
        # Find all tokens in the chain (parent and children)
        user_tokens = db.query(RefreshToken).filter(
            RefreshToken.user_id == token_record.user_id,
            RefreshToken.is_active == True
        ).all()
        
        for token_obj in user_tokens:
            token_obj.is_active = False
            
        db.commit()

    @staticmethod
    def cleanup_expired(db):
        """Remove expired refresh tokens"""
        now = datetime.now(timezone.utc)
        expired_tokens = db.query(RefreshToken).filter(
            RefreshToken.expires_at < now
        ).all()
        
        for token in expired_tokens:
            db.delete(token)
            
        db.commit()
        return len(expired_tokens)

    @staticmethod
    def get_user_sessions(user_id: int, db):
        """Get all active sessions for a user"""
        return db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_active == True,
            RefreshToken.expires_at > datetime.now(timezone.utc)
        ).all()

    def to_dict(self):
        """Convert to dictionary for API responses"""
        device_data = json.loads(str(self.device_info)) if self.device_info else {}
        
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "device_info": device_data,
            "ip_address": self.ip_address,
            "is_current": False  # Will be set by caller
        }
