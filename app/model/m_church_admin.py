from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from app.utils.database import Base
from datetime import datetime, timezone


class ChurchAdmin(Base):
    __tablename__ = "church_admins"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Core references
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False)
    
    # Admin details
    admin_name = Column(String(255), nullable=True)  # Display name (can be different from user name)
    role = Column(String(50), default="admin")  # admin, moderator, treasurer, pastor, etc.
    permissions = Column(JSON, nullable=True)  # JSON array of specific permissions
    
    # Admin status
    is_active = Column(Boolean, default=True)
    is_primary_admin = Column(Boolean, default=False)  # Primary admin for the church
    can_manage_finances = Column(Boolean, default=True)
    can_manage_members = Column(Boolean, default=True)
    can_manage_settings = Column(Boolean, default=True)
    
    # Contact information (can override user contact info)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    
    # Stripe Identity verification fields (KYC for payouts)
    stripe_identity_session_id = Column(String(255), unique=True, nullable=True)
    identity_verification_status = Column(String, default="not_started")  # not_started, pending, verified, cancelled, failed
    identity_verification_date = Column(DateTime(timezone=True), nullable=True)
    
    # Admin metadata
    admin_notes = Column(Text, nullable=True)
    admin_metadata = Column(JSON, nullable=True)  # Additional admin-specific data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_activity = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="church_admin")
    church = relationship("Church", back_populates="church_admins")
    
    def __repr__(self):
        return f"<ChurchAdmin(id={self.id}, user_id={self.user_id}, church_id={self.church_id}, role='{self.role}')>"
    
    @property
    def display_name(self):
        """Get the display name, fallback to user name if not set"""
        if self.admin_name:
            return self.admin_name
        if self.user:
            return f"{self.user.first_name} {self.user.last_name}".strip()
        return "Unknown Admin"
    
    @property
    def email(self):
        """Get the contact email, fallback to user email if not set"""
        if self.contact_email:
            return self.contact_email
        if self.user:
            return self.user.email
        return None
    
    @property
    def phone(self):
        """Get the contact phone, fallback to user phone if not set"""
        if self.contact_phone:
            return self.contact_phone
        if self.user:
            return self.user.phone
        return None
    
    def has_permission(self, permission):
        """Check if admin has a specific permission"""
        if self.is_primary_admin:
            return True  # Primary admin has all permissions
        
        if not self.permissions:
            return False
        
        return permission in self.permissions
    
    def can_manage(self, area):
        """Check if admin can manage a specific area"""
        if area == "finances":
            return self.can_manage_finances
        elif area == "members":
            return self.can_manage_members
        elif area == "settings":
            return self.can_manage_settings
        return False
