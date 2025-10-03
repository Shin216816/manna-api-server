"""
Collection Scheduler Service

Handles automated collection of pending roundups based on user preferences.
Integrates with payment processing to collect and distribute funds.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from app.model.m_user import User
from app.model.m_donation_preference import DonationPreference
from app.model.m_roundup_new import DonorPayout, ChurchPayout
from app.model.m_pending_roundup import PendingRoundup
from app.model.m_church import Church
from app.services.transaction_processor import TransactionProcessor
from app.services.payment_service import PaymentService
from app.core.exceptions import ValidationError, PaymentError
from app.utils.error_handler import handle_service_errors

logger = logging.getLogger(__name__)

class CollectionScheduler:
    """Service for scheduling and executing roundup collections"""
    
    def __init__(self, db: Session):
        self.db = db
        self.transaction_processor = TransactionProcessor(db)
        self.payment_service = PaymentService()
    
    @handle_service_errors
    def process_scheduled_collections(self) -> Dict:
        """
        Process all users who are due for collection based on their preferences
        
        Returns:
            Collection processing results
        """
        try:
            # Get users due for collection
            users_due = self._get_users_due_for_collection()
            
            if not users_due:
                return {
                    'success': True,
                    'message': 'No users due for collection',
                    'processed_count': 0,
                    'total_collected': 0.0
                }
            
            total_processed = 0
            total_collected = 0.0
            results = []
            
            for user in users_due:
                try:
                    result = self._collect_user_roundups(user)
                    if result['success']:
                        total_processed += 1
                        total_collected += result['amount']
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error collecting roundups for user {user.id}: {str(e)}")
                    results.append({
                        'user_id': user.id,
                        'success': False,
                        'error': str(e)
                    })
                    continue
            
            return {
                'success': True,
                'message': f'Processed {total_processed} users',
                'processed_count': total_processed,
                'total_collected': total_collected,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error processing scheduled collections: {str(e)}")
            raise
    
    @handle_service_errors
    def collect_user_roundups(self, user_id: int) -> Dict:
        """
        Manually collect roundups for a specific user
        
        Args:
            user_id: User ID
        
        Returns:
            Collection results
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValidationError("User not found")
        
        return self._collect_user_roundups(user)
    
    @handle_service_errors
    def schedule_user_collection(self, user_id: int) -> Dict:
        """
        Schedule a user for collection based on their preferences
        
        Args:
            user_id: User ID
        
        Returns:
            Scheduling results
        """
        try:
            # Get user's preferences
            preferences = self.db.query(DonationPreference).filter(
                DonationPreference.user_id == user_id
            ).first()
            
            if not preferences:
                return {
                    'success': False,
                    'message': 'No donation preferences found'
                }
            
            # Check if user has pending roundups
            pending_total = self.transaction_processor.get_pending_roundup_summary(user_id)
            
            if pending_total['total_amount'] < float(preferences.minimum_roundup):
                return {
                    'success': False,
                    'message': f'Pending roundup amount (${pending_total["total_amount"]:.2f}) below minimum threshold (${preferences.minimum_roundup})'
                }
            
            # Check if user is due for collection
            if not self._is_user_due_for_collection(user_id, preferences):
                return {
                    'success': False,
                    'message': 'User not due for collection yet'
                }
            
            # Collect roundups
            return self._collect_user_roundups(self.db.query(User).filter(User.id == user_id).first())
            
        except Exception as e:
            logger.error(f"Error scheduling collection for user {user_id}: {str(e)}")
            raise
    
    def _get_users_due_for_collection(self) -> List[User]:
        """Get all users who are due for collection based on their preferences"""
        # Get all active users with donation preferences
        users = self.db.query(User).join(DonationPreference).filter(
            User.is_active == True,
            DonationPreference.pause == False,
            DonationPreference.roundups_enabled == True
        ).all()
        
        users_due = []
        
        for user in users:
            preferences = self.db.query(DonationPreference).filter(
                DonationPreference.user_id == user.id
            ).first()
            
            if self._is_user_due_for_collection(user.id, preferences):
                users_due.append(user)
        
        return users_due
    
    def _is_user_due_for_collection(self, user_id: int, preferences: DonationPreference) -> bool:
        """Check if a user is due for collection based on their preferences"""
        if not preferences or preferences.pause or not preferences.roundups_enabled:
            return False
        
        # Get last collection date
        last_collection = self.db.query(DonorPayout).filter(
            DonorPayout.user_id == user_id,
            DonorPayout.status == 'completed'
        ).order_by(DonorPayout.created_at.desc()).first()
        
        if not last_collection:
            # First collection - check if user has enough pending roundups
            pending_total = self.transaction_processor.get_pending_roundup_summary(user_id)
            return pending_total['total_amount'] >= float(preferences.minimum_roundup)
        
        # Check collection frequency
        now = datetime.now(timezone.utc)
        days_since_last = (now - last_collection.created_at).days
        
        if preferences.frequency == 'biweekly':
            return days_since_last >= 14
        elif preferences.frequency == 'monthly':
            return days_since_last >= 30
        
        return False
    
    def _collect_user_roundups(self, user: User) -> Dict:
        """Collect roundups for a specific user"""
        try:
            # Get pending roundup summary
            pending_summary = self.transaction_processor.get_pending_roundup_summary(user.id)
            
            if pending_summary['total_amount'] <= 0:
                return {
                    'user_id': user.id,
                    'success': False,
                    'message': 'No pending roundups to collect',
                    'amount': 0.0
                }
            
            # Create donor payout record
            donor_payout = DonorPayout(
                user_id=user.id,
                church_id=user.church_id,
                donation_amount=pending_summary['total_amount'],
                status='pending',
                collection_type='roundup',
                created_at=datetime.now(timezone.utc)
            )
            
            self.db.add(donor_payout)
            self.db.flush()
            
            # Process payment through Stripe
            payment_result = self.payment_service.process_donor_payment(
                user_id=user.id,
                amount=pending_summary['total_amount'],
                church_id=user.church_id,
                payout_id=donor_payout.id
            )
            
            if payment_result['success']:
                # Mark payout as completed
                donor_payout.status = 'completed'
                donor_payout.processed_at = datetime.now(timezone.utc)
                
                # Update pending roundups status
                self._mark_roundups_collected(user.id, donor_payout.id)
                
                # Create church payout record
                self._create_church_payout(donor_payout)
                
                self.db.commit()
                
                logger.info(f"Successfully collected ${pending_summary['total_amount']:.2f} for user {user.id}")
                
                return {
                    'user_id': user.id,
                    'success': True,
                    'message': 'Roundups collected successfully',
                    'amount': pending_summary['total_amount'],
                    'payout_id': donor_payout.id
                }
            else:
                # Mark payout as failed
                donor_payout.status = 'failed'
                self.db.commit()
                
                return {
                    'user_id': user.id,
                    'success': False,
                    'message': f"Payment failed: {payment_result.get('error', 'Unknown error')}",
                    'amount': 0.0
                }
                
        except Exception as e:
            logger.error(f"Error collecting roundups for user {user.id}: {str(e)}")
            self.db.rollback()
            raise
    
    def _mark_roundups_collected(self, user_id: int, payout_id: int):
        """Mark all pending roundups as collected"""
        pending_roundups = self.db.query(PendingRoundup).filter(
            PendingRoundup.user_id == user_id,
            PendingRoundup.status == 'pending'
        ).all()
        
        for roundup in pending_roundups:
            roundup.status = 'collected'
            roundup.payout_id = payout_id
            roundup.collected_at = datetime.now(timezone.utc)
    
    def _create_church_payout(self, donor_payout: DonorPayout):
        """Create church payout record for the collected donation"""
        # Check if church payout already exists for this period
        existing_payout = self.db.query(ChurchPayout).filter(
            ChurchPayout.church_id == donor_payout.church_id,
            ChurchPayout.status == 'pending'
        ).first()
        
        if existing_payout:
            # Add to existing payout
            existing_payout.total_amount += donor_payout.donation_amount
            existing_payout.donor_count += 1
        else:
            # Create new church payout
            church_payout = ChurchPayout(
                church_id=donor_payout.church_id,
                total_amount=donor_payout.donation_amount,
                donor_count=1,
                status='pending',
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(church_payout)
    
    @handle_service_errors
    def get_collection_schedule(self) -> Dict:
        """Get collection schedule for all users"""
        users_due = self._get_users_due_for_collection()
        
        schedule = []
        for user in users_due:
            preferences = self.db.query(DonationPreference).filter(
                DonationPreference.user_id == user.id
            ).first()
            
            pending_summary = self.transaction_processor.get_pending_roundup_summary(user.id)
            
            schedule.append({
                'user_id': user.id,
                'email': user.email,
                'frequency': preferences.frequency if preferences else 'unknown',
                'pending_amount': pending_summary['total_amount'],
                'pending_count': pending_summary['count']
            })
        
        return {
            'total_users_due': len(users_due),
            'schedule': schedule
        }
