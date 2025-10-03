from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.middleware.auth_middleware import get_current_user
import stripe
import logging
from app.controller.donor.payment_methods import (
    add_card_payment_method,
    get_payment_methods_enhanced,
    set_default_payment_method_enhanced,
    remove_payment_method_enhanced,
    verify_payment_method_enhanced,
    save_completed_payment_method,
)
from app.controller.mobile.stripe import get_stripe_config, create_setup_intent_handler, get_setup_intent_handler
from app.controller.donor.donations import (
    process_roundup_donation_enhanced,
    confirm_donation_payment,
    get_donation_status,
    get_donation_history_enhanced,
    refund_donation,
    get_donation_summary,
)

router = APIRouter()


@router.get("/test")
def test_route():
    """Test route to verify router is working"""
    return {"message": "Enhanced payments router is working", "status": "success"}


@router.get("/test-auth")
def test_auth_route(current_user: dict = Depends(get_current_user)):
    """Test route that requires authentication"""
    return {"message": "Authenticated route working", "user_id": current_user.get("id")}

@router.get("/stripe/config")
def get_stripe_config_route():
    """Get Stripe configuration for donor payments"""
    return get_stripe_config()

@router.post("/setup-intents/create")
def create_setup_intent_route(
    data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a setup intent for saving payment methods"""
    from app.schema.stripe_schema import SetupIntentCreateRequest
    
    # Convert dict to schema
    setup_data = SetupIntentCreateRequest(
        payment_method_types=data.get("payment_method_types", ["card"]),
        usage=data.get("usage", "off_session")
    )
    
    return create_setup_intent_handler(current_user["user_id"], setup_data, db)

@router.get("/setup-intents/{setup_intent_id}")
def get_setup_intent_route(
    setup_intent_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get setup intent status"""
    return get_setup_intent_handler(setup_intent_id, current_user["user_id"], db)


# Payment Methods Routes
@router.post("/payment-methods/card/add")
def add_card_payment_method_route(
    data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a new card payment method for a donor"""
    return add_card_payment_method(current_user, data, db)


# REMOVED: ACH and Financial Connections routes - using Stripe API directly
# These functions were removed from payment_methods controller as we now use Stripe API directly
# for all payment method management instead of storing them locally in the database


@router.post("/setup-intents/{setup_intent_id}/save-payment-method")
def save_completed_payment_method_route(
    setup_intent_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save a completed payment method from a setup intent"""
    return save_completed_payment_method(current_user, setup_intent_id, db)


# REMOVED: This endpoint was causing SPA redirect issues
# For SPAs, use client-side Stripe Elements integration instead
# No redirects needed - frontend handles everything




# REMOVED: Digital wallet payment method route - using Stripe API directly


@router.get("/payment-methods/list")
def get_payment_methods_enhanced_route(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get all payment methods for a donor with enhanced details"""
    return get_payment_methods_enhanced(current_user, db)


@router.post("/payment-methods/set-default")
def set_default_payment_method_enhanced_route(
    data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Set a payment method as default"""
    return set_default_payment_method_enhanced(current_user, data, db)


@router.post("/payment-methods/remove")
def remove_payment_method_enhanced_route(
    data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a payment method"""
    return remove_payment_method_enhanced(current_user, data, db)


@router.post("/payment-methods/verify")
def verify_payment_method_enhanced_route(
    data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify a payment method with a small test charge"""
    return verify_payment_method_enhanced(current_user, data, db)


# REMOVED: Payment method requirements route - using Stripe API directly


# Donation Routes
@router.post("/donations/roundup")
def process_roundup_donation_enhanced_route(
    data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Process a roundup donation with enhanced payment processing"""
    return process_roundup_donation_enhanced(current_user, data, db)


@router.post("/donations/confirm")
def confirm_donation_payment_route(
    data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Confirm a donation payment intent"""
    return confirm_donation_payment(current_user, data, db)


@router.post("/donations/status")
def get_donation_status_route(
    data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the status of a donation payment"""
    return get_donation_status(current_user, data, db)


@router.get("/donations/history")
def get_donation_history_enhanced_route(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get enhanced donation history for a donor"""
    return get_donation_history_enhanced(current_user, db, limit, offset)


@router.post("/donations/refund")
def refund_donation_route(
    data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Refund a donation"""
    return refund_donation(current_user, data, db)


@router.get("/donations/summary")
def get_donation_summary_route(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get donation summary for a donor"""
    return get_donation_summary(current_user, db)


@router.post("/webhooks/stripe")
async def stripe_webhook_route(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhooks for payment processing and Connect events"""
    try:
        # Get the raw body for signature verification
        body = await request.body()
        signature = request.headers.get("stripe-signature")

        if not signature:
            raise HTTPException(
                status_code=400, detail="Missing stripe-signature header"
            )

        # Verify webhook signature
        from app.config import config

        try:
            event = stripe.Webhook.construct_event(
                body, signature, config.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Handle the event
        if event.type == "payment_intent.succeeded":
            payment_intent = event.data.object
            # Handle successful payment - funds are captured but may not be available yet

            # For ACH payments, funds may not be available immediately
            if (
                payment_intent.payment_method_types
                and "us_bank_account" in payment_intent.payment_method_types
            ):
                pass

        elif event.type == "payment_intent.processing":
            payment_intent = event.data.object

        elif event.type == "payment_intent.payment_failed":
            payment_intent = event.data.object
            # Handle failed payment

        elif event.type == "charge.dispute.created":
            dispute = event.data.object
            # Handle dispute creation (ACH returns)

        elif event.type == "transfer.created":
            transfer = event.data.object
            # Handle transfer creation to connected account

        elif event.type == "transfer.paid":
            transfer = event.data.object
            # Handle successful transfer to connected account

        elif event.type == "transfer.failed":
            transfer = event.data.object
            # Handle failed transfer

        elif event.type == "account.updated":
            account = event.data.object
            # Handle connected account updates

        elif event.type == "payout.paid":
            payout = event.data.object
            # Handle successful payout from connected account to external bank

        elif event.type == "payout.failed":
            payout = event.data.object
            # Handle failed payout

        else:
            pass

        return {"status": "success"}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Webhook processing failed")
