"""
Plaid Webhook Controller

Handles Plaid webhook events for:
- Transaction updates
- Account status changes
- Item login repairs
- Error notifications

Updated to use the new /transactions/sync endpoint and improved webhook handling.
"""

import logging
from sqlalchemy.orm import Session
from app.core.responses import ResponseFactory
from app.model.m_plaid_items import PlaidItem
# PlaidAccount import removed - using on-demand Plaid API fetching
from app.utils.encryption import decrypt_token
from app.services.plaid_client import get_transactions, get_transactions_sync
from app.controller.shared.plaid_webhook_handler import handle_plaid_webhook as handle_webhook


def handle_plaid_webhook(payload: dict, db: Session):
    """
    Handle Plaid webhook events using the new webhook handler
    
    This function now delegates to the improved webhook handler that supports
    the new /transactions/sync endpoint and SYNC_UPDATES_AVAILABLE webhook.
    """
    try:
        # Use the new webhook handler
        return handle_webhook(payload)
        
    except Exception as e:
        logging.error(f"Webhook processing failed: {str(e)}")
        raise Exception(f"Webhook processing failed: {str(e)}")


def handle_transactions_updated(payload: dict, db: Session):
    """Handle transactions updated webhook"""
    try:
        item_id = payload.get("item_id")
        new_transactions = payload.get("new_transactions", 0)

        # Find Plaid items associated with this item_id
        plaid_items = (
            db.query(PlaidItem).filter(PlaidItem.item_id == item_id).all()
        )

        if not plaid_items:

            return ResponseFactory.success(
                message="No Plaid items found for item",
                data={"new_transactions": new_transactions},
            )

        # Process new transactions for each item
        for plaid_item in plaid_items:
            try:
                access_token = decrypt_token(plaid_item.access_token)
                # Fetch new transactions from Plaid
                transactions = get_transactions(
                    access_token,
                    days_back=7,  # Get transactions from last 7 days for webhook
                )

            except Exception as e:

                continue

        return ResponseFactory.success(
            message="Transactions updated successfully",
            data={
                "item_id": item_id,
                "new_transactions": new_transactions,
                "accounts_processed": len(plaid_items),
            },
        )

    except Exception as e:

        raise Exception(f"Failed to handle transactions updated: {str(e)}")


def handle_transactions_removed(payload: dict, db: Session):
    """Handle transactions removed webhook"""
    try:
        item_id = payload.get("item_id")
        removed_transactions = payload.get("removed_transactions", [])

        return ResponseFactory.success(
            message="Transactions removed successfully",
            data={"item_id": item_id, "removed_count": len(removed_transactions)},
        )

    except Exception as e:

        raise Exception(f"Failed to handle transactions removed: {str(e)}")


def handle_item_login_repaired(payload: dict, db: Session):
    """Handle item login repaired webhook"""
    try:
        item_id = payload.get("item_id")

        return ResponseFactory.success(
            message="Item login repaired successfully", data={"item_id": item_id}
        )

    except Exception as e:

        raise Exception(f"Failed to handle item login repaired: {str(e)}")


def handle_item_error(payload: dict, db: Session):
    """Handle item error webhook"""
    try:
        item_id = payload.get("item_id")
        error = payload.get("error", {})

        return ResponseFactory.success(
            message="Item error processed", data={"item_id": item_id, "error": error}
        )

    except Exception as e:

        raise Exception(f"Failed to handle item error: {str(e)}")


def handle_item_removed(payload: dict, db: Session):
    """Handle item removed webhook"""
    try:
        item_id = payload.get("item_id")

        # Mark associated Plaid items as inactive
        plaid_items = (
            db.query(PlaidItem).filter(PlaidItem.item_id == item_id).all()
        )

        for plaid_item in plaid_items:
            plaid_item.status = "inactive"
            plaid_item.updated_at = None

        db.commit()

        return ResponseFactory.success(
            message="Item removed successfully",
            data={"item_id": item_id, "items_deactivated": len(plaid_items)},
        )

    except Exception as e:

        raise Exception(f"Failed to handle item removed: {str(e)}")


def handle_transactions_initial_update(payload: dict, db: Session):
    """Handle initial transaction update webhook"""
    try:
        item_id = payload.get("item_id")

        # Trigger roundup processing for new transactions
        from app.tasks.process_roundups import process_user_roundups

        # Find user by item_id and process roundups
        plaid_item = db.query(PlaidItem).filter(PlaidItem.item_id == item_id).first()
        if plaid_item:
            process_user_roundups(plaid_item.user_id, db)

        return ResponseFactory.success(
            message="Initial transactions update processed", data={"item_id": item_id}
        )

    except Exception as e:

        raise Exception(f"Failed to handle initial transactions update: {str(e)}")


def handle_transactions_historical_update(payload: dict, db: Session):
    """Handle historical transaction update webhook"""
    try:
        item_id = payload.get("item_id")

        return ResponseFactory.success(
            message="Historical transactions update processed",
            data={"item_id": item_id},
        )

    except Exception as e:

        raise Exception(f"Failed to handle historical transactions update: {str(e)}")


def handle_transactions_default_update(payload: dict, db: Session):
    """Handle default transaction update webhook"""
    try:
        item_id = payload.get("item_id")

        # Trigger roundup processing for new transactions
        from app.tasks.process_roundups import process_user_roundups

        # Find user by item_id and process roundups
        plaid_item = db.query(PlaidItem).filter(PlaidItem.item_id == item_id).first()
        if plaid_item:
            process_user_roundups(plaid_item.user_id, db)

        return ResponseFactory.success(
            message="Default transactions update processed", data={"item_id": item_id}
        )

    except Exception as e:

        raise Exception(f"Failed to handle default transactions update: {str(e)}")


def handle_item_pending_expiration(payload: dict, db: Session):
    """Handle item pending expiration webhook"""
    try:
        item_id = payload.get("item_id")

        return ResponseFactory.success(
            message="Item pending expiration processed", data={"item_id": item_id}
        )

    except Exception as e:

        raise Exception(f"Failed to handle item pending expiration: {str(e)}")


def handle_user_permission_revoked(payload: dict, db: Session):
    """Handle user permission revoked webhook"""
    try:
        item_id = payload.get("item_id")

        return ResponseFactory.success(
            message="User permission revoked processed", data={"item_id": item_id}
        )

    except Exception as e:

        raise Exception(f"Failed to handle user permission revoked: {str(e)}")
