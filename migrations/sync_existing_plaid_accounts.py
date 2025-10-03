#!/usr/bin/env python3
"""
Migration script to sync existing Plaid accounts to the plaid_accounts table.

This script will:
1. Find all active Plaid items
2. Fetch account data from Plaid for each item
3. Create PlaidAccount records for any missing accounts
4. Update existing accounts with fresh data

Run this script after deploying the updated bank controller.
"""

import sys
import os
import logging
from datetime import datetime, timezone

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.utils.database import get_db
from app.model.m_user import User
from app.model.m_plaid_items import PlaidItem
from app.model.m_plaid_account import PlaidAccount
from app.services.plaid_client import get_accounts

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_existing_plaid_accounts():
    """Sync all existing Plaid accounts to the plaid_accounts table."""
    
    db = next(get_db())
    
    try:
        # Get all active Plaid items
        active_plaid_items = (
            db.query(PlaidItem)
            .filter(PlaidItem.status == "active")
            .all()
        )
        
        logger.info(f"Found {len(active_plaid_items)} active Plaid items")
        
        total_accounts_synced = 0
        
        for plaid_item in active_plaid_items:
            try:
                logger.info(f"Processing Plaid item {plaid_item.id} for user {plaid_item.user_id}")
                
                # Get fresh account data from Plaid
                accounts_data = get_accounts(plaid_item.access_token)
                
                # Update institution info
                if "item" in accounts_data and "institution_id" in accounts_data["item"]:
                    plaid_item.institution_id = str(accounts_data["item"]["institution_id"])
                if "institution" in accounts_data and "name" in accounts_data["institution"]:
                    plaid_item.institution_name = str(accounts_data["institution"]["name"])

                # Process each account
                for account in accounts_data.get("accounts", []):
                    account_type = str(account["type"])
                    account_subtype = str(account["subtype"])

                    if account_type == "depository" and account_subtype in ["checking", "savings"]:
                        # Check if account already exists
                        existing_account = (
                            db.query(PlaidAccount)
                            .filter(
                                PlaidAccount.user_id == plaid_item.user_id,
                                PlaidAccount.account_id == str(account["account_id"])
                            )
                            .first()
                        )

                        if existing_account:
                            # Update existing account
                            existing_account.name = str(account["name"])
                            existing_account.official_name = str(account.get("official_name", ""))
                            existing_account.type = str(account["type"])
                            existing_account.subtype = str(account["subtype"])
                            existing_account.mask = str(account["mask"])
                            existing_account.available_balance = account.get("balances", {}).get("available")
                            existing_account.current_balance = account.get("balances", {}).get("current")
                            existing_account.iso_currency_code = account.get("balances", {}).get("iso_currency_code", "USD")
                            existing_account.status = "active"
                            existing_account.updated_at = datetime.now(timezone.utc)
                            
                            logger.info(f"Updated existing account {account['account_id']}")
                        else:
                            # Create new account
                            plaid_account = PlaidAccount(
                                user_id=plaid_item.user_id,
                                plaid_item_id=plaid_item.id,
                                account_id=str(account["account_id"]),
                                name=str(account["name"]),
                                official_name=str(account.get("official_name", "")),
                                type=str(account["type"]),
                                subtype=str(account["subtype"]),
                                mask=str(account["mask"]),
                                available_balance=account.get("balances", {}).get("available"),
                                current_balance=account.get("balances", {}).get("current"),
                                iso_currency_code=account.get("balances", {}).get("iso_currency_code", "USD"),
                                status="active"
                            )
                            db.add(plaid_account)
                            
                            logger.info(f"Created new account {account['account_id']}")
                        
                        total_accounts_synced += 1

            except Exception as e:
                logger.error(f"Error processing Plaid item {plaid_item.id}: {str(e)}")
                continue

        # Commit all changes
        db.commit()
        
        logger.info(f"Successfully synced {total_accounts_synced} accounts")
        
    except Exception as e:
        logger.error(f"Error during sync: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    sync_existing_plaid_accounts()
