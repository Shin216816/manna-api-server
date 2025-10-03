from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
from app.utils.database import Base


# RoundupSettings class removed - using DonationPreference instead


class DonorPayout(Base):
    """
    Individual donor donation records - stores each donor's contribution with roundup details
    Stripe transaction details are fetched via API, not stored locally
    """
    __tablename__ = "donor_payouts"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    
    # Donation details (business logic, not Stripe data)
    donation_amount = Column(Numeric(10, 2), nullable=False)  # Final donation amount after roundup multiplier
    roundup_multiplier = Column(Numeric(3, 1), nullable=False, default=2.0)  # 2x, 3x, etc.
    base_roundup_amount = Column(Numeric(10, 2), nullable=False)  # Original roundup before multiplier
    plaid_transaction_count = Column(Integer, nullable=False, default=0)  # Number of Plaid transactions rounded up
    
    # Collection period
    collection_period = Column(String(50), nullable=False)  # e.g., "2024-01-01_2024-01-15"
    donation_type = Column(String(20), nullable=False, default="roundup")  # roundup, manual, recurring
    
    # Stripe reference removed - payment details fetched via API when needed
    # stripe_payment_intent_id column was removed in optimize_donor_payment_flow migration
    
    # Processing status
    status = Column(String(20), nullable=False, default="pending")  # pending, processing, completed, failed, refunded
    # failure_reason column doesn't exist in database - removed
    
    # Donation metadata (business context, not Stripe data)
    donation_summary = Column(JSON, nullable=True)  # Roundup breakdown, merchant categories, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    # failed_at column doesn't exist in database - removed
    allocated_at = Column(DateTime(timezone=True), nullable=True)  # When included in donation batch
    
    # Relationships
    user = relationship("User", back_populates="donor_payouts")
    church = relationship("Church", back_populates="donor_payouts")
    pending_roundups = relationship("PendingRoundup", back_populates="payout")
    # payout_allocations removed - using direct church_id relationship instead

    def __repr__(self):
        return f"<DonorPayout(id={self.id}, user_id={self.user_id}, donation=${self.donation_amount}, multiplier={self.roundup_multiplier}x, status='{self.status}')>"

    @classmethod
    def get_by_user(cls, db, user_id: int, limit: int = 50):
        """Get donor payouts for a user"""
        return db.query(cls).filter(cls.user_id == user_id).order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_by_church(cls, db, church_id: int, limit: int = 100):
        """Get donor payouts for a church"""
        return db.query(cls).filter(cls.church_id == church_id).order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_pending_for_batch(cls, db, church_id: int):
        """Get completed donor payouts that haven't been included in donation batch yet"""
        return db.query(cls).filter(
            cls.church_id == church_id,
            cls.status == "completed",
            cls.allocated_at.is_(None)  # Not yet included in donation batch
        ).all()

    def mark_completed(self, db):
        """Mark donation as completed (Stripe transaction succeeded)"""
        self.status = "completed"
        self.processed_at = datetime.now(timezone.utc)
        db.commit()
    
    def mark_allocated(self, db):
        """Mark donation as included in donation batch"""
        self.allocated_at = datetime.now(timezone.utc)
        db.commit()

    def mark_failed(self, db, failure_reason: str = None):
        """Mark payout as failed"""
        self.status = "failed"
        # failed_at and failure_reason columns don't exist in database
        db.commit()

    def to_dict(self) -> dict:
        """Convert donation record to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "church_id": self.church_id,
            "donation_amount": float(self.donation_amount),
            "roundup_multiplier": float(self.roundup_multiplier),
            "base_roundup_amount": float(self.base_roundup_amount),
            "plaid_transaction_count": self.plaid_transaction_count,
            "collection_period": self.collection_period,
            "donation_type": self.donation_type,
            "status": self.status,
            "stripe_payment_intent_id": self.stripe_payment_intent_id,
            "donation_summary": self.donation_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "allocated_at": self.allocated_at.isoformat() if self.allocated_at else None
        }
    
    def get_stripe_details(self):
        """Get Stripe transaction details via API (not stored locally)"""
        if not self.stripe_payment_intent_id:
            return None
        # This would call Stripe API to get current transaction details
        # including amount, fees, charge_id, etc.
        # Implementation depends on stripe_service
        pass


class ChurchPayout(Base):
    """
    Records church payout transactions - created AFTER successful Stripe transfer
    
    CORRECT WORKFLOW:
    1. Calculate church earnings from donor_payouts (minus system fees)
    2. Execute Stripe transfer to church
    3. If transfer succeeds, create ChurchPayout record with stripe_transfer_id
    4. Mark donor_payouts as allocated
    """
    __tablename__ = "church_payouts"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    
    # Financial calculation (from donor_payouts)
    gross_donation_amount = Column(Numeric(12, 2), nullable=False)  # Sum of donor donations
    system_fee_amount = Column(Numeric(10, 2), nullable=False, default=0.00)  # Manna's platform fee
    system_fee_percentage = Column(Numeric(5, 4), nullable=False, default=0.05)  # Default 5% platform fee
    net_payout_amount = Column(Numeric(12, 2), nullable=False)  # Amount actually sent to church
    
    # Payout summary
    donor_count = Column(Integer, nullable=False, default=0)  # Number of unique donors included
    donation_count = Column(Integer, nullable=False, default=0)  # Total donations included
    
    # Payout period
    period_start = Column(String(20), nullable=False)  # "2024-01-01"
    period_end = Column(String(20), nullable=False)  # "2024-01-31"
    
    # Stripe transfer details (REQUIRED - payout created only after successful transfer)
    stripe_transfer_id = Column(String(100), unique=True, nullable=False, index=True)  # Required - proves transfer succeeded
    status = Column(String(20), nullable=False, default="completed")  # completed (default), reversed, failed
    failure_reason = Column(Text, nullable=True)  # Only for reversals or failures
    
    # Detailed breakdown (for analytics)
    payout_breakdown = Column(JSON, nullable=True)  # Per-donor breakdown, category analysis
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    church = relationship("Church", back_populates="church_payouts")
    # payout_allocations removed - using direct church_id relationship instead
    # referral_commissions relationship removed - ReferralCommission model deprecated
    # Use ChurchReferral model for commission tracking instead

    def __repr__(self):
        return f"<ChurchPayout(id={self.id}, church_id={self.church_id}, net_amount=${self.net_payout_amount}, transfer_id={self.stripe_transfer_id})>"

    @classmethod
    def get_by_church(cls, db, church_id: int, limit: int = 50):
        """Get church payouts for a church"""
        return db.query(cls).filter(cls.church_id == church_id).order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def create_after_successful_transfer(cls, db, church_id: int, donor_payouts: list, stripe_transfer_id: str, 
                                       system_fee_percentage: float = 0.05):
        """Create ChurchPayout record AFTER successful Stripe transfer"""
        # Calculate totals from donor payouts
        gross_amount = sum(float(dp.donation_amount) for dp in donor_payouts)
        system_fee = gross_amount * system_fee_percentage
        net_amount = gross_amount - system_fee
        
        # Get period boundaries
        periods = [dp.collection_period for dp in donor_payouts]
        period_start = min(periods)
        period_end = max(periods)
        
        # Generate donor breakdown
        donor_breakdown = []
        for dp in donor_payouts:
            donor_breakdown.append({
                "user_id": dp.user_id,
                "donation_amount": float(dp.donation_amount),
                "roundup_multiplier": float(dp.roundup_multiplier),
                "transaction_count": dp.plaid_transaction_count
            })
        
        # Generate category breakdown (placeholder - would need actual category data)
        category_breakdown = {
            "youth_programs": round(gross_amount * 0.3, 2),
            "community_outreach": round(gross_amount * 0.25, 2),
            "facilities": round(gross_amount * 0.2, 2),
            "missions": round(gross_amount * 0.15, 2),
            "events": round(gross_amount * 0.1, 2)
        }
        
        # Create payout record
        payout = cls(
            church_id=church_id,
            gross_donation_amount=gross_amount,
            system_fee_amount=system_fee,
            system_fee_percentage=system_fee_percentage,
            net_payout_amount=net_amount,
            donor_count=len(set(dp.user_id for dp in donor_payouts)),
            donation_count=len(donor_payouts),
            period_start=period_start,
            period_end=period_end,
            stripe_transfer_id=stripe_transfer_id,
            status="completed",
            payout_breakdown={
                "donor_breakdown": donor_breakdown,
                "category_breakdown": category_breakdown
            }
        )
        
        db.add(payout)
        db.flush()  # Get the ID
        
        # Mark all donor payouts as allocated
        for dp in donor_payouts:
            dp.mark_allocated(db)
        
        db.commit()
        return payout

    def mark_failed(self, db, failure_reason: str = None):
        """Mark payout as failed"""
        self.status = "failed"
        # failed_at and failure_reason columns don't exist in database
        db.commit()

    def to_dict(self) -> dict:
        """Convert payout to dictionary"""
        return {
            "id": self.id,
            "church_id": self.church_id,
            "gross_donation_amount": float(self.gross_donation_amount),
            "system_fee_amount": float(self.system_fee_amount),
            "system_fee_percentage": float(self.system_fee_percentage),
            "net_payout_amount": float(self.net_payout_amount),
            "donor_count": self.donor_count,
            "donation_count": self.donation_count,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "status": self.status,
            "stripe_transfer_id": self.stripe_transfer_id,
            "failure_reason": self.failure_reason,
            "payout_breakdown": self.payout_breakdown,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None
        }


# PayoutAllocation class removed - using direct church_id relationship and allocated_at timestamp instead
# This eliminates the complex many-to-many junction table and simplifies payout tracking
