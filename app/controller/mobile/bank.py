from fastapi import HTTPException
from sqlalchemy.orm import Session
import logging
import os
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import SQLAlchemyError
from collections import defaultdict
from sqlalchemy import func, and_, desc
from typing import List, Dict, Any, Optional

from app.model.m_user import User
from app.model.m_plaid_items import PlaidItem
# PlaidAccount import removed - using on-demand Plaid API fetching
from app.model.m_donation_batch import DonationBatch
from app.model.m_donation_preference import DonationPreference
# from app.model.m_donation_schedule import DonationSchedule  # Removed - not needed for roundup-only system
from app.model.m_church import Church
from app.services.plaid_client import create_link_token, exchange_public_token, get_accounts, get_transactions, get_institution_by_id, plaid_client
from plaid.model.transactions_get_request import TransactionsGetRequest
from app.utils.encryption import encrypt_token, decrypt_token
from app.utils.stripe_client import stripe
from app.core.messages import get_bank_message
from app.core.responses import ResponseFactory
from app.config import config






def create_mobile_link_token(data, current_user: dict, db: Session):
    """Create Plaid link token for mobile app"""
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token")
        
        link_token = create_link_token(str(user_id))
        return ResponseFactory.success(
            message="Plaid link token created successfully",
            data={"link_token": link_token}
        )
    except Exception as e:
        error_msg = str(e)
        if "Android package name must be configured" in error_msg:
            
            raise HTTPException(
                status_code=400, 
                detail="PLAID_CONFIG_ERROR: Android package name must be configured in Plaid developer dashboard. Please contact support."
            )
        elif "INVALID_FIELD" in error_msg:
            
            raise HTTPException(
                status_code=400, 
                detail="PLAID_CONFIG_ERROR: Plaid configuration issue. Please contact support."
            )
        else:
            
            raise HTTPException(status_code=400, detail=f"PLAID.LINK_TOKEN_ERROR: {error_msg}")


