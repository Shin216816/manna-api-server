import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.model.m_user import User
from app.model.m_donation_batch import DonationBatch
from app.model.m_roundup_new import DonorPayout
from app.services.stripe_service import create_payment_intent, create_customer, attach_payment_method, create_setup_intent
from app.core.responses import ResponseFactory
from app.core.exceptions import UserNotFoundError, ValidationError
from app.utils.error_handler import handle_controller_errors
from fastapi import HTTPException

@handle_controller_errors
def create_payment_intent(current_user: dict, data, db: Session):
    """Create a Stripe Payment Intent for donor payments"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        amount_cents = data.get("amount_cents")
        if not amount_cents or amount_cents <= 0:
            raise ValidationError("Valid amount is required")

        # Get user's primary church ID
        primary_church = user.get_primary_church(db)
        church_id = primary_church.id if primary_church else None

        if not user.stripe_customer_id:
            customer_data = create_customer(
                email=user.email,
                name=f"{user.first_name} {user.last_name}",
                phone=user.phone
            )
            user.stripe_customer_id = customer_data["id"]
            db.commit()

        payment_intent = create_payment_intent(
            amount=amount_cents,
            currency="usd",
            customer_id=user.stripe_customer_id,
            description=f"Roundup donation for {user.first_name} {user.last_name}",
            metadata={
                "user_id": str(user.id),
                "church_id": str(church_id) if church_id else "",
                "period_key": data.get("period_key", "manual")
            },
            automatic_payment_methods=True
        )

        return ResponseFactory.success(
            message="Payment intent created successfully",
            data={
                "client_secret": payment_intent["client_secret"],
                "payment_intent_id": payment_intent["id"]
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create payment intent")

@handle_controller_errors
def create_setup_intent_controller(current_user: dict, data, db: Session):
    """Create a Stripe Setup Intent for adding payment methods"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        amount_cents = data.get("amount_cents", 100)  # Default to $1.00 for setup
        
        # Get user's primary church ID
        primary_church = user.get_primary_church(db)
        church_id = primary_church.id if primary_church else None

        if not user.stripe_customer_id:
            customer_data = create_customer(
                email=user.email,
                name=f"{user.first_name} {user.last_name}",
                phone=user.phone
            )
            user.stripe_customer_id = customer_data["id"]
            db.commit()

        setup_intent = create_setup_intent(
            customer_id=user.stripe_customer_id,
            description=f"Setup payment method for {user.first_name} {user.last_name}",
            metadata={
                "user_id": str(user.id),
                "church_id": str(church_id) if church_id else "",
                "purpose": "roundup_donations"
            }
        )

        return ResponseFactory.success(
            message="Setup intent created successfully",
            data={
                "client_secret": setup_intent["client_secret"],
                "setup_intent_id": setup_intent["id"]
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create setup intent")

@handle_controller_errors
def set_default_payment_method(current_user: dict, data, db: Session):
    """Set default payment method for donor"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        payment_method_id = data.get("payment_method_id")
        if not payment_method_id:
            raise ValidationError("Payment method ID is required")

        if not user.stripe_customer_id:
            raise ValidationError("No Stripe customer found")

        attach_payment_method(
            payment_method_id=payment_method_id,
            customer_id=user.stripe_customer_id
        )

        return ResponseFactory.success(
            message="Default payment method set successfully",
            data={"payment_method_id": payment_method_id}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to set default payment method")

@handle_controller_errors
def get_payment_history(current_user: dict, db: Session):
    """Get donor's payment history"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    # Get donation batches instead of transactions
    donation_batches = db.query(DonationBatch).filter(
        DonationBatch.user_id == user.id
    ).order_by(DonationBatch.created_at.desc()).limit(50).all()

    return ResponseFactory.success(
        message="Payment history retrieved successfully",
        data={
            "payments": [
                {
                    "id": batch.id,
                    "amount_cents": int(batch.amount * 100),  # Convert to cents
                    "method_type": "roundup_donation",
                    "status": batch.status,
                    "period_key": batch.batch_number,
                    "created_at": batch.created_at.isoformat() if batch.created_at else None,
                    "transaction_count": batch.transaction_count,
                    "net_amount": float(batch.net_amount)
                }
                for batch in donation_batches
            ],
            "total_count": len(donation_batches)
        }
    )

@handle_controller_errors
def get_payment_methods(current_user: dict, db: Session):
    """Get donor's payment methods"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        from app.services.stripe_service import get_customer_payment_methods
        
        if not user.stripe_customer_id:
            return ResponseFactory.success(
                message="No payment methods found",
                data={"payment_methods": []}
            )

        payment_methods = get_customer_payment_methods(user.stripe_customer_id)

        return ResponseFactory.success(
            message="Payment methods retrieved successfully",
            data={"payment_methods": payment_methods}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get payment methods")
