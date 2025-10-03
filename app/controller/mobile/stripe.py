"""
Mobile Stripe Controller

Handles Stripe payment operations for mobile app:
- Payment intents
- Setup intents
- Payment methods
- Charges and refunds
- Customer management
"""

from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.services.stripe_service import (
    create_customer, get_customer, update_customer,
    create_payment_intent, confirm_payment_intent, get_payment_intent, cancel_payment_intent,
    create_setup_intent, attach_payment_method, detach_payment_method, list_payment_methods,
    update_payment_method, create_charge, transfer_to_church, create_connect_account,
    create_account_link, get_account, create_refund, get_balance, list_charges
)
from app.model.m_user import User
from app.model.m_church import Church
from app.schema.stripe_schema import (
    CustomerCreateRequest, CustomerUpdateRequest, PaymentIntentCreateRequest,
    PaymentIntentConfirmRequest, SetupIntentCreateRequest, PaymentMethodAttachRequest,
    PaymentMethodUpdateRequest, ChargeCreateRequest, ConnectAccountCreateRequest,
    AccountLinkCreateRequest, RefundCreateRequest, TransferCreateRequest
)
from app.core.responses import ResponseFactory
from typing import List, Dict, Any, Optional
import logging


def create_stripe_customer(user_id: int, customer_data: CustomerCreateRequest, db: Session):
    """Create a Stripe customer for a user"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create customer in Stripe
        stripe_customer = create_customer(
            email=customer_data.email,
            name=customer_data.name,
            phone=customer_data.phone
        )
        
        # Update user with Stripe customer ID
        user.stripe_customer_id = stripe_customer["id"]
        db.commit()
        
        return ResponseFactory.success(
            message="Stripe customer created successfully",
            data={
                "customer_id": stripe_customer["id"],
                "customer": stripe_customer
            }
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Customer creation failed: {str(e)}")


def get_stripe_customer(user_id: int, db: Session):
    """Get Stripe customer information for a user"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.stripe_customer_id:
            raise HTTPException(status_code=404, detail="Stripe customer not found")
        
        customer = get_customer(user.stripe_customer_id)
        
        return ResponseFactory.success(
            message="Stripe customer retrieved successfully",
            data={"customer": customer}
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Customer retrieval failed: {str(e)}")


def update_stripe_customer(user_id: int, update_data: CustomerUpdateRequest, db: Session):
    """Update Stripe customer information"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.stripe_customer_id:
            raise HTTPException(status_code=404, detail="Stripe customer not found")
        
        customer = update_customer(user.stripe_customer_id, **update_data.dict(exclude_unset=True))
        
        return ResponseFactory.success(
            message="Stripe customer updated successfully",
            data={"customer": customer}
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Customer update failed: {str(e)}")


def create_payment_intent_handler(user_id: int, payment_data: PaymentIntentCreateRequest, db: Session):
    """Create a Payment Intent for processing payments"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prepare metadata
        metadata = {
            "user_id": str(user_id),
        }
        if payment_data.donation_type:
            metadata["donation_type"] = payment_data.donation_type
        if payment_data.church_id:
            metadata["church_id"] = str(payment_data.church_id)
        
        # Create payment intent
        payment_intent = create_payment_intent(
            amount=payment_data.amount,
            currency=payment_data.currency,
            description=payment_data.description,
            metadata=metadata,
            customer_id=user.stripe_customer_id if user.stripe_customer_id else None
        )
        
        return ResponseFactory.success(
            message="Payment intent created successfully",
            data={"payment_intent": payment_intent}
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Payment intent creation failed: {str(e)}")


def confirm_payment_intent_handler(payment_data: PaymentIntentConfirmRequest):
    """Confirm a Payment Intent"""
    try:
        payment_intent = confirm_payment_intent(
            payment_intent_id=payment_data.payment_intent_id,
            payment_method_id=payment_data.payment_method_id
        )
        
        return ResponseFactory.success(
            message="Payment intent confirmed successfully",
            data={"payment_intent": payment_intent}
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Payment intent confirmation failed: {str(e)}")


def get_payment_intent_handler(payment_intent_id: str):
    """Get Payment Intent details"""
    try:
        payment_intent = get_payment_intent(payment_intent_id)
        
        return ResponseFactory.success(
            message="Payment intent retrieved successfully",
            data={"payment_intent": payment_intent}
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Payment intent retrieval failed: {str(e)}")


def cancel_payment_intent_handler(payment_intent_id: str):
    """Cancel a Payment Intent"""
    try:
        payment_intent = cancel_payment_intent(payment_intent_id)
        
        return ResponseFactory.success(
            message="Payment intent cancelled successfully",
            data={"payment_intent": payment_intent}
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Payment intent cancellation failed: {str(e)}")


def create_setup_intent_handler(user_id: int, setup_data: SetupIntentCreateRequest, db: Session):
    """Create a Setup Intent for saving payment methods"""
    try:
        logging.info(f"Creating setup intent for user_id: {user_id}")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logging.error(f"User not found for user_id: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        logging.info(f"User found: {user.email}, stripe_customer_id: {user.stripe_customer_id}")
        
        # Ensure user has a Stripe customer ID
        if not user.stripe_customer_id:
            logging.info(f"Creating Stripe customer for user: {user.email}")
            # Create a Stripe customer for the user
            stripe_customer = create_customer(
                email=user.email,
                name=f"{user.first_name} {user.last_name or ''}".strip(),
                phone=user.phone
            )
            
            logging.info(f"Stripe customer created: {stripe_customer.get('id')}")
            # Update user with Stripe customer ID
            user.stripe_customer_id = stripe_customer["id"]
            db.commit()
            
            
        
        # Create setup intent with the customer ID
        
        
        
        logging.info(f"Creating setup intent with customer_id: {user.stripe_customer_id}")
        setup_intent = create_setup_intent(
            customer_id=user.stripe_customer_id,
            payment_method_types=setup_data.payment_method_types,
            usage=setup_data.usage
        )      
        
        # Log the setup intent for debugging
        logging.info(f"Created setup intent: {setup_intent}")
        logging.info(f"Setup intent client_secret: {setup_intent.get('client_secret', 'NOT_FOUND')}")
        
        return ResponseFactory.success(
            message="Setup intent created successfully",
            data={
                "client_secret": setup_intent.get("client_secret"),
                "id": setup_intent.get("id"),
                "status": setup_intent.get("status"),
                "payment_method_types": setup_intent.get("payment_method_types"),
                "usage": setup_intent.get("usage")
            }
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Setup intent creation failed: {str(e)}")


def get_setup_intent_handler(setup_intent_id: str, user_id: int, db: Session):
    """Get Setup Intent details"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get setup intent from Stripe
        from app.services.stripe_service import get_setup_intent as stripe_get_setup_intent
        stripe_setup_intent = stripe_get_setup_intent(setup_intent_id)
        
        return ResponseFactory.success(
            message="Setup intent retrieved successfully",
            data={
                "setup_intent": stripe_setup_intent
            }
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Setup intent retrieval failed: {str(e)}")


def attach_payment_method_handler(user_id: int, attach_data: PaymentMethodAttachRequest, db: Session):
    """Attach a payment method to the authenticated user's Stripe customer"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.stripe_customer_id:
            raise HTTPException(status_code=404, detail="Stripe customer not found")
        
        payment_method = attach_payment_method(
            payment_method_id=attach_data.payment_method_id,
            customer_id=user.stripe_customer_id
        )
        
        return ResponseFactory.success(
            message="Payment method attached successfully",
            data={"payment_method": payment_method}
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Payment method attachment failed: {str(e)}")


def detach_payment_method_handler(payment_method_id: str):
    """Detach a payment method from the authenticated user's Stripe customer"""
    try:
        payment_method = detach_payment_method(payment_method_id)
        
        return ResponseFactory.success(
            message="Payment method detached successfully",
            data={"payment_method": payment_method}
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Payment method detachment failed: {str(e)}")


def list_payment_methods_handler(user_id: int, db: Session, type: str = "card", limit: int = 100):
    """List payment methods for the authenticated user's Stripe customer"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.stripe_customer_id:
            return ResponseFactory.success(
                message="No payment methods found",
                data={"payment_methods": []}
            )
        
        payment_methods = list_payment_methods(
            customer_id=user.stripe_customer_id,
            type=type,
            limit=limit
        )
        
        return ResponseFactory.success(
            message="Payment methods retrieved successfully",
            data={"payment_methods": payment_methods}
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Payment methods listing failed: {str(e)}")


def update_payment_method_handler(payment_method_id: str, update_data: PaymentMethodUpdateRequest):
    """Update a payment method's billing details or metadata"""
    try:
        payment_method = update_payment_method(
            payment_method_id=payment_method_id,
            billing_details=update_data.billing_details
        )
        
        return ResponseFactory.success(
            message="Payment method updated successfully",
            data={"payment_method": payment_method}
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Payment method update failed: {str(e)}")


def create_charge_handler(user_id: int, charge_data: ChargeCreateRequest, db: Session):
    """Create a charge for the authenticated user"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create charge
        charge = create_charge(
            amount=charge_data.amount,
            currency=charge_data.currency,
            description=charge_data.description,
            customer_id=user.stripe_customer_id if user.stripe_customer_id else None
        )
        
        return ResponseFactory.success(
            message="Charge created successfully",
            data={"charge": charge}
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Charge creation failed: {str(e)}")


def create_connect_account_handler(user_id: int, account_data: ConnectAccountCreateRequest, db: Session):
    """Create a Stripe Connect account for a church"""
    try:
        # Note: This should be restricted to church admins
        # For now, we'll create the account without church association
        account = create_connect_account(
            type=account_data.type,
            country=account_data.country,
            email=account_data.email,
            business_type=account_data.business_type
        )
        
        return ResponseFactory.success(
            message="Connect account created successfully",
            data={"account": account}
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Connect account creation failed: {str(e)}")


def create_account_link_handler(church_id: int, link_data: AccountLinkCreateRequest, current_user: dict, db: Session):
    """Create an account link for Stripe Connect onboarding"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church or not church.stripe_account_id:
            raise HTTPException(status_code=404, detail="Church or Stripe account not found")
        
        account_link = create_account_link(
            account_id=church.stripe_account_id,
            refresh_url=link_data.refresh_url,
            return_url=link_data.return_url,
            type=link_data.type
        )
        
        return ResponseFactory.success(
            message="Account link created successfully",
            data={"account_link": account_link}
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Account link creation failed: {str(e)}")


def get_connect_account_handler(church_id: int, current_user: dict, db: Session):
    """Get Stripe Connect account information for a church"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church or not church.stripe_account_id:
            raise HTTPException(status_code=404, detail="Church or Stripe account not found")
        
        account = get_account(church.stripe_account_id)
        
        return ResponseFactory.success(
            message="Connect account retrieved successfully",
            data={"account": account}
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Connect account retrieval failed: {str(e)}")


def create_refund_handler(refund_data: RefundCreateRequest):
    """Create a refund for a charge"""
    try:
        refund = create_refund(
            charge_id=refund_data.charge_id,
            amount=refund_data.amount,
            reason=refund_data.reason
        )
        
        return ResponseFactory.success(
            message="Refund created successfully",
            data={"refund": refund}
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Refund creation failed: {str(e)}")


def get_balance_handler():
    """Get Stripe account balance"""
    try:
        balance = get_balance()
        
        return ResponseFactory.success(
            message="Balance retrieved successfully",
            data={"balance": balance}
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Balance retrieval failed: {str(e)}")


def list_charges_handler(user_id: Optional[int] = None, db: Optional[Session] = None, limit: int = 100):
    """List charges for the authenticated user"""
    try:
        charges = list_charges(limit=limit)
        
        return ResponseFactory.success(
            message="Charges retrieved successfully",
            data={"charges": charges}
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Charges listing failed: {str(e)}")


def transfer_to_church_handler(user_id: int, transfer_data: TransferCreateRequest, db: Session):
    """Transfer funds to a church's Stripe Connect account"""
    try:
        # Get the church's Stripe account ID
        church = db.query(Church).filter(Church.id == transfer_data.church_id).first()
        if not church or not church.stripe_account_id:
            raise HTTPException(status_code=404, detail="Church or Stripe account not found")
        
        transfer = transfer_to_church(
            amount_cents=transfer_data.amount_cents,
            destination_account_id=church.stripe_account_id,
            metadata=transfer_data.metadata or {}
        )
        
        return ResponseFactory.success(
            message="Transfer created successfully",
            data={"transfer": transfer}
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Transfer creation failed: {str(e)}")


def get_stripe_config():
    """Get Stripe configuration for mobile app"""
    try:
        from app.config import config
        return ResponseFactory.success(
            message="Stripe configuration retrieved",
            data={
                "publishable_key": config.STRIPE_PUBLIC_KEY,
                "api_version": "2023-10-16"
            }
        )
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to get Stripe configuration")
