import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from app.utils.database import get_db
from app.model.m_user import User
from app.model.m_plaid_items import PlaidItem
# PlaidAccount import removed - using on-demand Plaid API fetching
from app.services.plaid_transaction_service import plaid_transaction_service
import math


def process_user_roundups(user_id: int, db: Session):
    """Process roundups for a specific user using on-demand transaction fetching"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:

            return

        # Get user's Plaid items
        plaid_items = (
            db.query(PlaidItem).filter_by(user_id=user_id, status="active").all()
        )
        if not plaid_items:

            return

        # Calculate roundup amount using the new service
        roundup_result = plaid_transaction_service.calculate_roundup_amount(
            user_id=user_id,
            db=db,
            days_back=7,
            multiplier=1.0,  # Default multiplier, could be fetched from user preferences
        )

        if not roundup_result["success"]:

            return

        roundup_amount = roundup_result["roundup_amount"]
        transaction_count = roundup_result["transaction_count"]

    except Exception as e:
        pass


def process_all_roundups():
    """Process roundups for all active users"""
    db = next(get_db())
    try:
        users = db.query(User).filter(User.is_active == True).all()

        for user in users:
            process_user_roundups(user.id, db)

    except Exception as e:
        pass
    finally:
        db.close()


def calculate_period_totals():
    """Legacy function - period totals calculation removed

    This function is no longer needed as the system now uses:
    - Real-time calculations from Plaid API
    - DonorPayout and ChurchPayout tables for actual transaction records
    - Live aggregation instead of cached totals
    """
    return {
        "success": True,
        "message": "Period totals calculation deprecated - using real-time data",
    }


def get_user_roundup_summary(user_id: int, db: Session):
    """Get roundup summary for a specific user"""
    try:
        # Get transactions for roundup
        result = plaid_transaction_service.get_transactions_for_roundup(
            user_id=user_id, db=db, days_back=7
        )

        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Failed to fetch transactions"),
                "roundup_amount": 0.0,
                "transaction_count": 0,
            }

        transactions = result["transactions"]
        total_roundup = 0.0

        for transaction in transactions:
            amount = abs(transaction.get("amount", 0))
            if amount > 0:
                # Calculate roundup (round up to next dollar)
                roundup = (1.0 - (amount % 1.0)) if amount % 1.0 != 0 else 0.0
                total_roundup += roundup

        return {
            "success": True,
            "roundup_amount": round(total_roundup, 2),
            "transaction_count": len(transactions),
            "period_days": 7,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "roundup_amount": 0.0,
            "transaction_count": 0,
        }
