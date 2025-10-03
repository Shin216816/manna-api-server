import logging
import json
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime

from app.model.m_user import User
from app.services.stripe_service import (
    create_donor_customer,
    create_card_payment_method,
    create_ach_setup_intent,
    create_ach_payment_method,
    verify_ach_payment_method,
    create_digital_wallet_payment_method,
    list_customer_payment_methods,
    get_payment_method,
    detach_payment_method,
    create_test_charge,
    get_payment_method_requirements,
    create_financial_connections_session,
    create_payment_method_from_financial_connections,
    create_unified_payment_intent,
    create_setup_intent
)
from app.core.responses import ResponseFactory
from app.core.exceptions import UserNotFoundError, ValidationError
from app.utils.error_handler import handle_controller_errors
from fastapi import HTTPException
import stripe
from app.config import config

@handle_controller_errors
def save_completed_payment_method(
    current_user: dict,
    setup_intent_id: str,
    db: Session
) -> Dict[str, Any]:
    """Payment method is automatically saved in Stripe - no local storage needed"""
    try:
        # Set Stripe API key
        stripe.api_key = config.STRIPE_SECRET_KEY
        
        # Get the setup intent to extract payment method details
        setup_intent = stripe.SetupIntent.retrieve(setup_intent_id)
        
        if not setup_intent.payment_method:
            raise Exception("No payment method found in setup intent")
        
        payment_method_id = setup_intent.payment_method
        
        # Payment method is already saved in Stripe, just return success
        return ResponseFactory.success(
            message="Payment method saved successfully",
            data={"payment_method_id": payment_method_id}
        )
        
    except Exception as e:
        raise Exception(f"Payment method saving failed: {str(e)}")

