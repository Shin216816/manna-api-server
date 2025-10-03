"""
Transaction Processing Service

Handles fetching and processing bank transactions from Plaid.
Integrates with the roundup engine to create pending roundups.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.model.m_user import User
from app.model.m_plaid_items import PlaidItem
# PlaidTransaction import removed - using on-demand Plaid API fetching
# PlaidService import removed - using PlaidTransactionService for on-demand fetching
from app.services.roundup_engine import RoundupEngine
from app.core.exceptions import ValidationError, ExternalServiceError
from app.utils.error_handler import handle_service_errors

logger = logging.getLogger(__name__)

class TransactionProcessor:
    """Service for processing bank transactions and creating roundups"""
    
    def __init__(self, db: Session):
        self.db = db
        # PlaidService removed - using PlaidTransactionService for on-demand fetching
        self.roundup_engine = RoundupEngine(db)
    
    @handle_service_errors
    def process_user_transactions(self, user_id: int, days_back: int = 30) -> Dict:
        """
        Process all transactions for a user and create pending roundups
        
        Args:
            user_id: User ID
            days_back: Number of days back to fetch transactions
        
        Returns:
            Processing results summary
        """
        try:
            # Get user's Plaid items
            plaid_items = self.db.query(PlaidItem).filter(
                PlaidItem.user_id == user_id,
                PlaidItem.status == 'active'
            ).all()
            
            if not plaid_items:
                return {
                    'success': False,
                    'message': 'No active bank accounts found',
                    'processed_count': 0,
                    'total_roundup': 0.0
                }
            
            total_processed = 0
            total_roundup = 0.0
            all_roundups = []
            
            # Process transactions for each account
            for plaid_item in plaid_items:
                try:
                    result = self._process_account_transactions(
                        user_id, 
                        plaid_item, 
                        days_back
                    )
                    
                    total_processed += result['processed_count']
                    total_roundup += result['total_roundup']
                    all_roundups.extend(result['created_roundups'])
                    
                except Exception as e:
                    logger.error(f"Error processing account {plaid_item.account_id}: {str(e)}")
                    continue
            
            return {
                'success': True,
                'message': f'Processed {total_processed} transactions',
                'processed_count': total_processed,
                'total_roundup': total_roundup,
                'created_roundups': all_roundups
            }
            
        except Exception as e:
            logger.error(f"Error processing transactions for user {user_id}: {str(e)}")
            raise
    
    @handle_service_errors
    def process_account_transactions(self, user_id: int, account_id: str, days_back: int = 30) -> Dict:
        """
        Process transactions for a specific account
        
        Args:
            user_id: User ID
            account_id: Plaid account ID
            days_back: Number of days back to fetch transactions
        
        Returns:
            Processing results
        """
        plaid_item = self.db.query(PlaidItem).filter(
            PlaidItem.user_id == user_id,
            PlaidItem.account_id == account_id,
            PlaidItem.status == 'active'
        ).first()
        
        if not plaid_item:
            raise ValidationError("Account not found or inactive")
        
        return self._process_account_transactions(user_id, plaid_item, days_back)
    
    @handle_service_errors
    def sync_recent_transactions(self, user_id: int) -> Dict:
        """
        Sync recent transactions (last 7 days) for a user
        
        Args:
            user_id: User ID
        
        Returns:
            Sync results
        """
        return self.process_user_transactions(user_id, days_back=7)
    
    @handle_service_errors
    def get_user_transactions_with_roundups(self, user_id: int, limit: int = 50) -> Dict:
        """
        Get user's recent transactions with roundup information
        
        Args:
            user_id: User ID
            limit: Maximum number of transactions to return
        
        Returns:
            Transactions with roundup data
        """
        # Get user's Plaid items
        plaid_items = self.db.query(PlaidItem).filter(
            PlaidItem.user_id == user_id,
            PlaidItem.status == 'active'
        ).all()
        
        if not plaid_items:
            return {
                'transactions': [],
                'total_pending_roundup': 0.0
            }
        
        all_transactions = []
        total_pending_roundup = 0.0
        
        # Fetch transactions from each account
        for plaid_item in plaid_items:
            try:
                # Use PlaidTransactionService for on-demand fetching
                from app.services.plaid_transaction_service import plaid_transaction_service
                result = plaid_transaction_service.get_user_transactions(
                    user_id=user_id,
                    db=self.db,
                    days_back=30
                )
                transactions = result.get("transactions", []) if result.get("success") else []
                
                # Add roundup information to each transaction
                for transaction in transactions:
                    transaction['account_name'] = plaid_item.account_name
                    transaction['account_type'] = plaid_item.account_type
                    
                    # Check if this transaction has a pending roundup
                    pending_roundup = self._get_pending_roundup_for_transaction(
                        user_id, 
                        transaction['transaction_id']
                    )
                    
                    if pending_roundup:
                        transaction['roundup_amount'] = float(pending_roundup.roundup_amount)
                        transaction['roundup_status'] = 'pending'
                        total_pending_roundup += float(pending_roundup.roundup_amount)
                    else:
                        transaction['roundup_amount'] = 0.0
                        transaction['roundup_status'] = 'none'
                    
                    all_transactions.append(transaction)
                    
            except Exception as e:
                logger.error(f"Error fetching transactions for account {plaid_item.account_id}: {str(e)}")
                continue
        
        # Sort by date (most recent first) and limit
        all_transactions.sort(key=lambda x: x.get('date', ''), reverse=True)
        all_transactions = all_transactions[:limit]
        
        return {
            'transactions': all_transactions,
            'total_pending_roundup': total_pending_roundup
        }
    
    def _process_account_transactions(self, user_id: int, plaid_item: PlaidItem, days_back: int) -> Dict:
        """Process transactions for a specific Plaid item"""
        try:
            # Fetch transactions from Plaid using PlaidTransactionService
            from app.services.plaid_transaction_service import plaid_transaction_service
            result = plaid_transaction_service.get_user_transactions(
                user_id=plaid_item.user_id,
                db=self.db,
                days_back=days_back
            )
            transactions = result.get("transactions", []) if result.get("success") else []
            
            # Process transactions through roundup engine
            result = self.roundup_engine.process_user_transactions(user_id, transactions)
            
            # Transaction storage removed - using on-demand Plaid API fetching
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing account {plaid_item.account_id}: {str(e)}")
            raise
    
    # _store_transactions method removed - using on-demand Plaid API fetching instead of database storage
    
    def _get_pending_roundup_for_transaction(self, user_id: int, transaction_id: str) -> Optional:
        """Get pending roundup for a specific transaction"""
        from app.model.m_pending_roundup import PendingRoundup
        
        return self.db.query(PendingRoundup).filter(
            PendingRoundup.user_id == user_id,
            PendingRoundup.transaction_id == transaction_id,
            PendingRoundup.status == 'pending'
        ).first()
    
    @handle_service_errors
    def collect_pending_roundups(self, user_id: int) -> Dict:
        """
        Collect all pending roundups for a user
        
        Args:
            user_id: User ID
        
        Returns:
            Collection results
        """
        return self.roundup_engine.collect_pending_roundups(user_id)
    
    @handle_service_errors
    def get_pending_roundup_summary(self, user_id: int) -> Dict:
        """
        Get summary of pending roundups for a user
        
        Args:
            user_id: User ID
        
        Returns:
            Pending roundup summary
        """
        pending_roundups = self.roundup_engine.get_pending_roundups(user_id)
        total_amount = self.roundup_engine.get_pending_roundup_total(user_id)
        
        return {
            'count': len(pending_roundups),
            'total_amount': total_amount,
            'roundups': [
                {
                    'id': roundup.id,
                    'amount': float(roundup.roundup_amount),
                    'merchant': roundup.merchant_name,
                    'date': roundup.transaction_date.isoformat(),
                    'original_amount': float(roundup.original_amount)
                }
                for roundup in pending_roundups
            ]
        }
