"""
Round-up Calculation Engine

Core service for calculating round-ups from bank transactions.
Handles transaction processing, round-up calculation, and pending balance management.
"""

import logging
import math
from decimal import Decimal, ROUND_UP
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from app.model.m_user import User
from app.model.m_donation_preference import DonationPreference
from app.model.m_plaid_items import PlaidItem
# PlaidTransaction import removed - using on-demand Plaid API fetching
from app.model.m_roundup_new import DonorPayout, ChurchPayout
from app.model.m_pending_roundup import PendingRoundup
from app.model.m_church import Church
from app.core.exceptions import ValidationError
from app.utils.error_handler import handle_service_errors

logger = logging.getLogger(__name__)

class RoundupEngine:
    """Core round-up calculation engine"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @handle_service_errors
    def calculate_roundup(self, transaction_amount: float, multiplier: str = "1x") -> float:
        """
        Calculate round-up amount for a transaction
        
        Args:
            transaction_amount: Original transaction amount
            multiplier: Round-up multiplier (1x, 2x, 3x, 5x)
        
        Returns:
            Round-up amount
        """
        if transaction_amount <= 0:
            return 0.0
        
        # Convert multiplier to float
        multiplier_map = {
            "1x": 1.0,
            "2x": 2.0,
            "3x": 3.0,
            "5x": 5.0
        }
        
        mult = multiplier_map.get(multiplier, 1.0)
        
        # Calculate round-up: ceiling(amount) - amount
        ceiling_amount = Decimal(str(transaction_amount)).quantize(Decimal('1.00'), rounding=ROUND_UP)
        roundup_amount = float(ceiling_amount - Decimal(str(transaction_amount)))
        
        # Apply multiplier
        final_roundup = roundup_amount * mult
        
        # Round to 2 decimal places
        return round(final_roundup, 2)
    
    @handle_service_errors
    def process_transaction_for_roundup(self, user_id: int, transaction: Dict) -> Optional[PendingRoundup]:
        """
        Process a single transaction and create pending roundup if applicable
        
        Args:
            user_id: User ID
            transaction: Transaction data from Plaid
        
        Returns:
            PendingRoundup object if roundup created, None otherwise
        """
        try:
            # Get user's donation preferences
            preferences = self.db.query(DonationPreference).filter(
                DonationPreference.user_id == user_id
            ).first()
            
            if not preferences or preferences.pause or not preferences.roundups_enabled:
                return None
            
            # Check if transaction is eligible for roundup
            if not self._is_transaction_eligible(transaction, preferences):
                return None
            
            # Calculate roundup amount
            transaction_amount = abs(float(transaction.get('amount', 0)))
            roundup_amount = self.calculate_roundup(transaction_amount, preferences.multiplier)
            
            # Check minimum roundup threshold
            if roundup_amount < float(preferences.minimum_roundup):
                return None
            
            # Check monthly cap if set
            if preferences.monthly_cap:
                monthly_total = self._get_monthly_roundup_total(user_id)
                if monthly_total + roundup_amount > float(preferences.monthly_cap):
                    # Adjust roundup to fit within cap
                    roundup_amount = max(0, float(preferences.monthly_cap) - monthly_total)
                    if roundup_amount < float(preferences.minimum_roundup):
                        return None
            
            # Create pending roundup
            pending_roundup = PendingRoundup(
                user_id=user_id,
                transaction_id=transaction.get('transaction_id'),
                account_id=transaction.get('account_id'),
                original_amount=transaction_amount,
                roundup_amount=roundup_amount,
                merchant_name=transaction.get('merchant_name', 'Unknown'),
                category=transaction.get('category', []),
                transaction_date=datetime.fromisoformat(transaction.get('date', '').replace('Z', '+00:00')),
                status='pending',
                created_at=datetime.now(timezone.utc)
            )
            
            self.db.add(pending_roundup)
            self.db.commit()
            self.db.refresh(pending_roundup)
            
            logger.info(f"Created pending roundup: {roundup_amount} for user {user_id}")
            return pending_roundup
            
        except Exception as e:
            logger.error(f"Error processing transaction for roundup: {str(e)}")
            self.db.rollback()
            raise
    
    @handle_service_errors
    def process_user_transactions(self, user_id: int, transactions: List[Dict]) -> Dict:
        """
        Process multiple transactions for a user and create pending roundups
        
        Args:
            user_id: User ID
            transactions: List of transaction data from Plaid
        
        Returns:
            Summary of processing results
        """
        processed_count = 0
        total_roundup = 0.0
        created_roundups = []
        
        for transaction in transactions:
            try:
                pending_roundup = self.process_transaction_for_roundup(user_id, transaction)
                if pending_roundup:
                    created_roundups.append(pending_roundup)
                    processed_count += 1
                    total_roundup += pending_roundup.roundup_amount
                    
                        
            except Exception as e:
                logger.error(f"Error processing transaction {transaction.get('transaction_id')}: {str(e)}")
                continue
        
        
        return {
            'processed_count': processed_count,
            'total_roundup': total_roundup,
            'created_roundups': created_roundups
        }
    
    @handle_service_errors
    def get_pending_roundups(self, user_id: int) -> List[PendingRoundup]:
        """Get all pending roundups for a user"""
        return self.db.query(PendingRoundup).filter(
            PendingRoundup.user_id == user_id,
            PendingRoundup.status == 'pending'
        ).order_by(PendingRoundup.created_at.desc()).all()
    
    @handle_service_errors
    def get_pending_roundup_total(self, user_id: int) -> float:
        """Get total pending roundup amount for a user"""
        result = self.db.query(func.sum(PendingRoundup.roundup_amount)).filter(
            PendingRoundup.user_id == user_id,
            PendingRoundup.status == 'pending'
        ).scalar()
        return float(result or 0.0)
    
    @handle_service_errors
    def collect_pending_roundups(self, user_id: int) -> Dict:
        """
        Collect all pending roundups for a user and create a payout
        
        Args:
            user_id: User ID
        
        Returns:
            Collection results
        """
        # Get pending roundups
        pending_roundups = self.get_pending_roundups(user_id)
        
        if not pending_roundups:
            return {
                'success': False,
                'message': 'No pending roundups to collect',
                'total_amount': 0.0
            }
        
        # Calculate total amount
        total_amount = sum(roundup.roundup_amount for roundup in pending_roundups)
        
        # Get user's target church
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.church_id:
            raise ValidationError("User must be associated with a church to collect roundups")
        
        # Create donor payout
        donor_payout = DonorPayout(
            user_id=user_id,
            church_id=user.church_id,
            donation_amount=total_amount,
            status='pending',
            collection_type='roundup',
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(donor_payout)
        self.db.flush()
        
        # Update pending roundups status
        for roundup in pending_roundups:
            roundup.status = 'collected'
            roundup.payout_id = donor_payout.id
            roundup.collected_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        logger.info(f"Collected {len(pending_roundups)} roundups totaling ${total_amount} for user {user_id}")
        
        return {
            'success': True,
            'message': f'Successfully collected {len(pending_roundups)} roundups',
            'total_amount': total_amount,
            'payout_id': donor_payout.id
        }
    
    def _is_transaction_eligible(self, transaction: Dict, preferences: DonationPreference) -> bool:
        """Check if transaction is eligible for roundup"""
        # Only process debit transactions (positive amounts in Plaid)
        if float(transaction.get('amount', 0)) <= 0:
            return False
        
        # Check excluded categories
        if preferences.exclude_categories:
            excluded = preferences.exclude_categories.split(',')
            transaction_categories = transaction.get('category', [])
            if any(cat in excluded for cat in transaction_categories):
                return False
        
        # Check minimum transaction amount (optional)
        min_amount = float(preferences.minimum_roundup)
        if abs(float(transaction.get('amount', 0))) < min_amount:
            return False
        
        return True
    
    def _get_monthly_roundup_total(self, user_id: int) -> float:
        """Get total roundup amount for current month"""
        now = datetime.now(timezone.utc)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        result = self.db.query(func.sum(PendingRoundup.roundup_amount)).filter(
            PendingRoundup.user_id == user_id,
            PendingRoundup.status == 'pending',
            PendingRoundup.created_at >= start_of_month
        ).scalar()
        
        return float(result or 0.0)

    # Additional functions from other roundup services for consolidation
    # These maintain API compatibility while consolidating services
    
    @staticmethod
    def calculate_roundups(
        user_id: int,
        start_date: str,
        end_date: str,
        db: Session,
        multiplier: float = 1.0,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate roundups for a user (from roundup_service.py)
        Maintains API compatibility
        """
        try:
            from app.services.plaid_transaction_service import plaid_transaction_service
            
            # Get user preferences
            preferences = db.query(DonationPreference).filter(
                DonationPreference.user_id == user_id
            ).first()
            
            if not preferences:
                return {
                    "success": False,
                    "error": "No donation preferences found",
                    "roundups": []
                }
            
            # Get transactions from Plaid
            result = plaid_transaction_service.get_user_transactions(
                user_id=user_id,
                db=db,
                days_back=days_back
            )
            
            if not result.get("success"):
                return {
                    "success": False,
                    "error": "Failed to fetch transactions",
                    "roundups": []
                }
            
            transactions = result.get("transactions", [])
            roundup_transactions = []
            
            for transaction in transactions:
                if RoundupEngine._is_transaction_eligible_static(transaction, preferences):
                    transaction_amount = abs(float(transaction.get('amount', 0)))
                    roundup_amount = RoundupEngine._calculate_roundup_static(
                        transaction_amount, 
                        f"{multiplier}x"
                    )
                    
                    if roundup_amount > 0:
                        roundup_transactions.append({
                            "transaction_id": transaction.get("transaction_id"),
                            "amount": transaction_amount,
                            "roundup_amount": roundup_amount,
                            "date": transaction.get("date"),
                            "description": transaction.get("name", "Transaction"),
                            "category": transaction.get("category", [])
                        })
            
            return {
                "success": True,
                "roundups": roundup_transactions,
                "total_roundup": sum(r["roundup_amount"] for r in roundup_transactions),
                "transaction_count": len(roundup_transactions)
            }
            
        except Exception as e:
            logger.error(f"Error calculating roundups: {str(e)}")
            return {
                "success": False,
                "error": f"Roundup calculation failed: {str(e)}",
                "roundups": []
            }
    
    @staticmethod
    def _is_transaction_eligible_static(transaction: Dict, preferences: DonationPreference) -> bool:
        """Static version of transaction eligibility check"""
        # Only process debit transactions (positive amounts in Plaid)
        if float(transaction.get('amount', 0)) <= 0:
            return False
        
        # Check excluded categories
        if preferences.exclude_categories:
            excluded = preferences.exclude_categories.split(',')
            transaction_categories = transaction.get('category', [])
            if any(cat in excluded for cat in transaction_categories):
                return False
        
        # Check minimum transaction amount (optional)
        min_amount = float(preferences.minimum_roundup)
        if abs(float(transaction.get('amount', 0))) < min_amount:
            return False
        
        return True
    
    @staticmethod
    def _calculate_roundup_static(amount: float, multiplier_str: str) -> float:
        """Static version of roundup calculation"""
        try:
            multiplier = float(multiplier_str.replace('x', ''))
            roundup = math.ceil(amount) - amount
            return round(roundup * multiplier, 2)
        except (ValueError, TypeError):
            return 0.0
