"""
Plaid Transaction Service

Handles on-demand transaction fetching from Plaid API.
Transactions are NOT stored in the database to avoid scalability issues.
Instead, we fetch them on-demand when needed for roundup calculations.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.model.m_plaid_items import PlaidItem
# PlaidAccount import removed - using on-demand Plaid API fetching
from app.services.plaid_client import get_transactions, get_accounts
from app.utils.encryption import decrypt_token

class PlaidTransactionService:
    """Service for fetching transactions on-demand from Plaid"""
    
    @staticmethod
    def get_user_transactions(
        user_id: int, 
        db: Session, 
        days_back: int = 30,
        account_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """, m
        Get transactions for a user on-demand from Plaid
        
        Args:
            user_id: User ID
            db: Database session
            days_back: Number of days to look back
            account_ids: Specific account IDs to fetch (optional)
            
        Returns:
            Dict with transactions and metadata
        """
        try:
            # Get user's Plaid items
            plaid_items = db.query(PlaidItem).filter(
                PlaidItem.user_id == user_id,
                PlaidItem.status == "active"
            ).all()
            if not plaid_items:
                return {
                    "success": False,
                    "error": "No active Plaid items found for user",
                    "transactions": [],
                    "total_count": 0
                }
            
            all_transactions = []
            total_count = 0
            
            for item in plaid_items:
                # Skip if specific items requested and this one not included
                if account_ids and item.item_id not in account_ids:
                    continue
                
                try:
                    # Get access token directly from PlaidItem (not encrypted in this model)
                    access_token = item.access_token
                    
                    # Fetch transactions from Plaid
                    transactions_response = get_transactions(
                        access_token=access_token,
                        days_back=days_back,
                        account_ids=None  # PlaidItem doesn't have individual account_ids, fetch all accounts for this item
                    )
                    
                    if transactions_response and hasattr(transactions_response, 'transactions'):
                        transactions = transactions_response.transactions
                        
                        # Add item info to each transaction
                        for transaction in transactions:
                            transaction_dict = transaction.to_dict()
                            transaction_dict['item_id'] = item.item_id
                            transaction_dict['plaid_item_id'] = item.id
                            all_transactions.append(transaction_dict)
                        
                        total_count += len(transactions)
                        logging.info(f"Fetched {len(transactions)} transactions for item {item.item_id}")
                    elif isinstance(transactions_response, dict) and 'transactions' in transactions_response:
                        # Handle dict response format
                        transactions = transactions_response['transactions']
                        
                        # Add item info to each transaction
                        for transaction in transactions:
                            transaction['item_id'] = item.item_id
                            transaction['plaid_item_id'] = item.id
                            all_transactions.append(transaction)
                        
                        total_count += len(transactions)
                        logging.info(f"Fetched {len(transactions)} transactions for item {item.item_id}")
                    
                except Exception as e:
                    logging.error(f"Error fetching transactions for item {item.item_id}: {str(e)}")
                    continue
            
            # Sort transactions by date (newest first)
            all_transactions.sort(key=lambda x: x.get('date', ''), reverse=True)
            
            return {
                "success": True,
                "transactions": all_transactions,
                "total_count": total_count,
                "items_processed": len(plaid_items)
            }
            
        except Exception as e:
            logging.error(f"Error in get_user_transactions: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "transactions": [],
                "total_count": 0
            }
    
    @staticmethod
    def get_transactions_for_roundup(
        user_id: int,
        db: Session,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """
        Get transactions specifically for roundup calculations
        
        Args:
            user_id: User ID
            db: Database session
            days_back: Number of days to look back (default 7 for weekly roundups)
            
        Returns:
            Dict with transactions suitable for roundup processing
        """
        try:
            # Get transactions from Plaid
            result = PlaidTransactionService.get_user_transactions(
                user_id=user_id,
                db=db,
                days_back=days_back
            )
            
            if not result["success"]:
                return result
            
            transactions = result["transactions"]
            
            # Filter transactions suitable for roundups
            roundup_transactions = []
            for transaction in transactions:
                # Only include debit transactions (negative amounts)
                if transaction.get('amount', 0) < 0:
                    # Exclude certain categories that shouldn't be rounded up
                    category = transaction.get('category', [])
                    if category:
                        excluded_categories = [
                            'Transfer', 'Payment', 'Deposit', 'ATM', 
                            'Bank Fees', 'Interest', 'Credit'
                        ]
                        if not any(excluded in str(cat) for cat in category for excluded in excluded_categories):
                            roundup_transactions.append(transaction)
            
            return {
                "success": True,
                "transactions": roundup_transactions,
                "total_count": len(roundup_transactions),
                "original_count": len(transactions),
                "filtered_count": len(transactions) - len(roundup_transactions)
            }
            
        except Exception as e:
            logging.error(f"Error in get_transactions_for_roundup: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "transactions": [],
                "total_count": 0
            }
    
    @staticmethod
    def calculate_roundup_amount(
        user_id: int,
        db: Session,
        days_back: int = 7,
        multiplier: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculate roundup amount for a user based on recent transactions
        
        Args:
            user_id: User ID
            db: Database session
            days_back: Number of days to look back
            multiplier: Roundup multiplier (1.0 = normal, 2.0 = double, etc.)
            
        Returns:
            Dict with roundup calculation results
        """
        try:
            # Get transactions for roundup
            result = PlaidTransactionService.get_transactions_for_roundup(
                user_id=user_id,
                db=db,
                days_back=days_back
            )
            
            if not result["success"]:
                return result
            
            transactions = result["transactions"]
            
            if not transactions:
                return {
                    "success": True,
                    "roundup_amount": 0.0,
                    "base_amount": 0.0,
                    "transaction_count": 0,
                    "multiplier": multiplier,
                    "message": "No transactions found for roundup"
                }
            
            # Calculate roundup amounts
            total_roundup = 0.0
            base_amount = 0.0
            
            for transaction in transactions:
                amount = abs(transaction.get('amount', 0))
                if amount > 0:
                    # Calculate roundup (round up to next dollar)
                    roundup = (1.0 - (amount % 1.0)) if amount % 1.0 != 0 else 0.0
                    base_amount += roundup
                    total_roundup += roundup * multiplier
            
            return {
                "success": True,
                "roundup_amount": round(total_roundup, 2),
                "base_amount": round(base_amount, 2),
                "transaction_count": len(transactions),
                "multiplier": multiplier,
                "transactions_processed": len(transactions),
                "period_days": days_back
            }
            
        except Exception as e:
            logging.error(f"Error in calculate_roundup_amount: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "roundup_amount": 0.0,
                "base_amount": 0.0,
                "transaction_count": 0
            }
    
    @staticmethod
    def get_account_balances(
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get current account balances from Plaid
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            Dict with account balances
        """
        try:
            # Get user's Plaid items (which contain access tokens)
            plaid_items = db.query(PlaidItem).filter(
                PlaidItem.user_id == user_id,
                PlaidItem.status == "active"
            ).all()
            
            if not plaid_items:
                return {
                    "success": False,
                    "error": "No active Plaid items found for user",
                    "accounts": []
                }
            
            account_balances = []
            
            for item in plaid_items:
                try:
                    # Get access token from PlaidItem
                    access_token = item.access_token
                    
                    # Get account balances from Plaid
                    accounts_response = get_accounts(access_token)
                    
                    # Handle different response formats
                    if accounts_response:
                        if hasattr(accounts_response, 'accounts'):
                            accounts = accounts_response.accounts
                        elif isinstance(accounts_response, dict) and 'accounts' in accounts_response:
                            accounts = accounts_response['accounts']
                        else:
                            accounts = []
                        
                        for plaid_account in accounts:
                            account_balances.append({
                                "account_id": plaid_account.account_id if hasattr(plaid_account, 'account_id') else plaid_account.get('account_id'),
                                "name": plaid_account.name if hasattr(plaid_account, 'name') else plaid_account.get('name'),
                                "mask": plaid_account.mask if hasattr(plaid_account, 'mask') else plaid_account.get('mask'),
                                "type": plaid_account.type if hasattr(plaid_account, 'type') else plaid_account.get('type'),
                                "subtype": plaid_account.subtype if hasattr(plaid_account, 'subtype') else plaid_account.get('subtype'),
                                "current_balance": plaid_account.balances.current if hasattr(plaid_account, 'balances') and hasattr(plaid_account.balances, 'current') else plaid_account.get('balances', {}).get('current'),
                                "available_balance": plaid_account.balances.available if hasattr(plaid_account, 'balances') and hasattr(plaid_account.balances, 'available') else plaid_account.get('balances', {}).get('available'),
                                "limit": plaid_account.balances.limit if hasattr(plaid_account, 'balances') and hasattr(plaid_account.balances, 'limit') else plaid_account.get('balances', {}).get('limit'),
                                "currency_code": plaid_account.balances.iso_currency_code if hasattr(plaid_account, 'balances') and hasattr(plaid_account.balances, 'iso_currency_code') else plaid_account.get('balances', {}).get('iso_currency_code', 'USD')
                            })
                
                except Exception as e:
                    logging.error(f"Error fetching balance for item {item.item_id}: {str(e)}")
                    continue
            
            return {
                "success": True,
                "accounts": account_balances,
                "total_accounts": len(account_balances)
            }
            
        except Exception as e:
            logging.error(f"Error in get_account_balances: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "accounts": []
            }


# Global service instance
plaid_transaction_service = PlaidTransactionService()