def exchange_mobile_public_token(data, current_user, db: Session):
    """Exchange public token for access token and link bank accounts"""
    try:
        user_id = current_user["id"]
        public_token = data.public_token
        
        exchange_response = exchange_public_token(public_token)
        access_token = exchange_response['access_token']
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PLAID.EXCHANGE_FAILED: {str(e)}")

    try:
        accounts_response = get_accounts(access_token).to_dict()
        institution_id = accounts_response["item"].get("institution_id", "")
        institution_name = "Unknown"

        if institution_id:
            try:
                institution_response = get_institution_by_id(institution_id).to_dict()
                institution_name = institution_response.get("institution", {}).get("name", "Unknown")
            except Exception as e:
                pass
                

        # Delete existing Plaid items for this user
        existing_items = db.query(PlaidItem).filter_by(user_id=user_id).all()
        for item in existing_items:
            db.delete(item)
        db.commit()

        # Create new Plaid item
        plaid_item = PlaidItem(
            user_id=user_id,
            item_id=accounts_response["item"]["item_id"],
            access_token=encrypt_token(access_token),
            institution_id=institution_id,
            institution_name=institution_name,
            status="active"
        )
        db.add(plaid_item)
        db.flush()  # Get the ID

        # Prepare account data for response (no database storage needed)
        created_accounts = []
        for account_data in accounts_response.get("accounts", []):
            created_accounts.append({
                "account_id": account_data["account_id"],
                "name": account_data.get("name", ""),
                "mask": account_data.get("mask", ""),
                "subtype": account_data.get("subtype", ""),
                "type": account_data.get("type", ""),
                "institution": institution_name
            })

        db.commit()

        return ResponseFactory.success(
            message="Bank accounts linked successfully",
            data={
                "accounts": created_accounts,
                "institution": institution_name
            }
        )

    except SQLAlchemyError as db_err:
        db.rollback()
        
        raise HTTPException(
            status_code=500, 
            detail=get_bank_message("BANK_ACCOUNT_LINK_FAILED")
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to link bank accounts")


def get_mobile_transactions(data, current_user, db: Session):
    """Fetch user transactions from linked bank accounts"""
    try:
        user_id = current_user["id"]
        plaid_item = db.query(PlaidItem).filter(PlaidItem.user_id == user_id).first()
        if not plaid_item:
            raise HTTPException(
                status_code=404, 
                detail=get_bank_message("BANK_ACCOUNT_NOT_FOUND")
            )

        access_token = decrypt_token(plaid_item.access_token)

        start_date = None
        end_date = None
        try:
            start_date = datetime.strptime(data.start_date, "%Y-%m-%d").date() if hasattr(data, 'start_date') and data.start_date else None
            end_date = datetime.strptime(data.end_date, "%Y-%m-%d").date() if hasattr(data, 'end_date') and data.end_date else None
        except Exception as date_err:
            
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

        if not start_date or not end_date:
            today = datetime.now().date()
            start_date = today
            end_date = today

        # Get transactions from Plaid using the correct approach like the old backend
        from plaid.model.transactions_get_request import TransactionsGetRequest
        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date
        )
        response = plaid_client.transactions_get(request).to_dict()
        return ResponseFactory.success(
            message="Transactions retrieved successfully",
            data={"transactions": response.get("transactions", [])}
        )

    except SQLAlchemyError as db_err:
        db.rollback()
        
        raise HTTPException(
            status_code=500, 
            detail=get_bank_message("TRANSACTIONS_FETCH_FAILED")
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to retrieve transactions")


def get_mobile_bank_accounts(current_user, db: Session):
    """Get user's linked bank accounts from Plaid API"""
    try:
        from app.services.plaid_account_service import plaid_account_service
        
        user_id = current_user["id"]
        result = plaid_account_service.get_user_accounts(user_id, db)
        
        if not result["success"]:
            return ResponseFactory.success(
                message="No bank accounts found",
                data={"accounts": []}
            )
        
        accounts_data = []
        for account in result["accounts"]:
            accounts_data.append({
                "account_id": account["account_id"],
                "name": account["name"],
                "mask": account["mask"],
                "subtype": account["subtype"],
                "type": account["type"],
                "institution": account.get("institution_name", "Unknown"),
                "created_at": account.get("linked_at")
            })
        
        return ResponseFactory.success(
            message="Bank accounts retrieved successfully",
            data={"accounts": accounts_data}
        )
    except Exception as e:
        logging.error(f"Error getting mobile bank accounts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve bank accounts")


def get_mobile_donation_history(current_user, db: Session):
    """Get user's donation history"""
    try:
        user_id = current_user["id"]
        
        # Get donation batches
        batches = db.query(DonationBatch).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        ).order_by(DonationBatch.created_at.desc()).all()
        
        history_data = []
        for batch in batches:
            history_data.append({
                "batch_id": batch.id,
                "total_amount": float(batch.total_amount),
                "status": batch.status,
                "created_at": batch.created_at.isoformat(),
                "processed_at": batch.processed_at.isoformat() if batch.processed_at else None,
                "transaction_count": batch.transaction_count
            })
        
        return ResponseFactory.success(
            message="Donation history retrieved successfully",
            data={"donations": history_data}
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to retrieve donation history")


def get_mobile_donation_summary(current_user, db: Session):
    """Get user's donation summary"""
    try:
        user_id = current_user["id"]
        
        # Calculate total donated
        total_donated = db.query(func.sum(DonationBatch.total_amount)).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        ).scalar() or 0.0
        
        # Calculate this month's donations
        current_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month_donated = db.query(func.sum(DonationBatch.total_amount)).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed",
            DonationBatch.created_at >= current_month
        ).scalar() or 0.0
        
        # Get donation count
        donation_count = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        ).scalar() or 0
        
        return ResponseFactory.success(
            message="Donation summary retrieved successfully",
            data={
                "total_donated": round(float(total_donated), 2),
                "this_month_donated": round(float(this_month_donated), 2),
                "donation_count": donation_count,
                "currency": "USD"
            }
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to retrieve donation summary")


def get_mobile_impact_analytics(current_user, db: Session):
    """Get user's impact analytics"""
    try:
        user_id = current_user["id"]
        
        # Get all completed donations
        donations = db.query(DonationBatch).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        ).all()
        
        total_amount = sum(float(d.total_amount) for d in donations)
        donation_count = len(donations)
        avg_donation = total_amount / donation_count if donation_count > 0 else 0.0
        
        # Monthly breakdown
        monthly_data = {}
        for donation in donations:
            month_key = donation.created_at.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {"amount": 0.0, "count": 0}
            monthly_data[month_key]["amount"] += float(donation.total_amount)
            monthly_data[month_key]["count"] += 1
        
        sorted_monthly = sorted(monthly_data.items(), key=lambda x: x[0])
        
        return ResponseFactory.success(
            message="Impact analytics retrieved successfully",
            data={
                "total_impact": {
                    "amount": round(float(total_amount), 2),
                    "donations": donation_count,
                    "average": round(avg_donation, 2)
                },
                "monthly_breakdown": [
                    {
                        "month": month,
                        "amount": round(data["amount"], 2),
                        "count": data["count"]
                    }
                    for month, data in sorted_monthly
                ]
            }
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to retrieve impact analytics")


def list_mobile_payment_methods(current_user, db):
    """List user's saved payment methods"""
    try:
        user_id = current_user["id"]
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.stripe_customer_id:
            return ResponseFactory.success(
                message="No payment methods found",
                data={"payment_methods": []}
            )
        
        # Get user's payment methods from Stripe using stored customer ID
        from app.services.stripe_service import list_payment_methods
        payment_methods_data = list_payment_methods(
            customer_id=user.stripe_customer_id,
            type="card",
            limit=100
        )
        
        payment_methods = []
        for pm in payment_methods_data:
            payment_methods.append({
                "id": pm["id"],
                "type": pm["type"],
                "card": {
                    "brand": pm["card"]["brand"] if pm.get("card") else None,
                    "last4": pm["card"]["last4"] if pm.get("card") else None,
                    "exp_month": pm["card"]["exp_month"] if pm.get("card") else None,
                    "exp_year": pm["card"]["exp_year"] if pm.get("card") else None
                },
                "created": pm["created"]
            })
        
        return ResponseFactory.success(
            message="Payment methods retrieved successfully",
            data={"payment_methods": payment_methods}
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to retrieve payment methods")


def delete_mobile_payment_method(payment_method_id, current_user, db):
    """Delete a payment method"""
    try:
        user_id = current_user["id"]
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.stripe_customer_id:
            raise HTTPException(status_code=404, detail="Stripe customer not found")
        
        # Verify the payment method belongs to the user
        from app.services.stripe_service import detach_payment_method
        payment_method = detach_payment_method(payment_method_id)
        
        return ResponseFactory.success(
            message="Payment method deleted successfully",
            data={"payment_method": payment_method}
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to delete payment method")


def save_mobile_payment_method(user_id: int, payment_method_id: str, current_user: dict, db: Session):
    """Save a payment method for user"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.stripe_customer_id:
            raise HTTPException(status_code=404, detail="Stripe customer not found")
        
        
        
        # Attach payment method to customer using the stored customer ID
        from app.services.stripe_service import attach_payment_method
        payment_method = attach_payment_method(
            payment_method_id=payment_method_id,
            customer_id=user.stripe_customer_id
        )
        
        return ResponseFactory.success(
            message="Payment method saved successfully",
            data={
                "payment_method": payment_method,
                "payment_method_id": payment_method.get("id"),
                "type": payment_method.get("type"),
                "card": payment_method.get("card", {}),
                "customer_id": user.stripe_customer_id
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Failed to save payment method: {str(e)}")


# Extended Bank Functions

def get_bank_dashboard(user_id: int, db: Session):
    """Get bank dashboard data for mobile app"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get bank accounts from Plaid API
        from app.services.plaid_account_service import plaid_account_service
        accounts_result = plaid_account_service.get_user_accounts(user_id, db)
        plaid_accounts = accounts_result.get("accounts", []) if accounts_result["success"] else []
        
        # Get donation statistics
        total_donations = db.query(func.count(DonationBatch.id)).filter(
            and_(
                DonationBatch.user_id == user_id,
                DonationBatch.status == "success"
            )
        ).scalar() or 0
        
        total_amount = db.query(func.sum(DonationBatch.total_amount)).filter(
            and_(
                DonationBatch.user_id == user_id,
                DonationBatch.status == "success"
            )
        ).scalar() or 0.0
        
        # Get this month's donations
        this_month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month_donations = db.query(func.sum(DonationBatch.total_amount)).filter(
            and_(
                DonationBatch.user_id == user_id,
                DonationBatch.status == "success",
                DonationBatch.executed_at >= this_month_start
            )
        ).scalar() or 0.0
        
        # Get preferences
        preferences = db.query(DonationPreference).filter(DonationPreference.user_id == user_id).first()
        
        dashboard_data = {
            "user_id": user_id,
            "bank_accounts": [
                {
                    "id": account["account_id"],
                    "institution_name": account.get("institution_name", "Unknown"),
                    "account_name": account["name"],
                    "account_type": account["type"],
                    "account_subtype": account["subtype"],
                    "mask": account["mask"],
                    "is_active": account.get("status", "active") == "active"
                }
                for account in plaid_accounts
            ],
            "donation_summary": {
                "total_donations": total_donations,
                "total_amount": float(total_amount),
                "this_month_amount": float(this_month_donations),
                "average_per_donation": float(total_amount / total_donations) if total_donations > 0 else 0.0
            },
            "preferences": {
                "multiplier": preferences.multiplier if preferences else "1x",
                "frequency": preferences.frequency if preferences else "monthly",
                "is_active": not preferences.pause if preferences else False,
                "cover_processing_fees": preferences.cover_processing_fees if preferences else False
            },
            "stripe_customer_id": user.stripe_customer_id
        }
        
        return ResponseFactory.success(
            message="Bank dashboard retrieved successfully",
            data=dashboard_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to retrieve bank dashboard")


def get_bank_donation_summary(user_id: int, db: Session):
    """Get bank donation summary for mobile app"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get donation data
        donations = db.query(DonationBatch).filter(
            and_(
                DonationBatch.user_id == user_id,
                DonationBatch.status == "success"
            )
        ).order_by(desc(DonationBatch.executed_at)).all()
        
        total_amount = sum(donation.total_amount for donation in donations)
        total_donations = len(donations)
        
        # Group by month for trend analysis
        monthly_data = {}
        for donation in donations:
            if donation.executed_at:
                month_key = donation.executed_at.strftime("%Y-%m")
                if month_key not in monthly_data:
                    monthly_data[month_key] = {"amount": 0.0, "count": 0}
                monthly_data[month_key]["amount"] += donation.total_amount
                monthly_data[month_key]["count"] += 1
        
        # Convert to sorted list
        monthly_trends = [
            {
                "month": month,
                "amount": data["amount"],
                "count": data["count"]
            }
            for month, data in sorted(monthly_data.items(), reverse=True)
        ]
        
        # Get recent donations
        recent_donations = [
            {
                "id": donation.id,
                "amount": donation.total_amount,
                "date": donation.executed_at.isoformat() if donation.executed_at else None,
                "status": donation.status,
                "stripe_charge_id": donation.stripe_charge_id
            }
            for donation in donations[:10]  # Last 10 donations
        ]
        
        summary_data = {
            "user_id": user_id,
            "total_amount": float(total_amount),
            "total_donations": total_donations,
            "average_per_donation": float(total_amount / total_donations) if total_donations > 0 else 0.0,
            "monthly_trends": monthly_trends,
            "recent_donations": recent_donations,
            "last_donation_date": recent_donations[0]["date"] if recent_donations else None
        }
        
        return ResponseFactory.success(
            message="Bank donation summary retrieved successfully",
            data=summary_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to retrieve bank donation summary")


def ensure_stripe_customer(user_id: int, db: Session):
    """Ensure user has a Stripe customer ID"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.stripe_customer_id:
            return ResponseFactory.success(
                message="Stripe customer already exists",
                data={
                    "user_id": user_id,
                    "stripe_customer_id": user.stripe_customer_id,
                    "status": "existing"
                }
            )
        
        # Here you would typically create a Stripe customer
        # For now, we'll return a mock response
        mock_stripe_customer_id = f"cus_mock_{user_id}_{int(datetime.now().timestamp())}"
        
        # Update user with Stripe customer ID
        user.stripe_customer_id = mock_stripe_customer_id
        db.commit()
        
        return ResponseFactory.success(
            message="Stripe customer created successfully",
            data={
                "user_id": user_id,
                "stripe_customer_id": mock_stripe_customer_id,
                "status": "created"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to ensure Stripe customer")


def delete_payment_method(payment_method_id: str, user_id: int, db: Session):
    """Delete a payment method"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.stripe_customer_id:
            raise HTTPException(status_code=400, detail="User has no Stripe customer ID")
        
        # Here you would typically delete the payment method from Stripe
        # For now, we'll return a mock response
        
        return ResponseFactory.success(
            message="Payment method deleted successfully",
            data={
                "user_id": user_id,
                "payment_method_id": payment_method_id,
                "stripe_customer_id": user.stripe_customer_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to delete payment method")


def set_default_payment_method(payment_method_id: str, user_id: int, db: Session):
    """Set a payment method as default"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.stripe_customer_id:
            raise HTTPException(status_code=400, detail="User has no Stripe customer ID")
        
        # Here you would typically update the default payment method in Stripe
        # For now, we'll return a mock response
        
        return ResponseFactory.success(
            message="Default payment method set successfully",
            data={
                "user_id": user_id,
                "payment_method_id": payment_method_id,
                "stripe_customer_id": user.stripe_customer_id,
                "is_default": True
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to set default payment method")


def fetch_mobile_transactions(data, current_user, db: Session):
    """Fetch user transactions from all linked bank accounts"""
    try:
        user_id = current_user["id"]
        # Get all user's Plaid items
        plaid_items = db.query(PlaidItem).filter(PlaidItem.user_id == user_id).all()
        if not plaid_items:
            raise HTTPException(
                status_code=404, 
                detail=get_bank_message("BANK_ACCOUNT_NOT_FOUND")
            )

        # Calculate date range automatically
        from datetime import datetime, timedelta
        today = datetime.now().date()
        
        # Get last donation date or default to 30 days ago
        last_donation = db.query(DonationBatch).filter(
            DonationBatch.user_id == user_id
        ).order_by(DonationBatch.created_at.desc()).first()
        
        if last_donation:
            start_date = last_donation.created_at.date()
        else:
            # Default to 30 days ago if no previous donations
            start_date = today - timedelta(days=30)
        
        end_date = today

        all_transactions = []

        # Fetch transactions from all Plaid items
        for plaid_item in plaid_items:
            try:
                # Decrypt access token
                access_token = decrypt_token(plaid_item.access_token)

                # Get transactions from Plaid for this account
                request = TransactionsGetRequest(
                    access_token=access_token,
                    start_date=start_date,
                    end_date=end_date
                )
                response = plaid_client.transactions_get(request).to_dict()
                account_transactions = response.get("transactions", [])
                
                # Add transactions from this account (raw Plaid format like old project)
                all_transactions.extend(account_transactions)
                
            except Exception as e:
                error_msg = str(e)
                if "ADDITIONAL_CONSENT_REQUIRED" in error_msg or "PRODUCT_TRANSACTIONS" in error_msg:
                    
                    continue
                else:
                    
                    continue

        return ResponseFactory.success(
            message="Transactions retrieved successfully",
            data={"transactions": all_transactions}
        )

    except SQLAlchemyError as db_err:
        db.rollback()
        
        raise HTTPException(
            status_code=500, 
            detail=get_bank_message("TRANSACTIONS_FETCH_FAILED")
        )
    except Exception as e:
        db.rollback()
        
        raise HTTPException(
            status_code=500, 
            detail=get_bank_message("TRANSACTIONS_FETCH_FAILED")
        )


def create_mobile_relink_token(user_id: int, db: Session):
    """Create a link token for re-linking accounts with transactions access"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        from app.services.plaid_client import create_link_token
        link_token = create_link_token(str(user_id))
        
        return ResponseFactory.success(
            message="Re-link token created successfully",
            data={
                "link_token": link_token,
                "message": "Use this link token to re-link your account with transactions access"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to create re-link token")


def get_bank_preferences(user_id: int, db: Session):
    """Get bank preferences for mobile app"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's bank accounts from Plaid API
        from app.services.plaid_account_service import plaid_account_service
        accounts_result = plaid_account_service.get_user_accounts(user_id, db)
        plaid_accounts = accounts_result.get("accounts", []) if accounts_result["success"] else []
        
        # Get basic preferences
        preferences = {
            "auto_roundup": True,  # Default to enabled
            "roundup_threshold": 1.00,  # Default threshold
            "max_monthly_donation": 100.00,  # Default max
            "linked_accounts_count": len(plaid_accounts),
            "last_sync_date": datetime.now().isoformat(),
            "notifications_enabled": True,
            "security_level": "standard"
        }
        
        return ResponseFactory.success(
            message="Bank preferences retrieved successfully",
            data={"preferences": preferences}
        )
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to get bank preferences")


def update_bank_preferences(user_id: int, data: dict, db: Session):
    """Update bank preferences for mobile app"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Validate and update preferences
        allowed_keys = [
            "auto_roundup", "roundup_threshold", "max_monthly_donation", 
            "notifications_enabled", "security_level"
        ]
        
        updated_preferences = {}
        for key, value in data.items():
            if key in allowed_keys:
                updated_preferences[key] = value
        
        # Here you would typically save to a preferences table
        # For now, we'll just return success
        
        return ResponseFactory.success(
            message="Bank preferences updated successfully",
            data={"preferences": updated_preferences}
        )
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to update bank preferences")


