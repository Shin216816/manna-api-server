"""
Donor Round-up Collection Controller

Handles comprehensive round-up collection functionality:
- Round-up collection settings and preferences
- Transaction display with round-up calculations
- Pending round-ups tracking
- Collection frequency management
- Round-up multiplier and caps
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from app.model.m_user import User
from app.model.m_donation_preference import DonationPreference
from app.model.m_plaid_items import PlaidItem
from app.model.m_roundup_new import DonorPayout
from app.services.plaid_client import get_transactions
from app.core.responses import ResponseFactory
from app.core.exceptions import UserNotFoundError, ValidationError
from app.utils.error_handler import handle_controller_errors
from fastapi import HTTPException
import math


@handle_controller_errors
def get_roundup_collection_settings(current_user: dict, db: Session) -> ResponseFactory:
    """Get comprehensive round-up collection settings"""
    try:
        user = User.get_by_id(db, current_user["user_id"])
        if not user:
            raise UserNotFoundError(details={"message": "User not found"})

        # Get donation preferences
        preferences = db.query(DonationPreference).filter(
            DonationPreference.user_id == user.id
        ).first()

        if not preferences:
            # Create default preferences
            preferences = DonationPreference(
                user_id=user.id,
                frequency="biweekly",
                multiplier="1x",
                pause=False,
                cover_processing_fees=False,
                monthly_cap=None,
                minimum_roundup=1.00,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(preferences)
            db.commit()
            db.refresh(preferences)

        # Get next collection date
        next_collection_date = calculate_next_collection_date(preferences, db)

        # Get pending round-ups amount
        pending_amount = calculate_pending_roundups(user.id, db)

        return ResponseFactory.success(
            message="Round-up collection settings retrieved successfully",
            data={
                "collection_settings": {
                    "frequency": preferences.frequency,
                    "multiplier": preferences.multiplier,
                    "pause": preferences.pause,
                    "cover_processing_fees": preferences.cover_processing_fees,
                    "monthly_cap": float(preferences.monthly_cap) if preferences.monthly_cap else None,
                    "minimum_roundup": float(preferences.minimum_roundup),
                    "next_collection_date": next_collection_date.isoformat() if next_collection_date else None
                },
                "pending_roundups": {
                    "amount": pending_amount,
                    "next_collection_date": next_collection_date.isoformat() if next_collection_date else None
                },
                "available_frequencies": ["biweekly", "monthly"],
                "available_multipliers": ["1x", "2x", "3x", "5x"],
                "updated_at": preferences.updated_at.isoformat()
            }
        )

    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"Error getting round-up collection settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get round-up collection settings")


@handle_controller_errors
def update_roundup_collection_settings(
    data: dict, 
    current_user: dict, 
    db: Session
) -> ResponseFactory:
    """Update round-up collection settings"""
    try:
        user = User.get_by_id(db, current_user["user_id"])
        if not user:
            raise UserNotFoundError(details={"message": "User not found"})

        # Get or create donation preferences
        preferences = db.query(DonationPreference).filter(
            DonationPreference.user_id == user.id
        ).first()

        if not preferences:
            preferences = DonationPreference(
                user_id=user.id,
                created_at=datetime.now(timezone.utc)
            )
            db.add(preferences)

        # Update settings with validation
        if "frequency" in data:
            if data["frequency"] not in ["biweekly", "monthly"]:
                raise ValidationError("Frequency must be 'biweekly' or 'monthly'")
            preferences.frequency = data["frequency"]

        if "multiplier" in data:
            if data["multiplier"] not in ["1x", "2x", "3x", "5x"]:
                raise ValidationError("Multiplier must be '1x', '2x', '3x', or '5x'")
            preferences.multiplier = data["multiplier"]

        if "pause" in data:
            preferences.pause = data["pause"]

        if "cover_processing_fees" in data:
            preferences.cover_processing_fees = data["cover_processing_fees"]

        if "monthly_cap" in data:
            if data["monthly_cap"] is not None:
                if data["monthly_cap"] < 0:
                    raise ValidationError("Monthly cap must be positive")
                if data["monthly_cap"] > 1000.00:
                    raise ValidationError("Monthly cap cannot exceed $1,000.00")
            preferences.monthly_cap = data["monthly_cap"]

        if "minimum_roundup" in data:
            if data["minimum_roundup"] < 0.01 or data["minimum_roundup"] > 10.00:
                raise ValidationError("Minimum roundup must be between $0.01 and $10.00")
            preferences.minimum_roundup = data["minimum_roundup"]

        preferences.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(preferences)

        # Calculate next collection date
        next_collection_date = calculate_next_collection_date(preferences, db)

        return ResponseFactory.success(
            message="Round-up collection settings updated successfully",
            data={
                "collection_settings": {
                    "frequency": preferences.frequency,
                    "multiplier": preferences.multiplier,
                    "pause": preferences.pause,
                    "cover_processing_fees": preferences.cover_processing_fees,
                    "monthly_cap": float(preferences.monthly_cap) if preferences.monthly_cap else None,
                    "minimum_roundup": float(preferences.minimum_roundup),
                    "next_collection_date": next_collection_date.isoformat() if next_collection_date else None
                },
                "updated_at": preferences.updated_at.isoformat()
            }
        )

    except (UserNotFoundError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error updating round-up collection settings: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update round-up collection settings")


@handle_controller_errors
def get_recent_transactions_with_roundups(
    current_user: dict, 
    days_back: int = 7,
    db: Session = None
) -> ResponseFactory:
    """Get recent transactions with calculated round-ups"""
    try:
        user = User.get_by_id(db, current_user["user_id"])
        if not user:
            raise UserNotFoundError(details={"message": "User not found"})

        # Get donation preferences
        preferences = db.query(DonationPreference).filter(
            DonationPreference.user_id == user.id
        ).first()

        if not preferences:
            return ResponseFactory.success(
                message="No transactions found",
                data={"transactions": [], "total_roundup": 0.0}
            )

        # Get Plaid item
        plaid_item = db.query(PlaidItem).filter(
            PlaidItem.user_id == user.id,
            PlaidItem.status == "active"
        ).first()

        if not plaid_item:
            return ResponseFactory.success(
                message="No bank account linked",
                data={"transactions": [], "total_roundup": 0.0}
            )

        # Get transactions from Plaid
        transactions_data = get_transactions(
            access_token=plaid_item.access_token,
            days_back=days_back
        )

        transactions = transactions_data.get("transactions", [])
        multiplier_value = int(preferences.multiplier.replace("x", ""))

        # Calculate round-ups for each transaction
        transactions_with_roundups = []
        total_roundup = 0.0

        for transaction in transactions:
            if transaction["amount"] < 0:  # Only spending transactions
                amount = abs(transaction["amount"])
                
                # Calculate base roundup
                base_roundup = round(1.0 - (amount % 1.0), 2)
                if base_roundup == 1.0:
                    base_roundup = 0.0  # Already a whole dollar
                
                # Apply multiplier
                calculated_roundup = base_roundup * multiplier_value
                
                # Apply minimum roundup threshold
                if calculated_roundup > 0 and calculated_roundup < preferences.minimum_roundup:
                    calculated_roundup = preferences.minimum_roundup

                transactions_with_roundups.append({
                    "transaction_id": transaction.get("transaction_id"),
                    "amount": amount,
                    "description": transaction.get("name", "Unknown"),
                    "date": transaction.get("date"),
                    "merchant": transaction.get("merchant_name"),
                    "category": transaction.get("category", []),
                    "base_roundup": base_roundup,
                    "multiplier": preferences.multiplier,
                    "calculated_roundup": calculated_roundup,
                    "account_id": transaction.get("account_id")
                })

                total_roundup += calculated_roundup

        # Sort by date (most recent first)
        transactions_with_roundups.sort(key=lambda x: x["date"], reverse=True)

        return ResponseFactory.success(
            message="Recent transactions with round-ups retrieved successfully",
            data={
                "transactions": transactions_with_roundups,
                "total_roundup": round(total_roundup, 2),
                "multiplier": preferences.multiplier,
                "frequency": preferences.frequency,
                "days_back": days_back,
                "retrieved_at": datetime.now(timezone.utc).isoformat()
            }
        )

    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"Error getting transactions with round-ups: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get transactions with round-ups")


@handle_controller_errors
def get_pending_roundups_summary(current_user: dict, db: Session) -> ResponseFactory:
    """Get pending round-ups summary"""
    try:
        user = User.get_by_id(db, current_user["user_id"])
        if not user:
            raise UserNotFoundError(details={"message": "User not found"})

        # Get donation preferences
        preferences = db.query(DonationPreference).filter(
            DonationPreference.user_id == user.id
        ).first()

        if not preferences or preferences.pause:
            return ResponseFactory.success(
                message="Round-ups are paused or not configured",
                data={
                    "pending_amount": 0.0,
                    "transaction_count": 0,
                    "next_collection_date": None,
                    "is_paused": True
                }
            )

        # Calculate pending round-ups
        pending_amount = calculate_pending_roundups(user.id, db)
        next_collection_date = calculate_next_collection_date(preferences, db)

        # Get transaction count for current period
        transaction_count = get_transaction_count_for_period(user.id, db, preferences)

        return ResponseFactory.success(
            message="Pending round-ups summary retrieved successfully",
            data={
                "pending_amount": round(pending_amount, 2),
                "transaction_count": transaction_count,
                "next_collection_date": next_collection_date.isoformat() if next_collection_date else None,
                "frequency": preferences.frequency,
                "multiplier": preferences.multiplier,
                "is_paused": False
            }
        )

    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"Error getting pending round-ups summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get pending round-ups summary")


def calculate_next_collection_date(preferences: DonationPreference, db: Session) -> Optional[datetime]:
    """Calculate next collection date based on frequency and last payout"""
    try:
        # Get last payout
        last_payout = db.query(DonorPayout).filter(
            DonorPayout.user_id == preferences.user_id
        ).order_by(desc(DonorPayout.created_at)).first()

        if not last_payout:
            # No previous payouts, set next collection based on frequency
            if preferences.frequency == "biweekly":
                return datetime.now(timezone.utc) + timedelta(days=14)
            else:  # monthly
                return datetime.now(timezone.utc) + timedelta(days=30)

        # Calculate next collection based on frequency
        if preferences.frequency == "biweekly":
            return last_payout.created_at + timedelta(days=14)
        else:  # monthly
            return last_payout.created_at + timedelta(days=30)

    except Exception as e:
        logging.error(f"Error calculating next collection date: {str(e)}")
        return None


def calculate_pending_roundups(user_id: int, db: Session) -> float:
    """Calculate pending round-ups amount"""
    try:
        # Get donation preferences
        preferences = db.query(DonationPreference).filter(
            DonationPreference.user_id == user_id
        ).first()

        if not preferences or preferences.pause:
            return 0.0

        # Get Plaid item
        plaid_item = db.query(PlaidItem).filter(
            PlaidItem.user_id == user_id,
            PlaidItem.status == "active"
        ).first()

        if not plaid_item:
            return 0.0

        # Get last payout date
        last_payout = db.query(DonorPayout).filter(
            DonorPayout.user_id == user_id
        ).order_by(desc(DonorPayout.created_at)).first()

        # Calculate days back based on last payout or default to 7 days
        if last_payout:
            days_back = (datetime.now(timezone.utc) - last_payout.created_at).days
        else:
            days_back = 7

        # Get transactions
        transactions_data = get_transactions(
            access_token=plaid_item.access_token,
            days_back=days_back
        )

        transactions = transactions_data.get("transactions", [])
        multiplier_value = int(preferences.multiplier.replace("x", ""))
        total_roundup = 0.0

        for transaction in transactions:
            if transaction["amount"] < 0:  # Only spending transactions
                amount = abs(transaction["amount"])
                
                # Calculate base roundup
                base_roundup = round(1.0 - (amount % 1.0), 2)
                if base_roundup == 1.0:
                    base_roundup = 0.0
                
                # Apply multiplier
                calculated_roundup = base_roundup * multiplier_value
                
                # Apply minimum roundup threshold
                if calculated_roundup > 0 and calculated_roundup < preferences.minimum_roundup:
                    calculated_roundup = preferences.minimum_roundup

                total_roundup += calculated_roundup

        # Apply monthly cap if set
        if preferences.monthly_cap and total_roundup > preferences.monthly_cap:
            total_roundup = preferences.monthly_cap

        return total_roundup

    except Exception as e:
        logging.error(f"Error calculating pending round-ups: {str(e)}")
        return 0.0


def get_transaction_count_for_period(user_id: int, db: Session, preferences: DonationPreference) -> int:
    """Get transaction count for current collection period"""
    try:
        # Get Plaid item
        plaid_item = db.query(PlaidItem).filter(
            PlaidItem.user_id == user_id,
            PlaidItem.status == "active"
        ).first()

        if not plaid_item:
            return 0

        # Get last payout date
        last_payout = db.query(DonorPayout).filter(
            DonorPayout.user_id == user_id
        ).order_by(desc(DonorPayout.created_at)).first()

        # Calculate days back
        if last_payout:
            days_back = (datetime.now(timezone.utc) - last_payout.created_at).days
        else:
            days_back = 7

        # Get transactions
        transactions_data = get_transactions(
            access_token=plaid_item.access_token,
            days_back=days_back
        )

        transactions = transactions_data.get("transactions", [])
        
        # Count spending transactions
        spending_count = sum(1 for t in transactions if t["amount"] < 0)
        
        return spending_count

    except Exception as e:
        logging.error(f"Error getting transaction count: {str(e)}")
        return 0
