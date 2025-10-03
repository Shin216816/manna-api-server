"""
Donor Schedule Service

Handles individual donor payout scheduling based on:
1. Donor's signup date
2. Donor's donation preferences (frequency, multiplier)
3. Calculates next donation dates for each donor
4. Processes individual donor payouts when their time comes
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import logging

from app.model.m_user import User
from app.model.m_donation_preference import DonationPreference
from app.model.m_roundup_new import DonorPayout
from app.model.m_donation_batch import DonationBatch
from app.services.stripe_service import create_payment_intent


class DonorScheduleService:
    """Service for managing individual donor payout schedules"""
    
    @staticmethod
    def calculate_next_donation_date(user: User, preference: DonationPreference, db: Session) -> datetime:
        """
        Calculate the next donation date for a donor based on their signup date and preferences
        
        Args:
            user: User object
            preference: DonationPreference object
            db: Database session
            
        Returns:
            datetime: Next donation date
        """
        # Get the last successful donation for this user
        last_donation = db.query(DonorPayout).filter(
            and_(
                DonorPayout.user_id == user.id,
                DonorPayout.status == "completed"
            )
        ).order_by(DonorPayout.processed_at.desc()).first()
        
        if last_donation:
            # Calculate next donation based on frequency from last donation
            base_date = last_donation.processed_at
        else:
            # First donation - calculate from signup date
            base_date = user.created_at
        
        # Calculate next donation date based on frequency
        if preference.frequency == "biweekly":
            # Every 2 weeks (14 days)
            next_date = base_date + timedelta(days=14)
        elif preference.frequency == "monthly":
            # Every month (30 days)
            next_date = base_date + timedelta(days=30)
        else:
            # Default to biweekly
            next_date = base_date + timedelta(days=14)
        
        return next_date
    
    @staticmethod
    def get_donors_due_for_donation(db: Session, target_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get all donors who are due for donation on a specific date
        
        Args:
            db: Database session
            target_date: Date to check (defaults to today)
            
        Returns:
            List of donor information with donation details
        """
        if target_date is None:
            target_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get all active donors with preferences
        donors_with_preferences = db.query(
            User.id,
            User.first_name,
            User.last_name,
            User.email,
            User.created_at,
            User.stripe_customer_id,
            DonationPreference.frequency,
            DonationPreference.multiplier,
            DonationPreference.target_church_id,
            DonationPreference.minimum_roundup,
            DonationPreference.monthly_cap
        ).join(
            DonationPreference, User.id == DonationPreference.user_id
        ).filter(
            and_(
                User.is_active == True,
                User.role == "donor",
                DonationPreference.pause == False,
                DonationPreference.roundups_enabled == True,
                User.stripe_customer_id.isnot(None)
            )
        ).all()
        
        due_donors = []
        
        for donor_data in donors_with_preferences:
            user_id, first_name, last_name, email, created_at, stripe_customer_id, frequency, multiplier, target_church_id, minimum_roundup, monthly_cap = donor_data
            
            # Create temporary objects for calculation
            user = User()
            user.id = user_id
            user.created_at = created_at
            
            preference = DonationPreference()
            preference.frequency = frequency
            preference.multiplier = multiplier
            preference.target_church_id = target_church_id
            preference.minimum_roundup = minimum_roundup
            preference.monthly_cap = monthly_cap
            
            # Calculate next donation date
            next_donation_date = DonorScheduleService.calculate_next_donation_date(user, preference, db)
            
            # Check if this donor is due today
            if next_donation_date.date() == target_date.date():
                # Calculate estimated donation amount
                estimated_amount = DonorScheduleService.calculate_estimated_donation_amount(user, preference, db)
                
                due_donors.append({
                    "user_id": user_id,
                    "name": f"{first_name} {last_name}",
                    "email": email,
                    "frequency": frequency,
                    "multiplier": multiplier,
                    "target_church_id": target_church_id,
                    "estimated_amount": estimated_amount,
                    "minimum_roundup": float(minimum_roundup) if minimum_roundup else 1.0,
                    "monthly_cap": float(monthly_cap) if monthly_cap else None,
                    "next_donation_date": next_donation_date.isoformat(),
                    "stripe_customer_id": stripe_customer_id
                })
        
        return due_donors
    
    @staticmethod
    def calculate_estimated_donation_amount(user: User, preference: DonationPreference, db: Session) -> float:
        """
        Calculate estimated donation amount for a donor based on their history
        
        Args:
            user: User object
            preference: DonationPreference object
            db: Database session
            
        Returns:
            float: Estimated donation amount
        """
        # Get last 3 successful donations to calculate average
        recent_donations = db.query(DonorPayout.donation_amount).filter(
            and_(
                DonorPayout.user_id == user.id,
                DonorPayout.status == "completed"
            )
        ).order_by(DonorPayout.processed_at.desc()).limit(3).all()
        
        if recent_donations:
            # Calculate average from recent donations
            total_amount = sum(float(donation.donation_amount) for donation in recent_donations)
            average_amount = total_amount / len(recent_donations)
        else:
            # No history - use minimum roundup
            average_amount = float(preference.minimum_roundup) if preference.minimum_roundup else 1.0
        
        # Apply monthly cap if set
        if preference.monthly_cap and average_amount > float(preference.monthly_cap):
            average_amount = float(preference.monthly_cap)
        
        return round(average_amount, 2)
    
    @staticmethod
    def process_donor_payout(user_id: int, db: Session) -> Dict[str, Any]:
        """
        Process payout for a specific donor
        
        Args:
            user_id: User ID to process
            db: Database session
            
        Returns:
            Dict with processing result
        """
        try:
            # Get user and preference
            user = db.query(User).filter_by(id=user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            preference = db.query(DonationPreference).filter_by(user_id=user_id).first()
            if not preference:
                return {"success": False, "error": "Donation preference not found"}
            
            # Calculate donation amount
            donation_amount = DonorScheduleService.calculate_estimated_donation_amount(user, preference, db)
            
            # Skip if amount is too small
            if donation_amount < 1.0:
                return {"success": False, "error": "Donation amount too small"}
            
            # Create payment intent
            payment_intent_data = create_payment_intent(
                amount=int(donation_amount * 100),  # Convert to cents
                currency="usd",
                customer_id=user.stripe_customer_id,
                metadata={
                    "user_id": str(user_id),
                    "church_id": str(preference.target_church_id) if preference.target_church_id else "default",
                    "type": "scheduled_donation",
                    "frequency": preference.frequency,
                    "multiplier": preference.multiplier
                }
            )
            
            # Create DonorPayout record
            donor_payout = DonorPayout(
                user_id=user_id,
                church_id=preference.target_church_id or user.church_id,
                donation_amount=donation_amount,
                roundup_multiplier=float(preference.multiplier.replace('x', '')),
                base_roundup_amount=donation_amount / float(preference.multiplier.replace('x', '')),
                plaid_transaction_count=1,  # Placeholder
                collection_period=f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
                donation_type="scheduled",
                status="completed",
                processed_at=datetime.now(timezone.utc)
            )
            
            db.add(donor_payout)
            db.commit()
            
            return {
                "success": True,
                "donor_payout_id": donor_payout.id,
                "amount": donation_amount,
                "payment_intent_id": payment_intent_data.get("id"),
                "user_name": user.full_name
            }
            
        except Exception as e:
            logging.error(f"Error processing donor payout for user {user_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_daily_donation_summary(db: Session, target_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get daily donation summary including upcoming donors and estimated amounts
        
        Args:
            db: Database session
            target_date: Date to analyze (defaults to today)
            
        Returns:
            Dict with daily summary
        """
        if target_date is None:
            target_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get donors due today
        due_donors = DonorScheduleService.get_donors_due_for_donation(db, target_date)
        
        # Calculate totals
        total_donors = len(due_donors)
        total_estimated_amount = sum(donor["estimated_amount"] for donor in due_donors)
        
        # Group by church
        church_totals = {}
        for donor in due_donors:
            church_id = donor["target_church_id"]
            if church_id not in church_totals:
                church_totals[church_id] = {"count": 0, "amount": 0.0}
            church_totals[church_id]["count"] += 1
            church_totals[church_id]["amount"] += donor["estimated_amount"]
        
        return {
            "date": target_date.strftime("%Y-%m-%d"),
            "total_donors": total_donors,
            "total_estimated_amount": round(total_estimated_amount, 2),
            "church_breakdown": church_totals,
            "donors": due_donors
        }
    
    @staticmethod
    def get_upcoming_donors(db: Session, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Get list of donors who will donate in the next N days
        
        Args:
            db: Database session
            days_ahead: Number of days to look ahead
            
        Returns:
            List of upcoming donors with their donation dates
        """
        upcoming_donors = []
        
        for day_offset in range(days_ahead):
            target_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=day_offset)
            due_donors = DonorScheduleService.get_donors_due_for_donation(db, target_date)
            
            for donor in due_donors:
                upcoming_donors.append({
                    **donor,
                    "donation_date": target_date.strftime("%Y-%m-%d"),
                    "days_from_now": day_offset
                })
        
        # Sort by donation date
        upcoming_donors.sort(key=lambda x: x["donation_date"])
        
        return upcoming_donors
