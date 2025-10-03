"""
Plaid Webhook Service

Handles real-time updates from Plaid webhooks.
Simplified version without transaction processing to avoid scalability issues.
"""

import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.model.m_plaid_items import PlaidItem
# PlaidAccount import removed - using on-demand Plaid API fetching
from app.utils.database import SessionLocal


class PlaidWebhookService:
    """Service for handling Plaid webhook events"""
    
    def __init__(self):
        self.supported_webhook_types = [
            "ITEM",
            "ACCOUNTS"
        ]
    
    def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming Plaid webhook"""
        try:
            webhook_type = webhook_data.get("webhook_type")
            webhook_code = webhook_data.get("webhook_code")
            
            
            
            if webhook_type == "ITEM":
                return self._handle_item_webhook(webhook_data)
            elif webhook_type == "ACCOUNTS":
                return self._handle_accounts_webhook(webhook_data)
            else:
                
                return {"status": "ignored", "reason": "unsupported_webhook_type"}
                
        except Exception as e:
            
            return {"status": "error", "error": str(e)}
    
    def _handle_item_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle item webhook events"""
        try:
            webhook_code = webhook_data.get("webhook_code")
            item_id = webhook_data.get("item_id")
            
            
            
            if webhook_code == "ERROR":
                return self._handle_item_error(webhook_data)
            elif webhook_code == "PENDING_EXPIRATION":
                return self._handle_item_expiration(webhook_data)
            elif webhook_code == "USER_PERMISSION_REVOKED":
                return self._handle_user_permission_revoked(webhook_data)
            else:
                return {"status": "ignored", "reason": "unhandled_item_webhook"}
                
        except Exception as e:
            
            return {"status": "error", "error": str(e)}
    
    def _handle_accounts_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle accounts webhook events"""
        try:
            webhook_code = webhook_data.get("webhook_code")
            item_id = webhook_data.get("item_id")
            
            
            
            # Handle account updates (e.g., account status changes)
            return {"status": "success", "webhook_code": webhook_code}
            
        except Exception as e:
            
            return {"status": "error", "error": str(e)}
    
    def _handle_item_error(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle item error webhook"""
        try:
            error = webhook_data.get("error", {})
            error_code = error.get("error_code")
            error_message = error.get("error_message")
            
            
            
            # Handle item error (e.g., mark account as inactive)
            item_id = webhook_data.get("item_id")
            if item_id:
                db = SessionLocal()
                try:
                    plaid_item = db.query(PlaidItem).filter_by(item_id=item_id).first()
                    if plaid_item:
                        plaid_item.status = "error"
                        db.commit()
                        
                finally:
                    db.close()
            
            return {"status": "success", "error_handled": True}
            
        except Exception as e:
            
            return {"status": "error", "error": str(e)}
    
    def _handle_item_expiration(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle item expiration webhook"""
        try:
            item_id = webhook_data.get("item_id")
            
            
            # Handle item expiration (e.g., notify user to re-authenticate)
            db = SessionLocal()
            try:
                plaid_item = db.query(PlaidItem).filter_by(item_id=item_id).first()
                if plaid_item:
                    plaid_item.status = "expiring"
                    db.commit()
                    
            finally:
                db.close()
            
            return {"status": "success", "expiration_notified": True}
            
        except Exception as e:
            
            return {"status": "error", "error": str(e)}
    
    def _handle_user_permission_revoked(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user permission revoked webhook"""
        try:
            item_id = webhook_data.get("item_id")
            
            
            # Handle permission revocation (e.g., mark account as inactive)
            db = SessionLocal()
            try:
                plaid_item = db.query(PlaidItem).filter_by(item_id=item_id).first()
                if plaid_item:
                    plaid_item.status = "revoked"
                    db.commit()
                    
            finally:
                db.close()
            
            return {"status": "success", "permission_revoked_handled": True}
            
        except Exception as e:
            
            return {"status": "error", "error": str(e)}


# Global webhook service instance
plaid_webhook_service = PlaidWebhookService()
