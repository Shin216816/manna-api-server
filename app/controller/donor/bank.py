import logging
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from sqlalchemy import func

from app.model.m_user import User
from app.model.m_plaid_items import PlaidItem
from app.services.plaid_client import (
    create_link_token as plaid_create_link_token,
    exchange_public_token as plaid_exchange_public_token,
    get_accounts,
)

from app.core.responses import ResponseFactory
from app.core.exceptions import UserNotFoundError, ValidationError
from app.utils.error_handler import handle_controller_errors
from fastapi import HTTPException
from plaid.model.country_code import CountryCode
from plaid.model.products import Products


@handle_controller_errors
def create_link_token(data, current_user: dict, db: Session):
    """Create Plaid link token for donor bank account linking"""

    # Handle different current_user structures
    user_id = None
    if hasattr(current_user, "id") and not isinstance(current_user, dict):
        # current_user is a User model instance
        user_id = current_user.id
    elif isinstance(current_user, dict):
        # current_user is a dictionary
        if "id" in current_user:
            user_id = current_user["user_id"]
        elif "user_id" in current_user:
            user_id = current_user["user_id"]

    if not user_id:
        raise UserNotFoundError(
            details={"message": "User ID not found in authentication data"}
        )

    user = User.get_by_id(db, user_id)
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        link_token_data = plaid_create_link_token(
            user_id=str(user.id),
            client_name="Manna",
            country_codes=[CountryCode("US")],
            language="en",
            products=[Products("transactions")],
        )

        return ResponseFactory.success(
            message="Link token created successfully", data=link_token_data
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create link token")


@handle_controller_errors
def exchange_public_token(data, current_user: dict, db: Session):
    """Exchange public token for access token and link bank account"""

    # Handle different current_user structures
    user_id = None
    if hasattr(current_user, "id") and not isinstance(current_user, dict):
        # current_user is a User model instance
        user_id = current_user.id
    elif isinstance(current_user, dict):
        # current_user is a dictionary
        if "id" in current_user:
            user_id = current_user["user_id"]
        elif "user_id" in current_user:
            user_id = current_user["user_id"]

    if not user_id:
        raise UserNotFoundError(
            details={"message": "User ID not found in authentication data"}
        )

    user = User.get_by_id(db, user_id)
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        public_token = data.public_token
        if not public_token:
            raise ValidationError("Public token is required")

        exchange_result = plaid_exchange_public_token(public_token)
        access_token = exchange_result["access_token"]
        item_id = exchange_result["item_id"]

        # Check if user already has an active Plaid item
        existing_plaid_item = (
            db.query(PlaidItem)
            .filter(PlaidItem.user_id == user.id, PlaidItem.status == "active")
            .first()
        )

        if existing_plaid_item:
            # Deactivate existing Plaid item
            existing_plaid_item.status = "inactive"

        # Create new Plaid item
        plaid_item = PlaidItem(
            user_id=user.id, item_id=item_id, access_token=access_token, status="active"
        )
        db.add(plaid_item)
        
        # Flush to get the plaid_item.id before creating accounts
        db.flush()

        # Get the linked accounts to return
        accounts_data = get_accounts(access_token)
        
        # Log the accounts data for debugging
        logging.info(f"Plaid accounts data: {accounts_data}")

        # Extract institution information safely
        institution_info = "Unknown Bank"
        if "institution" in accounts_data and "name" in accounts_data["institution"]:
            institution_info = str(accounts_data["institution"]["name"])
        elif "item" in accounts_data and "institution_id" in accounts_data["item"]:
            institution_info = str(accounts_data["item"]["institution_id"])

        # Update the plaid item with institution info
        plaid_item.institution_id = institution_info
        if "institution" in accounts_data and "name" in accounts_data["institution"]:
            plaid_item.institution_name = str(accounts_data["institution"]["name"])

        linked_accounts = []

        # Log all accounts for debugging
        logging.info(f"All accounts from Plaid: {accounts_data.get('accounts', [])}")

        # Filter for depository accounts (checking/savings) and prepare response
        for account in accounts_data["accounts"]:
            # Convert enum values to strings for comparison
            account_type = str(account["type"])
            account_subtype = str(account["subtype"])

            logging.info(f"Account type: {account_type}, subtype: {account_subtype}")

            # Include all depository accounts (checking, savings, etc.)
            if account_type == "depository":
                # Add to response with proper formatting
                linked_accounts.append(
                    {
                        "id": str(account["account_id"]),
                        "account_id": str(account["account_id"]),
                        "name": str(account["name"]),
                        "type": str(account["type"]),
                        "subtype": str(account["subtype"]),
                        "institution": institution_info,
                        "mask": str(account["mask"]),
                        "available_balance": account.get("balances", {}).get("available"),
                        "current_balance": account.get("balances", {}).get("current"),
                        "iso_currency_code": account.get("balances", {}).get("iso_currency_code", "USD"),
                        "status": "active",
                        "payment_method_type": "plaid_account"
                    }
                )

        # Commit the plaid item
        db.commit()

        # Log the final response
        logging.info(f"Returning {len(linked_accounts)} linked accounts: {linked_accounts}")

        return ResponseFactory.success(
            message="Public token exchanged successfully",
            data={
                "accounts": linked_accounts,
                "accounts_linked": len(linked_accounts),
                "item_id": item_id,
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to exchange public token")


@handle_controller_errors
def get_linked_accounts(current_user: dict, db: Session):
    """Get donor's linked bank accounts from both Plaid and Stripe"""

    # Handle different current_user structures
    user_id = None
    if hasattr(current_user, "id") and not isinstance(current_user, dict):
        # current_user is a User model instance
        user_id = current_user.id
    elif isinstance(current_user, dict):
        # current_user is a dictionary
        if "id" in current_user:
            user_id = current_user["user_id"]
        elif "user_id" in current_user:
            user_id = current_user["user_id"]

    if not user_id:
        raise UserNotFoundError(
            details={"message": "User ID not found in authentication data"}
        )

    user = User.get_by_id(db, user_id)
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    # Get Plaid accounts from API
    from app.services.plaid_account_service import plaid_account_service
    accounts_result = plaid_account_service.get_user_accounts(user_id, db)
    
    accounts = []
    
    # Add Plaid accounts
    if accounts_result["success"]:
        for plaid_account in accounts_result["accounts"]:
            accounts.append({
                "id": str(plaid_account["account_id"]),
                "account_id": str(plaid_account["account_id"]),
                "name": str(plaid_account["name"]),
                "type": str(plaid_account["type"]),
                "subtype": str(plaid_account["subtype"]),
                "institution": plaid_account.get("institution_name", "Plaid Bank"),
                "mask": str(plaid_account["mask"]),
                "available_balance": plaid_account.get("available_balance"),
                "current_balance": plaid_account.get("current_balance"),
                "currency": str(plaid_account.get("iso_currency_code", "USD")),
                "created_at": plaid_account.get("linked_at"),
                "status": str(plaid_account.get("status", "active")),
                "payment_method_type": "plaid_account"
            })

    # If no Plaid accounts and user has Stripe customer ID, get Stripe accounts
    if not accounts and user.stripe_customer_id:
        try:
            from app.services.stripe_service import list_customer_payment_methods
            from datetime import datetime
            
            # Get all payment methods from Stripe (both cards and bank accounts)
            all_payment_methods = []
            
            # Get bank accounts
            try:
                bank_accounts = list_customer_payment_methods(
                    customer_id=user.stripe_customer_id,
                    type="us_bank_account",
                    limit=100
                )
                all_payment_methods.extend(bank_accounts)
            except Exception as e:
                logging.warning(f"Error fetching bank accounts: {str(e)}")

            # Get cards
            try:
                cards = list_customer_payment_methods(
                    customer_id=user.stripe_customer_id,
                    type="card",
                    limit=100
                )
                all_payment_methods.extend(cards)
            except Exception as e:
                logging.warning(f"Error fetching cards: {str(e)}")

            for pm in all_payment_methods:
                pm_type = pm.get("type")
                
                if pm_type == "us_bank_account":
                    # Bank account
                    bank_account = pm.get("us_bank_account", {})
                    account_info = {
                        "id": pm.get("id"),
                        "account_id": pm.get("id"),
                        "name": f"{bank_account.get('bank_name', 'Bank Account')} - {bank_account.get('account_holder_type', 'account').title()}",
                        "type": "depository",
                        "subtype": bank_account.get("account_type", "checking"),
                        "institution": bank_account.get("bank_name", "Unknown Bank"),
                        "mask": bank_account.get("last4", "****"),
                        "stripe_payment_method_id": pm.get("id"),
                        "created_at": datetime.fromtimestamp(pm.get("created", 0)).isoformat() if pm.get("created") else None,
                        "status": "verified" if pm.get("status") != "errored" else "inactive",
                        "payment_method_type": "bank_account"
                    }
                elif pm_type == "card":
                    # Card
                    card = pm.get("card", {})
                    account_info = {
                        "id": pm.get("id"),
                        "account_id": pm.get("id"),
                        "name": f"{card.get('brand', 'Card').title()} •••• {card.get('last4', '****')}",
                        "type": "card",
                        "subtype": card.get("funding", "credit"),
                        "institution": f"{card.get('brand', 'Card').title()}",
                        "mask": card.get("last4", "****"),
                        "stripe_payment_method_id": pm.get("id"),
                        "created_at": datetime.fromtimestamp(pm.get("created", 0)).isoformat() if pm.get("created") else None,
                        "status": "verified" if pm.get("status") != "errored" else "inactive",
                        "payment_method_type": "card"
                    }
                else:
                    continue  # Skip other payment method types
                
                accounts.append(account_info)
        except Exception as e:
            logging.warning(f"Error fetching Stripe accounts: {str(e)}")

    return ResponseFactory.success(
        message="Linked accounts retrieved successfully",
        data={"accounts": accounts, "total_accounts": len(accounts)},
    )


@handle_controller_errors
def get_transactions(data, current_user: dict, db: Session):
    """Get donor's bank transactions"""

    # Handle different current_user structures
    user_id = None
    if hasattr(current_user, "id") and not isinstance(current_user, dict):
        # current_user is a User model instance
        user_id = current_user.id
    elif isinstance(current_user, dict):
        # current_user is a dictionary
        if "id" in current_user:
            user_id = current_user["user_id"]
        elif "user_id" in current_user:
            user_id = current_user["user_id"]

    if not user_id:
        raise UserNotFoundError(
            details={"message": "User ID not found in authentication data"}
        )

    user = User.get_by_id(db, user_id)
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        from app.services.plaid_client import get_transactions

        plaid_item = (
            db.query(PlaidItem)
            .filter(PlaidItem.user_id == user.id, PlaidItem.status == "active")
            .first()
        )

        if not plaid_item:
            raise ValidationError("No active Plaid connection found")

        transactions_data = get_transactions(
            access_token=plaid_item.access_token,
            days_back=30,  # Get transactions from last 30 days
        )

        return ResponseFactory.success(
            message="Transactions retrieved successfully",
            data={
                "transactions": transactions_data.get("transactions", []),
                "total_transactions": len(transactions_data.get("transactions", [])),
                "accounts": transactions_data.get("accounts", []),
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get transactions")


@handle_controller_errors
def unlink_account(account_id: str, current_user: dict, db: Session):
    """Unlink donor's bank account"""

    # Handle different current_user structures
    user_id = None
    if hasattr(current_user, "id") and not isinstance(current_user, dict):
        # current_user is a User model instance
        user_id = current_user.id
    elif isinstance(current_user, dict):
        # current_user is a dictionary
        if "id" in current_user:
            user_id = current_user["user_id"]
        elif "user_id" in current_user:
            user_id = current_user["user_id"]

    if not user_id:
        raise UserNotFoundError(
            details={"message": "User ID not found in authentication data"}
        )

    user = User.get_by_id(db, user_id)
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    # Detach the payment method from Stripe
    try:
        from app.services.stripe_service import detach_payment_method
        detach_payment_method(account_id)
    except Exception as e:
        logging.error(f"Error detaching payment method from Stripe: {str(e)}")
        raise ValidationError("Failed to unlink account")

    return ResponseFactory.success(
        message="Bank account unlinked successfully",
        data={
            "account_id": account_id,
            "unlinked_at": datetime.now(timezone.utc).isoformat(),
        },
    )


@handle_controller_errors
def sync_accounts(data, current_user: dict, db: Session):
    """Sync donor's payment methods from Stripe (no local storage needed)"""

    # Handle different current_user structures
    user_id = None
    if hasattr(current_user, "id") and not isinstance(current_user, dict):
        # current_user is a User model instance
        user_id = current_user.id
    elif isinstance(current_user, dict):
        # current_user is a dictionary
        if "id" in current_user:
            user_id = current_user["user_id"]
        elif "user_id" in current_user:
            user_id = current_user["user_id"]

    if not user_id:
        raise UserNotFoundError(
            details={"message": "User ID not found in authentication data"}
        )

    user = User.get_by_id(db, user_id)
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    # Check if user has a Stripe customer ID
    if not user.stripe_customer_id:
        return ResponseFactory.success(
            message="No Stripe customer found",
            data={
                "synced_at": datetime.now(timezone.utc).isoformat(),
                "accounts_synced": 0,
            },
        )

    try:
        from app.services.stripe_service import list_customer_payment_methods
        from datetime import datetime, timezone
        
        # Get all payment methods from Stripe
        all_payment_methods = []
        
        # Get bank accounts
        try:
            bank_accounts = list_customer_payment_methods(
                customer_id=user.stripe_customer_id,
                type="us_bank_account",
                limit=100
            )
            all_payment_methods.extend(bank_accounts)
        except Exception as e:
            logging.warning(f"Error fetching bank accounts: {str(e)}")

        # Get cards
        try:
            cards = list_customer_payment_methods(
                customer_id=user.stripe_customer_id,
                type="card",
                limit=100
            )
            all_payment_methods.extend(cards)
        except Exception as e:
            logging.warning(f"Error fetching cards: {str(e)}")

        return ResponseFactory.success(
            message="Payment methods synced successfully",
            data={
                "synced_at": datetime.now(timezone.utc).isoformat(),
                "accounts_synced": len(all_payment_methods),
                "message": "Payment methods are managed directly by Stripe"
            },
        )

    except Exception as e:
        logging.error(f"Error syncing accounts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to sync accounts")


@handle_controller_errors
def get_account_balance(account_id: str, current_user: dict, db: Session):
    """Get donor's account balance"""

    # Handle different current_user structures
    user_id = None
    if hasattr(current_user, "id") and not isinstance(current_user, dict):
        # current_user is a User model instance
        user_id = current_user.id
    elif isinstance(current_user, dict):
        # current_user is a dictionary
        if "id" in current_user:
            user_id = current_user["user_id"]
        elif "user_id" in current_user:
            user_id = current_user["user_id"]

    if not user_id:
        raise UserNotFoundError(
            details={"message": "User ID not found in authentication data"}
        )

    user = User.get_by_id(db, user_id)
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    # Find the plaid item that contains this account
    plaid_items = (
        db.query(PlaidItem)
        .filter(PlaidItem.user_id == user.id, PlaidItem.status == "active")
        .all()
    )

    account_found = False
    for plaid_item in plaid_items:
        try:
            accounts_data = get_accounts(plaid_item.access_token)
            for account in accounts_data["accounts"]:
                # Convert enum values to strings for comparison
                account_type = str(account["type"])
                account_subtype = str(account["subtype"])

                if account["account_id"] == account_id:
                    account_found = True
                    break
            if account_found:
                break
        except Exception as e:
            continue

    if not account_found:
        raise ValidationError("Bank account not found")

    try:
        # Placeholder for balance data
        # In a real implementation, this would fetch from Plaid
        return ResponseFactory.success(
            message="Account balance retrieved successfully",
            data={
                "account_id": account_id,
                "balance": {
                    "available": 0.0,
                    "current": 0.0,
                    "limit": None,
                    "iso_currency_code": "USD",
                    "unofficial_currency_code": None,
                },
                "last_updated": datetime.now(timezone.utc).isoformat(),
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get account balance")


@handle_controller_errors
def cleanup_duplicate_plaid_items(current_user: dict, db: Session):
    """Clean up duplicate Plaid items for the current user (admin function)"""

    # Handle different current_user structures
    user_id = None
    if hasattr(current_user, "id") and not isinstance(current_user, dict):
        # current_user is a User model instance
        user_id = current_user.id
    elif isinstance(current_user, dict):
        # current_user is a dictionary
        if "id" in current_user:
            user_id = current_user["user_id"]
        elif "user_id" in current_user:
            user_id = current_user["user_id"]

    if not user_id:
        raise UserNotFoundError(
            details={"message": "User ID not found in authentication data"}
        )

    user = User.get_by_id(db, user_id)
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        # Get all Plaid items for the user
        all_plaid_items = (
            db.query(PlaidItem)
            .filter(PlaidItem.user_id == user.id)
            .order_by(PlaidItem.created_at.desc())
            .all()
        )

        if len(all_plaid_items) <= 1:
            return ResponseFactory.success(
                message="No duplicate Plaid items found",
                data={"plaid_items_count": len(all_plaid_items)},
            )

        # Keep only the most recent active Plaid item, deactivate others
        latest_plaid_item = all_plaid_items[0]
        items_to_deactivate = all_plaid_items[1:]

        # Deactivate older Plaid items
        for item in items_to_deactivate:
            item.status = "inactive"

        db.commit()

        return ResponseFactory.success(
            message="Duplicate Plaid items cleaned up successfully",
            data={
                "kept_plaid_item_id": latest_plaid_item.id,
                "deactivated_count": len(items_to_deactivate),
                "remaining_active_count": 1,
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to cleanup duplicate Plaid items"
        )