@handle_controller_errors
def add_card_payment_method(
    current_user: dict,
    data: Dict[str, Any],
    db: Session
):
    """Add a new card payment method for a donor"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        payment_method_id = data.get("payment_method_id")
        if not payment_method_id:
            raise ValidationError("Payment method ID is required")

        # Get user's primary church ID
        primary_church = user.get_primary_church(db)
        church_id = primary_church.id if primary_church else None

        if not user.stripe_customer_id:
            customer_data = create_donor_customer({
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "church_id": church_id
            })
            user.stripe_customer_id = customer_data["id"]
            db.commit()

        stripe_payment_method = create_card_payment_method(
            payment_method_id=payment_method_id,
            customer_id=user.stripe_customer_id,
            metadata={
                "user_id": str(user.id),
                "church_id": str(church_id) if church_id else "",
                "source": "donor_app",
                "added_at": datetime.utcnow().isoformat()
            }
        )

        # Payment method is automatically saved in Stripe
        # No need to store locally

        return ResponseFactory.success(
            message="Card payment method added successfully",
            data={
                "payment_method_id": stripe_payment_method.get("id"),
                "type": stripe_payment_method.get("type"),
                "card_brand": stripe_payment_method.get("card", {}).get("brand"),
                "card_last4": stripe_payment_method.get("card", {}).get("last4")
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to add card payment method")

@handle_controller_errors
def get_payment_methods_enhanced(
    current_user: dict,
    db: Session
):
    """Get all payment methods for a donor with enhanced details"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        if not user.stripe_customer_id:
            return ResponseFactory.success(
                message="No payment methods found",
                data={
                    "payment_methods": [],
                    "total_count": 0
                }
            )

        # Get payment methods from Stripe
        stripe.api_key = config.STRIPE_SECRET_KEY
        stripe_payment_methods = stripe.PaymentMethod.list(
            customer=user.stripe_customer_id,
            type='card'
        )

        payment_methods = []
        for pm in stripe_payment_methods.data:
            method_data = {
                "id": pm.id,
                "type": pm.type,
                "is_default": pm.id == user.stripe_default_payment_method_id,
                "created_at": datetime.fromtimestamp(pm.created).isoformat()
            }

            if pm.type == "card" and pm.card:
                method_data.update({
                    "card_brand": pm.card.brand,
                    "card_last4": pm.card.last4,
                    "card_exp_month": pm.card.exp_month,
                    "card_exp_year": pm.card.exp_year,
                    "display_name": f"{pm.card.brand or 'Card'} •••• {pm.card.last4}"
                })
            elif pm.type == "us_bank_account" and pm.us_bank_account:
                method_data.update({
                    "bank_name": pm.us_bank_account.bank_name,
                    "bank_account_type": pm.us_bank_account.account_type,
                    "bank_account_last4": pm.us_bank_account.last4,
                    "display_name": f"{pm.us_bank_account.bank_name or 'Bank'} •••• {pm.us_bank_account.last4}"
                })

            payment_methods.append(method_data)

        return ResponseFactory.success(
            message="Payment methods retrieved successfully",
            data={
                "payment_methods": payment_methods,
                "total_count": len(payment_methods)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get payment methods")

@handle_controller_errors
def set_default_payment_method_enhanced(
    current_user: dict,
    data: Dict[str, Any],
    db: Session
):
    """Set a payment method as default"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        payment_method_id = data.get("payment_method_id")
        if not payment_method_id:
            raise ValidationError("Payment method ID is required")

        if not user.stripe_customer_id:
            raise ValidationError("Stripe customer not found")

        # Set Stripe API key
        stripe.api_key = config.STRIPE_SECRET_KEY

        # Verify the payment method belongs to the user
        payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
        if payment_method.customer != user.stripe_customer_id:
            raise ValidationError("Payment method not found")

        # Update the customer's default payment method in Stripe
        stripe.Customer.modify(
            user.stripe_customer_id,
            invoice_settings={
                "default_payment_method": payment_method_id
            }
        )

        # Update the user's default payment method ID in the database
        user.stripe_default_payment_method_id = payment_method_id
        db.commit()

        return ResponseFactory.success(
            message="Default payment method updated successfully",
            data={
                "payment_method_id": payment_method_id,
                "is_default": True
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to set default payment method")

@handle_controller_errors
def remove_payment_method_enhanced(
    current_user: dict,
    data: Dict[str, Any],
    db: Session
):
    """Remove a payment method"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        payment_method_id = data.get("payment_method_id")
        if not payment_method_id:
            raise ValidationError("Payment method ID is required")

        if not user.stripe_customer_id:
            raise ValidationError("Stripe customer not found")

        # Set Stripe API key
        stripe.api_key = config.STRIPE_SECRET_KEY

        # Verify the payment method belongs to the user
        payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
        if payment_method.customer != user.stripe_customer_id:
            raise ValidationError("Payment method not found")

        # Check if it's the default payment method
        if payment_method_id == user.stripe_default_payment_method_id:
            raise ValidationError("Cannot remove default payment method")

        # Detach the payment method from Stripe
        detach_payment_method(payment_method_id)

        return ResponseFactory.success(
            message="Payment method removed successfully",
            data={
                "payment_method_id": payment_method_id
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to remove payment method")

@handle_controller_errors
def verify_payment_method_enhanced(
    current_user: dict,
    data: Dict[str, Any],
    db: Session
):
    """Verify a payment method with a small test charge"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        payment_method_id = data.get("payment_method_id")
        if not payment_method_id:
            raise ValidationError("Payment method ID is required")

        if not user.stripe_customer_id:
            raise ValidationError("Stripe customer not found")

        # Set Stripe API key
        stripe.api_key = config.STRIPE_SECRET_KEY

        # Verify the payment method belongs to the user
        payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
        if payment_method.customer != user.stripe_customer_id:
            raise ValidationError("Payment method not found")

        # For card payment methods, use test charge
        test_charge = create_test_charge(
            payment_method_id=payment_method_id,
            customer_id=user.stripe_customer_id,
            amount_cents=50
        )

        return ResponseFactory.success(
            message="Payment method verification completed",
            data={
                "payment_method_id": payment_method_id,
                "verification_status": test_charge.get("status")
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to verify payment method")
