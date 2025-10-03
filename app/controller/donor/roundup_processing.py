import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from sqlalchemy import desc, and_, func
from typing import List, Dict, Any

# PlaidTransaction import removed - using on-demand Plaid API fetching
# RoundupTransaction removed - using DonationBatch instead
from app.model.m_donation_preference import DonationPreference
from app.model.m_donation_batch import DonationBatch
from app.core.responses import ResponseFactory
from app.core.exceptions import UserNotFoundError, ValidationError
from app.utils.error_handler import handle_controller_errors
from fastapi import HTTPException

@handle_controller_errors
def get_pending_roundups(user_id: int, db: Session):
    """
    Get pending roundups for user using on-demand Plaid API fetching
    
    Retrieves all pending roundup transactions for the specified user
    that are ready to be collected and processed as donations.
    
    Args:
        user_id: The ID of the user
        db: Database session
    
    Returns:
        Response with pending roundups data
    """
    from app.services.plaid_transaction_service import plaid_transaction_service
    
    # Get user's donation preferences
    donation_prefs = db.query(DonationPreference).filter(
        DonationPreference.user_id == user_id
    ).first()
    
    if not donation_prefs:
        return ResponseFactory.success(
            message="No donation preferences found",
            data={
                "total_amount": 0.0,
                "transaction_count": 0,
                "transactions": [],
                "settings": {
                    "frequency": "biweekly",
                    "multiplier": "1x",
                    "pause": False
                }
            }
        )
    
    # Check if round-ups are paused
    if donation_prefs.pause:
        return ResponseFactory.success(
            message="Round-ups are currently paused",
            data={
                "total_amount": 0.0,
                "transaction_count": 0,
                "transactions": [],
                "settings": {
                    "frequency": donation_prefs.frequency,
                    "multiplier": donation_prefs.multiplier,
                    "pause": True,
                    "monthly_cap": float(donation_prefs.monthly_cap) if donation_prefs.monthly_cap else None
                }
            }
        )
    
    # Get multiplier
    multiplier = 1.0
    if donation_prefs.multiplier:
        multiplier = float(donation_prefs.multiplier.replace('x', ''))
    
    # Use PlaidTransactionService to calculate roundup amount on-demand
    try:
        roundup_result = plaid_transaction_service.calculate_roundup_amount(
            user_id=user_id,
            db=db,
            days_back=7,  # Get transactions from last 7 days
            multiplier=multiplier
        )
        
        if not roundup_result["success"]:
            return ResponseFactory.success(
                message="No transactions found for roundup calculation",
                data={
                    "total_amount": 0.0,
                    "transaction_count": 0,
                    "transactions": [],
                    "settings": {
                        "frequency": donation_prefs.frequency,
                        "multiplier": donation_prefs.multiplier,
                        "pause": donation_prefs.pause,
                        "monthly_cap": float(donation_prefs.monthly_cap) if donation_prefs.monthly_cap else None
                    }
                }
            )
        
        # Format transactions for response
        processed_transactions = []
        for transaction in roundup_result.get("transactions", []):
            processed_transaction = {
                "id": transaction.get("transaction_id", ""),
                "amount": abs(float(transaction.get("amount", 0))),
                "date": transaction.get("date", ""),
                "merchant_name": transaction.get("merchant_name") or "Unknown Merchant",
                "category": transaction.get("category", ["other"])[0] if transaction.get("category") else "other",
                "roundup_amount": transaction.get("roundup_amount", 0.0),
                "description": transaction.get("name", "")
            }
            processed_transactions.append(processed_transaction)
        
        return ResponseFactory.success(
            message="Pending round-ups retrieved successfully",
            data={
                "total_amount": round(roundup_result.get("total_roundup", 0.0), 2),
                "transaction_count": len(processed_transactions),
                "transactions": processed_transactions,
                "settings": {
                    "frequency": donation_prefs.frequency,
                    "multiplier": donation_prefs.multiplier,
                    "pause": donation_prefs.pause,
                    "monthly_cap": float(donation_prefs.monthly_cap) if donation_prefs.monthly_cap else None
                }
            }
        )
        
    except Exception as e:
        logging.error(f"Error calculating roundup amount: {str(e)}")
        return ResponseFactory.success(
            message="Error calculating roundups",
            data={
                "total_amount": 0.0,
                "transaction_count": 0,
                "transactions": [],
                "settings": {
                    "frequency": donation_prefs.frequency,
                    "multiplier": donation_prefs.multiplier,
                    "pause": donation_prefs.pause,
                    "monthly_cap": float(donation_prefs.monthly_cap) if donation_prefs.monthly_cap else None
                }
            }
        )

