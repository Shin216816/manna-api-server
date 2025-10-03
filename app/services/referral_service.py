"""
Referral Service

Handles referral business logic including:
- Referral code generation and validation
- Commission calculations
- Referral status management
"""

import logging
import random
import string
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from app.model.m_church_referral import ChurchReferral
from app.model.m_church import Church
# from app.model.m_referral_commission import ReferralCommission  # Removed - redundant with church_referrals
from app.core.exceptions import ReferralError


class ReferralService:
    """Service for managing church referrals and commissions"""
    
    @staticmethod
    def generate_referral_code(church_id: int, db: Session) -> str:
        """Generate a unique referral code for a church"""
        max_attempts = 10
        attempts = 0
        
        while attempts < max_attempts:
            # Generate referral code: CHURCH_{church_id}_{random_string}
            random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            referral_code = f"CHURCH_{church_id}_{random_string}"
            
            # Check if code already exists
            existing = db.query(ChurchReferral).filter(ChurchReferral.referral_code == referral_code).first()
            if not existing:
                return referral_code
            
            attempts += 1
        
        raise ReferralError("Failed to generate unique referral code after maximum attempts")
    
    @staticmethod
    def get_or_create_referral_code(church_id: int, db: Session) -> ChurchReferral:
        """Get existing referral code or create a new one for a church"""
        try:
            # Check if church exists
            church = db.query(Church).filter(Church.id == church_id).first()
            if not church:
                raise ReferralError(f"Church {church_id} not found")
            
            # Look for existing referral code where this church is the referring church
            referral = db.query(ChurchReferral).filter(
                ChurchReferral.referring_church_id == church_id,
                ChurchReferral.referral_code.isnot(None)
            ).first()
            
            if not referral:
                # Generate new referral code
                referral_code = ReferralService.generate_referral_code(church_id, db)
                
                referral = ChurchReferral(
                    referring_church_id=church_id,
                    referred_church_id=church_id,  # Placeholder, will be updated when used
                    referral_code=referral_code,
                    commission_rate=0.10  # 10% default commission
                )
                db.add(referral)
                db.commit()
                db.refresh(referral)
                
                info(f"Created new referral code {referral_code} for church {church_id}")
            
            return referral
            
        except Exception as e:
            error(f"Error in get_or_create_referral_code: {str(e)}")
            raise ReferralError(f"Failed to get or create referral code: {str(e)}")
    
    @staticmethod
    def validate_referral_code(referral_code: str, db: Session) -> Optional[ChurchReferral]:
        """Validate a referral code and return the referral if valid"""
        try:
            referral = db.query(ChurchReferral).filter(
                ChurchReferral.referral_code == referral_code
            ).first()
            
            if referral and not referral.is_active():
                return None
            
            if not referral:
                return None
            
            # Check if referral is expired (1 year after creation)
            if referral.created_at:
                expiry_date = referral.created_at.replace(year=referral.created_at.year + 1)
                if datetime.now(timezone.utc) > expiry_date:
                    referral.status = "expired"
                    referral.is_active = False
                    db.commit()
                    return None
            
            return referral
            
        except Exception as e:
            error(f"Error validating referral code: {str(e)}")
            return None
    
    @staticmethod
    def create_referral_relationship(
        referral_code: str, 
        referred_church_id: int, 
        db: Session
    ) -> ChurchReferral:
        """Create a referral relationship when a church uses a referral code"""
        try:
            # Validate referral code
            referral = ReferralService.validate_referral_code(referral_code, db)
            if not referral:
                raise ReferralError("Invalid or expired referral code")
            
            # Check for self-referral
            if referral.referring_church_id == referred_church_id:
                raise ReferralError("Cannot refer yourself")
            
            # Check if referral already exists
            existing = db.query(ChurchReferral).filter(
                ChurchReferral.referring_church_id == referral.referring_church_id,
                ChurchReferral.referred_church_id == referred_church_id
            ).first()
            
            if existing:
                raise ReferralError("Referral relationship already exists")
            
            # Update the referral with the referred church
            referral.referred_church_id = referred_church_id
            referral.status = "active"
            referral.activated_at = datetime.now(timezone.utc)
            
            db.commit()
            db.refresh(referral)
            
            info(f"Created referral relationship: {referral.referring_church_id} -> {referred_church_id}")
            return referral
            
        except Exception as e:
            error(f"Error creating referral relationship: {str(e)}")
            raise ReferralError(f"Failed to create referral relationship: {str(e)}")
    
    @staticmethod
    def calculate_commission(
        referral_id: int, 
        base_amount: float, 
        db: Session
    ) -> Dict[str, Any]:
        """Calculate commission for a referral based on base amount"""
        try:
            referral = db.query(ChurchReferral).filter(ChurchReferral.id == referral_id).first()
            if not referral:
                raise ReferralError(f"Referral {referral_id} not found")
            
            if not referral.is_active():
                raise ReferralError("Referral cannot earn commission (expired, inactive, or already paid)")
            
            # Calculate commission
            commission_rate = float(referral.commission_rate)
            commission_amount = base_amount * commission_rate
            
            # Update referral record with commission info (no separate commission table needed)
            referral.total_commission_earned = (referral.total_commission_earned or 0) + commission_amount
            referral.payout_status = "pending"
            db.commit()
            
            return {
                "referral_id": referral_id,
                "church_id": referral.referring_church_id,
                "base_amount": base_amount,
                "commission_rate": commission_rate,
                "commission_amount": commission_amount,
                "status": "pending"
            }
            
        except Exception as e:
            error(f"Error calculating commission: {str(e)}")
            raise ReferralError(f"Failed to calculate commission: {str(e)}")
    
    @staticmethod
    def get_church_referral_stats(church_id: int, db: Session) -> Dict[str, Any]:
        """Get comprehensive referral statistics for a church"""
        try:
            # Get referrals made by this church
            referrals_made = db.query(ChurchReferral).filter(
                ChurchReferral.referring_church_id == church_id
            ).all()
            
            # Get referrals received by this church
            referrals_received = db.query(ChurchReferral).filter(
                ChurchReferral.referred_church_id == church_id
            ).all()
            
            # Calculate statistics from church_referrals table (no separate commissions table)
            total_referrals_made = len(referrals_made)
            active_referrals = len([r for r in referrals_made if r.is_active() and r.payout_status != "completed"])
            completed_referrals = len([r for r in referrals_made if r.payout_status == "completed"])
            
            # Calculate commission totals from referrals_made
            total_commission_earned = sum(float(r.total_commission_earned or 0) for r in referrals_made)
            paid_commission = sum(float(r.payout_amount or 0) for r in referrals_made if r.commission_paid)
            pending_commission = sum(float(r.total_commission_earned or 0) for r in referrals_made if not r.commission_paid)
            
            return {
                "referrals_made": total_referrals_made,
                "active_referrals": active_referrals,
                "completed_referrals": completed_referrals,
                "referrals_received": len(referrals_received),
                "total_commission_earned": total_commission_earned,
                "paid_commission": paid_commission,
                "pending_commission": pending_commission,
                "success_rate": (completed_referrals / total_referrals_made * 100) if total_referrals_made > 0 else 0
            }
            
        except Exception as e:
            error(f"Error getting church referral stats: {str(e)}")
            raise ReferralError(f"Failed to get referral statistics: {str(e)}")


# Global service instance
referral_service = ReferralService()
