from fastapi import HTTPException, Request
import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import json

from app.core.responses import ResponseFactory
from app.utils.stripe_client import stripe
from stripe import Webhook


async def handle_stripe_webhook(request: Request, db: Session):
    """Handle Stripe webhook events"""
    try:
        # Get the raw body
        body = await request.body()

        # Get the signature from headers
        signature = request.headers.get("stripe-signature")
        if not signature:
            raise HTTPException(
                status_code=400, detail="Missing stripe-signature header"
            )

        # Verify the webhook signature
        try:
            construct_event = getattr(Webhook, "construct_event")
            event = construct_event(
                body,
                signature,
                "whsec_your_webhook_secret",  # Replace with actual webhook secret
            )
        except Exception as e:

            raise HTTPException(status_code=400, detail="Invalid signature")

        # Handle different event types
        event_type = event["type"]

        if event_type == "payment_intent.succeeded":
            return handle_payment_intent_succeeded(event, db)
        elif event_type == "payment_intent.payment_failed":
            return handle_payment_intent_failed(event, db)
        elif event_type == "charge.succeeded":
            return handle_charge_succeeded(event, db)
        elif event_type == "charge.failed":
            return handle_charge_failed(event, db)
        elif event_type == "transfer.created":
            return handle_transfer_created(event, db)
        elif event_type == "account.updated":
            return handle_account_updated(event, db)
        else:

            return ResponseFactory.success(message="Event received")

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Webhook processing failed")


def handle_payment_intent_succeeded(event, db: Session):
    """Handle payment intent succeeded event"""
    try:
        payment_intent = event["data"]["object"]

        # Update donation batch status
        # This would typically update a donation batch record

        return ResponseFactory.success(message="Payment intent succeeded")
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to process payment intent")


def handle_payment_intent_failed(event, db: Session):
    """Handle payment intent failed event"""
    try:
        payment_intent = event["data"]["object"]

        # Update donation batch status to failed
        # This would typically update a donation batch record

        return ResponseFactory.success(message="Payment intent failed")
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to process payment intent")


def handle_charge_succeeded(event, db: Session):
    """Handle charge succeeded event"""
    try:
        charge = event["data"]["object"]

        return ResponseFactory.success(message="Charge succeeded")
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to process charge")


def handle_charge_failed(event, db: Session):
    """Handle charge failed event"""
    try:
        charge = event["data"]["object"]

        return ResponseFactory.success(message="Charge failed")
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to process charge")


def handle_transfer_created(event, db: Session):
    """Handle transfer created event"""
    try:
        transfer = event["data"]["object"]

        return ResponseFactory.success(message="Transfer created")
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to process transfer")


def handle_account_updated(event, db: Session):
    """Handle account updated event"""
    try:
        account = event["data"]["object"]

        return ResponseFactory.success(message="Account updated")
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to process account update")


async def handle_plaid_webhook(request: Request, db: Session):
    """Handle Plaid webhook events with real-time processing"""
    try:
        # Get the raw body
        body = await request.body()
        data = json.loads(body)

        # Use the enhanced webhook service
        from app.services.plaid_webhook_service import plaid_webhook_service

        result = plaid_webhook_service.process_webhook(data)

        if result["status"] == "success":
            return ResponseFactory.success(
                message="Webhook processed successfully", data=result
            )
        elif result["status"] == "ignored":
            return ResponseFactory.success(message="Webhook ignored", data=result)
        else:

            raise HTTPException(status_code=500, detail="Webhook processing failed")

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Webhook processing failed")


def handle_transactions_webhook(data, db: Session):
    """Handle Plaid transactions webhook"""
    try:
        webhook_code = data.get("webhook_code")

        return ResponseFactory.success(message="Transactions webhook processed")
    except Exception as e:

        raise HTTPException(
            status_code=500, detail="Failed to process transactions webhook"
        )


def handle_item_webhook(data, db: Session):
    """Handle Plaid item webhook"""
    try:
        webhook_code = data.get("webhook_code")

        return ResponseFactory.success(message="Item webhook processed")
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to process item webhook")