@handle_controller_errors
def collect_pending_roundups(user_id: int, db: Session):
    """
    Collect pending roundups and create donation batch
    
    Processes all pending roundup transactions for the user and creates
    a donation batch that can be processed for payment.
    
    Args:
        user_id: The ID of the user
        db: Database session
    
    Returns:
        Response with donation batch information
    """
    
    # Get user's donation preferences
    donation_prefs = db.query(DonationPreference).filter(
        DonationPreference.user_id == user_id
    ).first()
    
    if not donation_prefs:
        raise HTTPException(status_code=400, detail="No donation preferences found")
    
    if donation_prefs.pause:
        raise HTTPException(status_code=400, detail="Round-ups are currently paused")
    
    # Get pending round-ups
    pending_data = get_pending_roundups(user_id, db)
    pending_roundups = pending_data.data
    
    if pending_roundups["total_amount"] <= 0:
        return ResponseFactory.success(
            message="No pending round-ups to collect",
            data={
                "batch_id": None,
                "amount": 0.0,
                "transaction_count": 0
            }
        )
    
    # Create donation batch
    batch = DonationBatch(
        user_id=user_id,
        church_id=donation_prefs.target_church_id,
        amount=pending_roundups["total_amount"],
        transaction_count=len(pending_roundups["transactions"]),
        status="pending",
        collection_date=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc)
    )
    
    db.add(batch)
    db.commit()
    db.refresh(batch)
    
    # RoundupTransaction records removed - all data is now in DonationBatch
    # The DonationBatch already contains:
    # - transaction_count: Number of transactions processed
    # - amount: Total roundup amount
    # - status: Processing status
    # - user_id, church_id: User and church references
    
    db.commit()
    
    return ResponseFactory.success(
        message="Round-ups collected successfully",
        data={
            "batch_id": batch.id,
            "amount": float(batch.amount),
            "transaction_count": batch.transaction_count,
            "collection_date": batch.collection_date.isoformat()
        }
    )

@handle_controller_errors
def get_roundup_summary(user_id: int, db: Session):
    """Get round-up summary for the current user"""
    
    # Get user's donation preferences
    donation_prefs = db.query(DonationPreference).filter(
        DonationPreference.user_id == user_id
    ).first()
    
    if not donation_prefs:
        return ResponseFactory.success(
            message="No donation preferences found",
            data={
                "total_donated": 0.0,
                "total_collections": 0,
                "average_per_collection": 0.0,
                "this_month_donated": 0.0,
                "settings": {
                    "frequency": "biweekly",
                    "multiplier": "1x",
                    "pause": False
                }
            }
        )
    
    # Get total donated amount
    total_donated_result = db.query(
        func.sum(DonationBatch.amount)
    ).filter(
        and_(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        )
    ).scalar()
    
    total_donated = float(total_donated_result) if total_donated_result else 0.0
    
    # Get total collections count
    total_collections = db.query(DonationBatch).filter(
        and_(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        )
    ).count()
    
    # Calculate average per collection
    average_per_collection = total_donated / total_collections if total_collections > 0 else 0.0
    
    # Get this month's donations
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    this_month_result = db.query(
        func.sum(DonationBatch.amount)
    ).filter(
        and_(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed",
            DonationBatch.collection_date >= start_of_month
        )
    ).scalar()
    
    this_month_donated = float(this_month_result) if this_month_result else 0.0
    
    return ResponseFactory.success(
        message="Round-up summary retrieved successfully",
        data={
            "total_donated": round(total_donated, 2),
            "total_collections": total_collections,
            "average_per_collection": round(average_per_collection, 2),
            "this_month_donated": round(this_month_donated, 2),
            "settings": {
                "frequency": donation_prefs.frequency,
                "multiplier": donation_prefs.multiplier,
                "pause": donation_prefs.pause,
                "monthly_cap": float(donation_prefs.monthly_cap) if donation_prefs.monthly_cap else None
            }
        }
    )

def get_last_collection_date(user_id: int, db: Session) -> datetime:
    """Get the last collection date for the user"""
    
    last_batch = db.query(DonationBatch).filter(
        and_(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        )
    ).order_by(desc(DonationBatch.collection_date)).first()
    
    if last_batch:
        return last_batch.collection_date
    else:
        # If no previous collections, start from 30 days ago
        return datetime.now(timezone.utc) - timedelta(days=30)

def calculate_roundup_amount(amount: float, multiplier: float = 1.0) -> float:
    """Calculate round-up amount for a given transaction amount"""
    
    # Only calculate round-ups for positive amounts
    if amount <= 0:
        return 0.0
    
    # Calculate the round-up (ceiling - original amount)
    rounded_amount = float(amount).__ceil__()
    roundup = rounded_amount - amount
    
    # Apply multiplier
    final_roundup = roundup * multiplier
    
    # Round to 2 decimal places
    return round(final_roundup, 2)
