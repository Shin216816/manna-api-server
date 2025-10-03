from fastapi import HTTPException
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from app.model.m_user import User
from app.model.m_plaid_items import PlaidItem
# PlaidAccount import removed - using on-demand Plaid API fetching
from app.model.m_donation_batch import DonationBatch
from app.model.m_donation_preference import DonationPreference
from app.model.m_church import Church
from app.core.responses import ResponseFactory
from app.services.plaid_client import plaid_client, get_transactions
try:
    from plaid.model.transactions_get_request import TransactionsGetRequest
except ImportError:
    # Fallback if plaid is not installed
    TransactionsGetRequest = None
from app.utils.encryption import decrypt_token


def get_mobile_pending_roundups(user_id: int, db: Session):
    """Get pending roundups for mobile app"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's Plaid items
        plaid_items = db.query(PlaidItem).filter(PlaidItem.user_id == user_id).all()
        if not plaid_items:
            return ResponseFactory.success(
                message="No bank accounts linked",
                data={"pending_roundups": [], "total_amount": 0.0}
            )
        
        # Get preferences
        preferences = db.query(DonationPreference).filter(DonationPreference.user_id == user_id).first()
        multiplier = preferences.multiplier if preferences else "1x"
        
        # Calculate pending roundups
        pending_roundups = []
        total_amount = 0.0
        
        # Get recent transactions for roundup calculation
        for plaid_item in plaid_items:
            try:
                access_token = decrypt_token(plaid_item.access_token)
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=30)  # Last 30 days
                
                request = TransactionsGetRequest(
                    access_token=access_token,
                    start_date=start_date,
                    end_date=end_date
                )
                response = plaid_client.transactions_get(request).to_dict()
                transactions = response.get("transactions", [])

        # Calculate roundups for each transaction
                for transaction in transactions[:10]:  # Limit to recent transactions
                    amount = abs(transaction.get("amount", 0))
                    if amount > 0:
                        rounded_amount = (int(amount) + 1) - amount
                        if rounded_amount > 0:
                            # Apply multiplier
                            if multiplier == "2x":
                                rounded_amount *= 2
                            elif multiplier == "5x":
                                rounded_amount *= 5
                            
                            pending_roundups.append({
                                "transaction_id": transaction.get("transaction_id"),
                                "amount": round(amount, 2),
                                "roundup_amount": round(rounded_amount, 2),
                                "date": transaction.get("date"),
                                "merchant_name": transaction.get("merchant_name", "Unknown")
                            })
                            total_amount += rounded_amount
                            
            except Exception as e:
                
                continue

        return ResponseFactory.success(
            message="Pending roundups retrieved successfully",
            data={
                "pending_roundups": pending_roundups,
                "total_amount": round(total_amount, 2),
                "multiplier": multiplier,
                "is_paused": preferences.pause if preferences else False
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to get pending roundups")


def get_mobile_roundup_settings(user_id: int, db: Session):
    """Get roundup settings for mobile app"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get preferences
        preferences = db.query(DonationPreference).filter(DonationPreference.user_id == user_id).first()
        
        if not preferences:
            # Return default settings if no preferences exist
            # Get user's primary church ID
            primary_church = user.get_primary_church(db)
            church_id = primary_church.id if primary_church else None
            
            return ResponseFactory.success(
                message="Roundup settings retrieved successfully",
                data={
                    "pause": False,
                    "multiplier": "1x",
                    "frequency": "biweekly",
                    "cover_processing_fees": True,
                    "church_ids": [church_id] if church_id else []
            }
        )
        
        # Get user's primary church ID
        primary_church = user.get_primary_church(db)
        church_id = primary_church.id if primary_church else None
        
        return ResponseFactory.success(
            message="Roundup settings retrieved successfully",
            data={
                "pause": preferences.pause,
                "multiplier": preferences.multiplier,
                "frequency": preferences.frequency,
                "cover_processing_fees": preferences.cover_processing_fees,
                "church_ids": [church_id] if church_id else []
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to get roundup settings")


def update_mobile_roundup_settings(user_id: int, settings_data: Dict[str, Any], db: Session):
    """Update roundup settings for mobile app"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get or create preferences
        preferences = db.query(DonationPreference).filter(DonationPreference.user_id == user_id).first()
        
        if not preferences:
            preferences = DonationPreference(
                user_id=user_id,
                pause=settings_data.get("pause", False),
                multiplier=settings_data.get("multiplier", "1x"),
                frequency=settings_data.get("frequency", "biweekly"),
                cover_processing_fees=settings_data.get("cover_processing_fees", True)
            )
            db.add(preferences)
        else:
            # Update existing preferences
            if "pause" in settings_data:
                preferences.pause = settings_data["pause"]
            if "multiplier" in settings_data:
                preferences.multiplier = settings_data["multiplier"]
            if "frequency" in settings_data:
                preferences.frequency = settings_data["frequency"]
            if "cover_processing_fees" in settings_data:
                preferences.cover_processing_fees = settings_data["cover_processing_fees"]
        
        db.commit()
        db.refresh(preferences)
        
        # Get user's primary church ID
        primary_church = user.get_primary_church(db)
        church_id = primary_church.id if primary_church else None
        
        return ResponseFactory.success(
            message="Roundup settings updated successfully",
            data={
                "pause": preferences.pause,
                "multiplier": preferences.multiplier,
                "frequency": preferences.frequency,
                "cover_processing_fees": preferences.cover_processing_fees,
                "church_ids": [church_id] if church_id else []
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to update roundup settings")


def get_mobile_impact_summary(user_id: int, db: Session):
    """Get impact summary for mobile app"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's primary church
        primary_church = user.get_primary_church(db)
        church = primary_church
        
        # Get donation statistics
        total_donated = db.query(func.sum(DonationBatch.total_amount)).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        ).scalar() or 0.0
        
        # Get this month's donations
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
            message="Impact summary retrieved successfully",
            data={
                "total_donated": round(float(total_donated), 2),
                "this_month_donated": round(float(this_month_donated), 2),
                "donation_count": donation_count,
                "church_name": church.name if church else None,
                "church_id": church.id if church else None,
                "currency": "USD",
                "impact_metrics": {
                    "families_helped": int(total_donated / 50) if total_donated > 0 else 0,
                    "meals_provided": int(total_donated / 5) if total_donated > 0 else 0
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to get impact summary")


def quick_toggle_roundups(user_id: int, pause: bool, db: Session):
    """Quick toggle roundups on/off"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get or create preferences
        preferences = db.query(DonationPreference).filter(DonationPreference.user_id == user_id).first()
        
        if not preferences:
            preferences = DonationPreference(
                user_id=user_id,
                pause=pause,
                multiplier="1x",
                frequency="biweekly",
                cover_processing_fees=True
            )
            db.add(preferences)
        else:
            preferences.pause = pause
        
        db.commit()
        db.refresh(preferences)
        
        return ResponseFactory.success(
            message=f"Roundups {'paused' if pause else 'activated'} successfully",
            data={
                "pause": preferences.pause,
                "status": "paused" if pause else "active"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to toggle roundups")
