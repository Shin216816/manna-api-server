"""
Plaid Webhook Handler

Handles webhooks from Plaid for transaction updates and other events.
This follows the recommended Plaid webhook patterns for the new /transactions/sync endpoint.
"""

import logging
from typing import Dict, Any
from fastapi import HTTPException
from app.core.responses import ResponseFactory
from app.utils.error_handler import handle_controller_errors

@handle_controller_errors
def handle_plaid_webhook(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle Plaid webhook events
    
    Args:
        webhook_data: Webhook payload from Plaid
        
    Returns:
        Response indicating success or failure
    """
    try:
        webhook_type = webhook_data.get('webhook_type')
        webhook_code = webhook_data.get('webhook_code')
        
        logging.info(f"Received Plaid webhook: {webhook_type} - {webhook_code}")
        
        if webhook_type == 'TRANSACTIONS':
            return handle_transactions_webhook(webhook_data)
        elif webhook_type == 'ITEM':
            return handle_item_webhook(webhook_data)
        else:
            logging.warning(f"Unhandled webhook type: {webhook_type}")
            return ResponseFactory.success(
                message="Webhook received but not processed",
                data={"webhook_type": webhook_type, "webhook_code": webhook_code}
            )
            
    except Exception as e:
        logging.error(f"Error handling Plaid webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

def handle_transactions_webhook(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle transaction-related webhooks
    
    Args:
        webhook_data: Transaction webhook payload
        
    Returns:
        Response indicating success or failure
    """
    webhook_code = webhook_data.get('webhook_code')
    item_id = webhook_data.get('item_id')
    
    if webhook_code == 'SYNC_UPDATES_AVAILABLE':
        # New transaction updates are available
        # This is the recommended webhook for /transactions/sync
        logging.info(f"Transaction updates available for item {item_id}")
        
        return ResponseFactory.success(
            message="Transaction updates available",
            data={
                "item_id": item_id,
                "webhook_code": webhook_code,
                "action_required": "Call /transactions/sync to fetch updates"
            }
        )
        
    elif webhook_code == 'DEFAULT_UPDATE':
        # Legacy webhook for /transactions/get (still supported)
        new_transactions = webhook_data.get('new_transactions', 0)
        logging.info(f"New transactions available for item {item_id}: {new_transactions}")
        
        return ResponseFactory.success(
            message="New transactions available",
            data={
                "item_id": item_id,
                "webhook_code": webhook_code,
                "new_transactions": new_transactions,
                "action_required": "Call /transactions/sync to fetch updates"
            }
        )
        
    elif webhook_code == 'TRANSACTIONS_REMOVED':
        # Transactions have been removed
        removed_transactions = webhook_data.get('removed_transactions', [])
        logging.info(f"Transactions removed for item {item_id}: {len(removed_transactions)}")
        
        return ResponseFactory.success(
            message="Transactions removed",
            data={
                "item_id": item_id,
                "webhook_code": webhook_code,
                "removed_count": len(removed_transactions),
                "removed_transactions": removed_transactions
            }
        )
        
    elif webhook_code == 'INITIAL_UPDATE':
        # Initial transactions are ready
        logging.info(f"Initial transactions ready for item {item_id}")
        
        return ResponseFactory.success(
            message="Initial transactions ready",
            data={
                "item_id": item_id,
                "webhook_code": webhook_code,
                "action_required": "Call /transactions/sync to fetch initial data"
            }
        )
        
    elif webhook_code == 'HISTORICAL_UPDATE':
        # Historical transactions are ready
        logging.info(f"Historical transactions ready for item {item_id}")
        
        return ResponseFactory.success(
            message="Historical transactions ready",
            data={
                "item_id": item_id,
                "webhook_code": webhook_code,
                "action_required": "Call /transactions/sync to fetch historical data"
            }
        )
        
    else:
        logging.warning(f"Unhandled transaction webhook code: {webhook_code}")
        return ResponseFactory.success(
            message="Transaction webhook received",
            data={
                "item_id": item_id,
                "webhook_code": webhook_code,
                "status": "unhandled"
            }
        )

def handle_item_webhook(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle item-related webhooks
    
    Args:
        webhook_data: Item webhook payload
        
    Returns:
        Response indicating success or failure
    """
    webhook_code = webhook_data.get('webhook_code')
    item_id = webhook_data.get('item_id')
    
    if webhook_code == 'ERROR':
        # Item error occurred
        error = webhook_data.get('error', {})
        logging.error(f"Item error for {item_id}: {error}")
        
        return ResponseFactory.success(
            message="Item error webhook received",
            data={
                "item_id": item_id,
                "webhook_code": webhook_code,
                "error": error,
                "action_required": "Check item status and re-authenticate if needed"
            }
        )
        
    elif webhook_code == 'NEW_ACCOUNTS_AVAILABLE':
        # New accounts available
        logging.info(f"New accounts available for item {item_id}")
        
        return ResponseFactory.success(
            message="New accounts available",
            data={
                "item_id": item_id,
                "webhook_code": webhook_code,
                "action_required": "Call /accounts/get to fetch new accounts"
            }
        )
        
    else:
        logging.warning(f"Unhandled item webhook code: {webhook_code}")
        return ResponseFactory.success(
            message="Item webhook received",
            data={
                "item_id": item_id,
                "webhook_code": webhook_code,
                "status": "unhandled"
            }
        )
