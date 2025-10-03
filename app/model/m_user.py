from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
from app.utils.database import Base
from app.utils.security import verify_password, hash_password


class User(Base):
    """
    Unified user model for all user types in the MVP.
    Supports congregants, church admins, and manna admins.
    """
    __tablename__ = "users"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic profile
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    
    # Authentication
    password_hash = Column(Text, nullable=True)  # Nullable for OAuth-only users
    
    # OAuth provider IDs
    google_id = Column(String(100), unique=True, nullable=True, index=True)
    apple_id = Column(String(100), unique=True, nullable=True, index=True)
    
    # Role management - simplified for MVP
    role = Column(String(20), nullable=False, default="donor")  # donor, church_admin, manna_admin
    
    # Church association - direct relationship
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=True, index=True)
    
    # Stripe integration
    stripe_customer_id = Column(String(100), unique=True, nullable=True, index=True)
    stripe_default_payment_method_id = Column(String(100), nullable=True)
    
    # Profile
    profile_picture_url = Column(String(500), nullable=True)
    
    # Status flags
    is_active = Column(Boolean, default=True, nullable=False)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    is_phone_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    # plaid_transactions relationship removed - using on-demand Plaid API fetching
    # roundup_transactions relationship removed - using DonationBatch instead
    donation_batches = relationship("DonationBatch", back_populates="user")
    
    # Relationships
    plaid_items = relationship("PlaidItem", back_populates="user", cascade="all, delete-orphan")
    # roundup_settings removed - using donation_preferences instead
    donor_payouts = relationship("DonorPayout", back_populates="user")
    pending_roundups = relationship("PendingRoundup", back_populates="user")
    # payment_methods relationship removed - using Stripe API directly
    church_admin = relationship("ChurchAdmin", back_populates="user", cascade="all, delete-orphan")
    donor_settings = relationship("DonorSettings", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"

    @classmethod
    def get_by_email(cls, db, email: str):
        """Get user by email address"""
        return db.query(cls).filter(cls.email == email).first()

    @classmethod
    def get_by_id(cls, db, user_id: int):
        """Get user by ID"""
        return db.query(cls).filter(cls.id == user_id).first()

    @classmethod
    def get_by_google_id(cls, db, google_id: str):
        """Get user by Google OAuth ID"""
        return db.query(cls).filter(cls.google_id == google_id).first()

    @classmethod
    def get_by_phone(cls, db, phone: str):
        """Get user by phone number"""
        return db.query(cls).filter(cls.phone == phone).first()

    @classmethod
    def get_by_apple_id(cls, db, apple_id: str):
        """Get user by Apple OAuth ID"""
        return db.query(cls).filter(cls.apple_id == apple_id).first()

    def verify_password(self, plain_password: str) -> bool:
        """Verify password against stored hash"""
        if not self.password_hash:
            return False
        return verify_password(plain_password, self.password_hash)

    def has_password(self) -> bool:
        """Check if user has a password set"""
        return bool(self.password_hash)

    def set_password(self, plain_password: str):
        """Set password hash"""
        self.password_hash = hash_password(plain_password)
        self.updated_at = datetime.now(timezone.utc)

    def has_role(self, required_role: str) -> bool:
        """Check if user has specific role or higher privileges"""
        role_hierarchy = ["donor", "church_admin", "manna_admin"]
        
        if self.role not in role_hierarchy or required_role not in role_hierarchy:
            return False
            
        user_level = role_hierarchy.index(self.role)
        required_level = role_hierarchy.index(required_role)
        
        return user_level >= required_level

    def get_primary_church(self, db):
        """Get the primary church for this user"""
        if not self.church_id:
            return None
        from .m_church import Church
        return db.query(Church).filter(Church.id == self.church_id).first()

    def get_managed_churches(self, db):
        """Get all churches this user can manage (simplified - only their assigned church)"""
        if not self.church_id or self.role not in ["church_admin", "manna_admin"]:
            return []
        from .m_church import Church
        church = db.query(Church).filter(Church.id == self.church_id).first()
        return [church] if church else []

    def get_all_churches(self, db):
        """Get all churches this user is a member of (simplified - only their assigned church)"""
        if not self.church_id:
            return []
        from .m_church import Church
        church = db.query(Church).filter(Church.id == self.church_id).first()
        return [church] if church else []

    def get_church_membership(self, db, church_id: int):
        """Check if user belongs to specific church"""
        return self.church_id == church_id

    def is_member_of_church(self, db, church_id: int) -> bool:
        """Check if user is a member of a specific church"""
        return self.church_id == church_id

    def get_church_role(self, db, church_id: int) -> str:
        """Get user's role in a specific church"""
        if self.church_id != church_id:
            return None
        return self.role

    def add_church_membership(self, db, church_id: int, role: str = "donor"):
        """Add user to a church with specified role"""
        self.church_id = church_id
        self.role = role
        self.updated_at = datetime.now(timezone.utc)
        db.commit()
        return True

    def remove_church_membership(self, db, church_id: int):
        """Remove user from a church"""
        if self.church_id == church_id:
            self.church_id = None
            self.updated_at = datetime.now(timezone.utc)
            db.commit()
            return True
        return False

    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}".strip()

    def to_dict(self, include_sensitive=False) -> dict:
        """Convert user to dictionary for API responses"""
        data = {
            "id": self.id,
            "email": self.email,
            "phone": self.phone,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "role": self.role,
            "is_active": self.is_active,
            "is_email_verified": self.is_email_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }
        
        if include_sensitive:
            data.update({
                "google_id": self.google_id,
                "apple_id": self.apple_id,
                "stripe_customer_id": self.stripe_customer_id
            })
            
        return data
