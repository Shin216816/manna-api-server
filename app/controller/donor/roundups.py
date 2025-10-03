import logging
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from sqlalchemy import func

from app.schema.donor_schema import (
    DonorRoundupSettingsRequest, DonorPendingRoundupsRequest,
    DonorToggleRoundupsRequest, DonorCalculateRoundupsRequest,
    DonorRoundupHistoryRequest
)
from app.model.m_user import User
from app.model.m_donation_preference import DonationPreference
# Removed RoundupLedger - using real-time calculations instead
# Removed PeriodTotal - using real-time calculations instead
from app.model.m_plaid_items import PlaidItem
from app.services.plaid_client import get_transactions
from app.core.responses import ResponseFactory
from app.core.exceptions import UserNotFoundError, ValidationError
from app.utils.error_handler import handle_controller_errors
from fastapi import HTTPException
import math

@handle_controller_errors
def get_roundup_settings(current_user: dict, db: Session):
    """Get donor roundup settings and preferences"""
    
    # Handle different current_user structures
    user_id = None
    if hasattr(current_user, 'id') and not isinstance(current_user, dict):
        # current_user is a User model instance
        user_id = current_user.id
    elif isinstance(current_user, dict):
        # current_user is a dictionary
        if 'user_id' in current_user:
            user_id = current_user['user_id']
        elif 'id' in current_user:
            user_id = current_user['user_id']
    
    if not user_id:
        raise UserNotFoundError(details={"message": "User ID not found in authentication data"})
    
    user = User.get_by_id(db, user_id)
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    preferences = db.query(DonationPreference).filter(
        DonationPreference.user_id == user.id
    ).first()

    if not preferences:
        preferences = DonationPreference(
            user_id=user.id,
            frequency="biweekly",
            multiplier="1x",
            pause=False,
            cover_processing_fees=False,
            monthly_cap=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(preferences)
        db.commit()
        db.refresh(preferences)

    # Calculate monthly roundup estimates based on recent transactions
    monthly_estimates = {}
    try:
        plaid_item = db.query(PlaidItem).filter(
            PlaidItem.user_id == user.id,
            PlaidItem.status == "active"
        ).first()
        
        if plaid_item:
            # Get recent transactions for estimation
            transactions_data = get_transactions(
                access_token=plaid_item.access_token,
                days_back=30
            )
            
            transactions = transactions_data.get("transactions", [])
            base_monthly_roundup = 0
            
            # Calculate base roundup from spending transactions
            for transaction in transactions:
                if transaction["amount"] < 0:  # Negative amounts are spending
                    amount = abs(transaction["amount"])
                    # Calculate base roundup: amount needed to reach next whole dollar
                    base_roundup = round(1.0 - (amount % 1.0), 2)
                    if base_roundup == 1.0:
                        base_roundup = 0.0  # already a whole dollar
                    base_monthly_roundup += base_roundup
            
            # Calculate estimates for each multiplier
            multiplier_values = {"1x": 1, "2x": 2, "3x": 3, "5x": 5}
            for multiplier, value in multiplier_values.items():
                monthly_estimates[multiplier] = {
                    "base_amount": round(base_monthly_roundup, 2),
                    "multiplied_amount": round(base_monthly_roundup * value, 2),
                    "annual_impact": round(base_monthly_roundup * value * 12, 2)
                }
            
        else:
            pass
            
    except Exception as e:
        pass
        monthly_estimates = {}

    return ResponseFactory.success(
        message="Roundup settings retrieved successfully",
        data={
            "frequency": preferences.frequency,
            "multiplier": preferences.multiplier,
            "pause": preferences.pause,
            "cover_processing_fees": preferences.cover_processing_fees,
            "monthly_cap": float(preferences.monthly_cap) if preferences.monthly_cap else None,
            "minimum_roundup": float(preferences.minimum_roundup) if preferences.minimum_roundup else None,
            "church_id": preferences.target_church_id,
            "created_at": preferences.created_at,
            "updated_at": preferences.updated_at,
            "monthly_estimates": monthly_estimates
        }
    )

@handle_controller_errors
def update_roundup_settings(current_user: dict, data: DonorRoundupSettingsRequest, db: Session):
    """Update donor roundup settings"""
    
    # Debug logging
    logging.info(f"Received roundup settings update request: {data}")
    logging.info(f"Data types: monthly_cap={type(data.monthly_cap)}, minimum_roundup={type(data.minimum_roundup)}, church_id={type(data.church_id)}")
    
    # Handle different current_user structures
    user_id = None
    if hasattr(current_user, 'id') and not isinstance(current_user, dict):
        # current_user is a User model instance
        user_id = current_user.id
    elif isinstance(current_user, dict):
        # current_user is a dictionary
        if 'user_id' in current_user:
            user_id = current_user['user_id']
        elif 'id' in current_user:
            user_id = current_user['user_id']
    
    if not user_id:
        raise UserNotFoundError(details={"message": "User ID not found in authentication data"})
    
    user = User.get_by_id(db, user_id)
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    preferences = db.query(DonationPreference).filter(
        DonationPreference.user_id == user.id
    ).first()

    if not preferences:
        preferences = DonationPreference(
            user_id=user.id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(preferences)

    if data.frequency is not None:
        if data.frequency not in ["weekly", "biweekly", "monthly"]:
            raise ValidationError("Frequency must be 'weekly', 'biweekly', or 'monthly'")
        preferences.frequency = data.frequency

    if data.multiplier is not None:
        if data.multiplier not in ["1x", "2x", "3x", "5x"]:
            raise ValidationError("Multiplier must be '1x', '2x', '3x', or '5x'")
        preferences.multiplier = data.multiplier

    if data.pause is not None:
        preferences.pause = data.pause

    if data.cover_processing_fees is not None:
        preferences.cover_processing_fees = data.cover_processing_fees

    if data.monthly_cap is not None:
        if data.monthly_cap < 0:
            raise ValidationError("Monthly cap must be non-negative")
        logging.info(f"Setting monthly_cap to: {data.monthly_cap}")
        preferences.monthly_cap = float(data.monthly_cap)

    if data.minimum_roundup is not None:
        if data.minimum_roundup < 0:
            raise ValidationError("Minimum roundup must be non-negative")
        logging.info(f"Setting minimum_roundup to: {data.minimum_roundup}")
        preferences.minimum_roundup = float(data.minimum_roundup)

    if data.church_id is not None:
        logging.info(f"Setting target_church_id to: {data.church_id}")
        preferences.target_church_id = int(data.church_id)

    preferences.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(preferences)

    # Debug logging after update
    logging.info(f"Updated preferences: monthly_cap={preferences.monthly_cap}, minimum_roundup={preferences.minimum_roundup}, target_church_id={preferences.target_church_id}")

    return ResponseFactory.success(
        message="Roundup settings updated successfully",
        data={
            "frequency": preferences.frequency,
            "multiplier": preferences.multiplier,
            "pause": preferences.pause,
            "cover_processing_fees": preferences.cover_processing_fees,
            "monthly_cap": float(preferences.monthly_cap) if preferences.monthly_cap else None,
            "minimum_roundup": float(preferences.minimum_roundup) if preferences.minimum_roundup else None,
            "church_id": preferences.target_church_id
        }
    )

@handle_controller_errors
def get_pending_roundups(current_user: dict, data: DonorPendingRoundupsRequest, db: Session):
    """Get donor's pending roundups"""
    
    # Handle different current_user structures
    user_id = None
    if hasattr(current_user, 'id') and not isinstance(current_user, dict):
        # current_user is a User model instance
        user_id = current_user.id
    elif isinstance(current_user, dict):
        # current_user is a dictionary
        if 'user_id' in current_user:
            user_id = current_user['user_id']
        elif 'id' in current_user:
            user_id = current_user['user_id']
    
    if not user_id:
        raise UserNotFoundError(details={"message": "User ID not found in authentication data"})
    
    user = User.get_by_id(db, user_id)
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    preferences = db.query(DonationPreference).filter(
        DonationPreference.user_id == user.id
    ).first()

    if not preferences or preferences.pause:
        return ResponseFactory.success(
            message="Roundups are paused",
            data={
                "pending_roundups": 0,
                "multiplier": preferences.multiplier if preferences else "1x",
                "is_paused": True
            }
        )

    # Calculate pending roundups from real-time Plaid transactions
    try:
        from app.services.roundup_service import roundup_service
        
        # Get recent transactions and calculate roundups
        multiplier_value = float(preferences.multiplier.replace("x", ""))
        roundup_transactions = roundup_service.calculate_roundups(
            user_id=user.id,
            db=db,
            multiplier=multiplier_value,
            threshold=1.0
        )
        
        # Sum up pending roundups
        total_pending_cents = sum(t.roundup_amount_cents for t in roundup_transactions)
        
        return ResponseFactory.success(
            message="Pending roundups retrieved successfully",
            data={
                "pending_roundups": total_pending_cents / 100,
                "multiplier": preferences.multiplier,
                "is_paused": False,
                "transaction_count": len(roundup_transactions)
            }
        )
    except Exception as e:
        # Fallback to zero if calculation fails
        return ResponseFactory.success(
            message="Pending roundups retrieved successfully",
            data={
                "pending_roundups": 0.0,
                "multiplier": preferences.multiplier,
                "is_paused": False,
                "transaction_count": 0
            }
        )

@handle_controller_errors
def calculate_roundups(current_user: dict, data: DonorCalculateRoundupsRequest, db: Session):
    """Calculate roundups for recent transactions"""
    
    # Handle different current_user structures
    user_id = None
    if hasattr(current_user, 'id') and not isinstance(current_user, dict):
        # current_user is a User model instance
        user_id = current_user.id
    elif isinstance(current_user, dict):
        # current_user is a dictionary
        if 'user_id' in current_user:
            user_id = current_user['user_id']
        elif 'id' in current_user:
            user_id = current_user['user_id']
    
    if not user_id:
        raise UserNotFoundError(details={"message": "User ID not found in authentication data"})
    
    user = User.get_by_id(db, user_id)
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        plaid_item = db.query(PlaidItem).filter(
            PlaidItem.user_id == user.id,
            PlaidItem.status == "active"
        ).first()
        
        if not plaid_item:
            raise ValidationError("No active Plaid connection found")

        days_back = getattr(data, "days_back", 30)
        
        transactions_data = get_transactions(
            access_token=plaid_item.access_token,
            days_back=days_back
        )

        
        total_roundup = 0
        transaction_roundups = []
        
        # Handle the correct Plaid API response structure
        # The response has transactions directly, not nested under "transactions" key
        transactions = transactions_data.get("transactions", [])
        
        
        for transaction in transactions:
            # Process NEGATIVE amounts (spending transactions)
            # Negative amounts are debits/spending, positive amounts are credits/deposits
            if transaction["amount"] < 0:
                amount = abs(transaction["amount"])
                # Calculate roundup: round up to next dollar and subtract original amount
                roundup = math.ceil(amount) - amount
                total_roundup += roundup
                
                
                transaction_roundups.append({
                    "transaction_id": transaction["transaction_id"],
                    "name": transaction["name"],
                    "amount": transaction["amount"],
                    "roundup": roundup,
                    "date": transaction["date"].isoformat() if hasattr(transaction["date"], 'isoformat') else str(transaction["date"])
                })
        
        
        preferences = db.query(DonationPreference).filter(
            DonationPreference.user_id == user.id
        ).first()
        
        multiplier_value = int(preferences.multiplier.replace("x", "")) if preferences else 1
        total_with_multiplier = total_roundup * multiplier_value
        
        return ResponseFactory.success(
            message="Roundups calculated successfully",
            data={
                "total_roundup": total_roundup,
                "total_with_multiplier": total_with_multiplier,
                "multiplier": preferences.multiplier if preferences else "1x",
                "days_back": days_back,
                "transactions": transaction_roundups[:10]
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to calculate roundups")

@handle_controller_errors
def get_monthly_estimates(current_user: dict, db: Session):
    """Get detailed monthly roundup estimates for all multiplier options"""
    
    # Handle different current_user structures
    user_id = None
    if hasattr(current_user, 'id') and not isinstance(current_user, dict):
        # current_user is a User model instance
        user_id = current_user.id
    elif isinstance(current_user, dict):
        # current_user is a dictionary
        if 'user_id' in current_user:
            user_id = current_user['user_id']
        elif 'id' in current_user:
            user_id = current_user['user_id']
    
    if not user_id:
        raise UserNotFoundError(details={"message": "User ID not found in authentication data"})
    
    user = User.get_by_id(db, user_id)
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        plaid_item = db.query(PlaidItem).filter(
            PlaidItem.user_id == user.id,
            PlaidItem.status == "active"
        ).first()
        
        if not plaid_item:
            raise ValidationError("No active Plaid connection found")

        # Get recent transactions for estimation
        transactions_data = get_transactions(
            access_token=plaid_item.access_token,
            days_back=30
        )
        
        transactions = transactions_data.get("transactions", [])
        base_monthly_roundup = 0
        transaction_details = []
        
        # Calculate base roundup from spending transactions
        for transaction in transactions:
            if transaction["amount"] < 0:  # Negative amounts are spending
                amount = abs(transaction["amount"])
                # Calculate base roundup: amount needed to reach next whole dollar
                base_roundup = round(1.0 - (amount % 1.0), 2)
                if base_roundup == 1.0:
                    base_roundup = 0.0  # already a whole dollar
                base_monthly_roundup += base_roundup
                
                transaction_details.append({
                    "name": transaction["name"],
                    "amount": transaction["amount"],
                    "roundup": base_roundup,
                    "date": transaction["date"].isoformat() if hasattr(transaction["date"], 'isoformat') else str(transaction["date"])
                })
        
        # Calculate estimates for each multiplier
        multiplier_values = {"1x": 1, "2x": 2, "3x": 3, "5x": 5}
        estimates = {}
        
        for multiplier, value in multiplier_values.items():
            base_roundup = round(base_monthly_roundup, 2)
            multiplied_amount = round(base_roundup * value, 2)
            
            estimates[multiplier] = {
                "base_amount": base_roundup,
                "multiplied_amount": multiplied_amount,
                "annual_impact": round(multiplied_amount * 12, 2),
                "description": f"Round up to the next dollar and multiply by {value}",
                "example": f"Example: ${1.23} → ${1.54} (${base_roundup} × {value})" if value == 2 else ""
            }
        
        
        return ResponseFactory.success(
            message="Monthly estimates calculated successfully",
            data={
                "base_monthly_roundup": round(base_monthly_roundup, 2),
                "multiplier_options": estimates,
                "transaction_count": len(transaction_details),
                "sample_transactions": transaction_details[:10],  # Show first 10 transactions
                "calculation_period": "30 days",
                "note": "Estimates based on recent spending transactions (negative amounts)"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to calculate monthly estimates")

@handle_controller_errors
def get_roundup_history(current_user: dict, data: DonorRoundupHistoryRequest, db: Session):
    """Get donor's roundup history"""
    
    # Handle different current_user structures
    user_id = None
    if hasattr(current_user, 'id') and not isinstance(current_user, dict):
        # current_user is a User model instance
        user_id = current_user.id
    elif isinstance(current_user, dict):
        # current_user is a dictionary
        if 'user_id' in current_user:
            user_id = current_user['user_id']
        elif 'id' in current_user:
            user_id = current_user['user_id']
    
    if not user_id:
        raise UserNotFoundError(details={"message": "User ID not found in authentication data"})
    
    user = User.get_by_id(db, user_id)
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})
    page = getattr(data, "page", 1)
    limit = getattr(data, "limit", 20)
    offset = (page - 1) * limit

    # Get roundup history from actual donation transactions instead of ledger
    try:
        from app.model.m_roundup_new import DonorPayout
        
        # Query actual roundup donations made by this user
        roundup_donations = db.query(DonorPayout).filter(
            DonorPayout.user_id == user.id,
            DonorPayout.donation_type == "roundup"
        ).order_by(DonorPayout.created_at.desc()).offset(offset).limit(limit).all()
        
        total_count = db.query(DonorPayout).filter(
            DonorPayout.user_id == user.id,
            DonorPayout.donation_type == "roundup"
        ).count()
        
        return ResponseFactory.success(
            message="Roundup history retrieved successfully",
            data={
                "roundups": [
                    {
                        "id": payout.id,
                        "roundup_cents": int(payout.donation_amount * 100),  # Convert to cents
                        "computed_at": payout.created_at.isoformat(),
                        "status": payout.status,
                        "church_name": "Unknown"  # Church info would need to be fetched separately
                    }
                    for payout in roundup_donations
                ],
                "total_count": total_count,
                "page": page,
                "limit": limit,
                "has_more": (offset + limit) < total_count
            }
        )
    except Exception as e:
        # Fallback to empty history if query fails
        return ResponseFactory.success(
            message="Roundup history retrieved successfully",
            data={
                "roundups": [],
                "total_count": 0,
                "page": page,
                "limit": limit,
                "has_more": False
            }
        )

@handle_controller_errors
def toggle_roundups(current_user: dict, data: DonorToggleRoundupsRequest, db: Session):
    """Toggle roundups on/off"""
    
    # Handle different current_user structures
    user_id = None
    if hasattr(current_user, 'id') and not isinstance(current_user, dict):
        # current_user is a User model instance
        user_id = current_user.id
    elif isinstance(current_user, dict):
        # current_user is a dictionary
        if 'user_id' in current_user:
            user_id = current_user['user_id']
        elif 'id' in current_user:
            user_id = current_user['user_id']
    
    if not user_id:
        raise UserNotFoundError(details={"message": "User ID not found in authentication data"})
    
    user = User.get_by_id(db, user_id)
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    preferences = db.query(DonationPreference).filter(
        DonationPreference.user_id == user.id
    ).first()

    if not preferences:
        preferences = DonationPreference(
            user_id=user.id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(preferences)

    preferences.pause = data.pause
    preferences.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(preferences)

    return ResponseFactory.success(
        message=f"Roundups {'paused' if data.pause else 'resumed'} successfully",
        data={
            "pause": preferences.pause
        }
    )
