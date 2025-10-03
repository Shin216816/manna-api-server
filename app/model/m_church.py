from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
from app.utils.database import Base


class Church(Base):
    """
    Optimized church model with integrated KYC and simplified structure
    """
    __tablename__ = "churches"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic church information
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=True)  # Legal business name
    ein = Column(String(20), nullable=True, index=True)
    website = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)  # Main address field
    pastor_name = Column(String(255), nullable=True)  # Pastor name
    primary_purpose = Column(Text, nullable=True)  # Primary business purpose
    
    # Address
    address_line_1 = Column(String(255), nullable=True)
    address_line_2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(10), nullable=True)
    zip_code = Column(String(20), nullable=True)
    country = Column(String(2), default="US", nullable=False)
    
    # Additional church information - stored in KYC data JSON
    # denomination = Column(String(255), nullable=True)  # Removed - not in DB schema
    # congregation_size = Column(String(50), nullable=True)  # Removed - not in DB schema
    
    # KYC and verification status
    kyc_status = Column(String(20), default="not_submitted", nullable=False)  # not_submitted, pending, approved, rejected
    kyc_data = Column(JSON, nullable=True)  # Store KYC form data as JSON
    kyc_state = Column(String(20), nullable=True)  # KYC state for onboarding
    status = Column(String(20), default="pending", nullable=False)  # Church status
    is_active = Column(Boolean, default=False, nullable=False)  # Active status
    
    # KYC compliance fields
    formation_date = Column(DateTime, nullable=True)
    formation_state = Column(String(50), nullable=True)
    
    # Required document paths
    articles_of_incorporation = Column(Text, nullable=True)
    tax_exempt_letter = Column(Text, nullable=True)
    bank_statement = Column(Text, nullable=True)
    board_resolution = Column(Text, nullable=True)
    
    # Attestation flags
    tax_exempt = Column(Boolean, default=False, nullable=False)
    anti_terrorism = Column(Boolean, default=False, nullable=False)
    legitimate_entity = Column(Boolean, default=False, nullable=False)
    consent_checks = Column(Boolean, default=False, nullable=False)
    beneficial_ownership_disclosure = Column(Boolean, default=False, nullable=False)
    information_accuracy = Column(Boolean, default=False, nullable=False)
    penalty_of_perjury = Column(Boolean, default=False, nullable=False)
    
    # Stripe integration
    stripe_account_id = Column(String(100), unique=True, nullable=True, index=True)
    charges_enabled = Column(Boolean, default=False, nullable=False)
    payouts_enabled = Column(Boolean, default=False, nullable=False)
    
    # Referral system
    referral_code = Column(String(20), unique=True, nullable=True, index=True)
    
    # Financial tracking
    total_received = Column(Numeric(12, 2), default=0.00, nullable=False)
    
    # KYC approval/rejection tracking
    kyc_approved_at = Column(DateTime(timezone=True), nullable=True)
    kyc_rejected_at = Column(DateTime(timezone=True), nullable=True)
    kyc_rejection_reason = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    disabled_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    kyc_submitted_at = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    church_admins = relationship("ChurchAdmin", back_populates="church", cascade="all, delete-orphan")
    # roundup_settings removed - using donation_preferences instead
    donor_payouts = relationship("DonorPayout", back_populates="church")
    church_payouts = relationship("ChurchPayout", back_populates="church")
    beneficial_owners = relationship("BeneficialOwner", back_populates="church", cascade="all, delete-orphan")
    
    # Referral relationships
    referring_referrals = relationship("ChurchReferral", foreign_keys="ChurchReferral.referring_church_id", back_populates="referring_church")
    referred_referrals = relationship("ChurchReferral", foreign_keys="ChurchReferral.referred_church_id", back_populates="referred_church")
    
    # Donation relationships
    donation_batches = relationship("DonationBatch", back_populates="church")

    def __repr__(self):
        return f"<Church(id={self.id}, name='{self.name}', kyc_status='{self.kyc_status}')>"

    @classmethod
    def get_by_referral_code(cls, db, referral_code: str):
        """Get church by referral code"""
        return db.query(cls).filter(cls.referral_code == referral_code).first()

    @classmethod
    def get_by_stripe_account(cls, db, stripe_account_id: str):
        """Get church by Stripe account ID"""
        return db.query(cls).filter(cls.stripe_account_id == stripe_account_id).first()

    def get_admins(self, db):
        """Get all active admins for this church"""
        from .m_user import User
        return db.query(User).filter(
            User.church_id == self.id,
            User.is_active == True,
            User.role.in_(["church_admin", "manna_admin"])
        ).all()

    def get_primary_admin(self, db):
        """Get the primary admin for this church"""
        from .m_user import User
        return db.query(User).filter(
            User.church_id == self.id,
            User.is_active == True,
            User.role == "church_admin"
        ).first()

    def can_receive_payouts(self) -> bool:
        """Check if church can receive payouts"""
        return (
            self.kyc_status == "approved" and
            self.charges_enabled and
            self.payouts_enabled and
            self.stripe_account_id is not None
        )

    def to_dict(self, include_sensitive=False) -> dict:
        """Convert church to dictionary for API responses"""
        data = {
            "id": self.id,
            "name": self.name,
            "website": self.website,
            "phone": self.phone,
            "email": self.email,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "kyc_status": self.kyc_status,
            "charges_enabled": self.charges_enabled,
            "payouts_enabled": self.payouts_enabled,
            "referral_code": self.referral_code,
            "total_received": float(self.total_received) if self.total_received else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None
        }
        
        if include_sensitive:
            data.update({
                "ein": self.ein,
                "address_line_1": self.address_line_1,
                "address_line_2": self.address_line_2,
                "zip_code": self.zip_code,
                "stripe_account_id": self.stripe_account_id,
                "kyc_data": self.kyc_data
            })
            
        return data

