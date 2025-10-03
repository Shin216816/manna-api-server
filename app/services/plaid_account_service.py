"""
Plaid Account Service

Handles fetching account data from Plaid API on-demand.
Replaces the need for storing account data in the database.
"""

import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.model.m_plaid_items import PlaidItem
from app.services.plaid_client import get_accounts
from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

class PlaidAccountService:
    """Service for fetching account data from Plaid API"""
    
    @staticmethod
    def get_user_accounts(user_id: int, db: Session) -> Dict[str, Any]:
        """
        Get all accounts for a user from Plaid API
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            Dict with accounts and metadata
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
                    "accounts": [],
                    "total_accounts": 0
                }
            
            all_accounts = []
            total_accounts = 0
            
            for item in plaid_items:
                try:
                    # Get accounts from Plaid API
                    accounts_response = get_accounts(item.access_token)
                    
                    if accounts_response and 'accounts' in accounts_response:
                        accounts = accounts_response['accounts']
                        
                        # Add item and institution info to each account
                        for account in accounts:
                            account['plaid_item_id'] = item.id
                            account['item_id'] = item.item_id
                            account['institution_id'] = accounts_response.get('institution', {}).get('institution_id')
                            account['institution_name'] = accounts_response.get('institution', {}).get('name', 'Unknown Bank')
                            account['linked_at'] = item.created_at.isoformat() if item.created_at else None
                            all_accounts.append(account)
                        
                        total_accounts += len(accounts)
                        logger.info(f"Fetched {len(accounts)} accounts for item {item.item_id}")
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch accounts for item {item.item_id}: {str(e)}")
                    continue
            
            return {
                "success": True,
                "accounts": all_accounts,
                "total_accounts": total_accounts
            }
            
        except Exception as e:
            logger.error(f"Error fetching user accounts: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to fetch accounts: {str(e)}",
                "accounts": [],
                "total_accounts": 0
            }
    
    @staticmethod
    def get_account_by_id(user_id: int, account_id: str, db: Session) -> Dict[str, Any]:
        """
        Get a specific account by ID from Plaid API
        
        Args:
            user_id: User ID
            account_id: Account ID to find
            db: Database session
            
        Returns:
            Dict with account data or error
        """
        try:
            # Get all user accounts
            result = PlaidAccountService.get_user_accounts(user_id, db)
            
            if not result["success"]:
                return result
            
            # Find the specific account
            for account in result["accounts"]:
                if account["account_id"] == account_id:
                    return {
                        "success": True,
                        "account": account
                    }
            
            return {
                "success": False,
                "error": "Account not found",
                "account": None
            }
            
        except Exception as e:
            logger.error(f"Error fetching account {account_id}: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to fetch account: {str(e)}",
                "account": None
            }
    
    @staticmethod
    def get_accounts_count(user_id: int, db: Session) -> int:
        """
        Get the count of linked accounts for a user
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            Number of linked accounts
        """
        try:
            result = PlaidAccountService.get_user_accounts(user_id, db)
            return result.get("total_accounts", 0) if result["success"] else 0
        except Exception as e:
            logger.error(f"Error counting accounts for user {user_id}: {str(e)}")
            return 0

# Create service instance
plaid_account_service = PlaidAccountService()
