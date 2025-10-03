from fastapi import HTTPException
import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from app.core.responses import ResponseFactory
import stripe
from stripe import PaymentIntent
from app.config import config

# Configure stripe
setattr(stripe, "api_key", config.STRIPE_SECRET_KEY)


def create_payment_intent(
    amount: int, currency: str = "usd", metadata: Optional[Dict[str, str]] = None
):
    """Create a Stripe payment intent"""
    try:
        # Validate input
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")

        payment_intent_data: Dict[str, Any] = {
            "amount": amount,
            "currency": currency,
        }

        if metadata:
            payment_intent_data["metadata"] = metadata

        payment_intent = PaymentIntent.create(**payment_intent_data)

        # Validate response
        if not payment_intent or not payment_intent.id:
            raise HTTPException(
                status_code=500, detail="Invalid response from Stripe API"
            )

        return ResponseFactory.success(
            message="Payment intent created successfully",
            data={
                "payment_intent_id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "amount": payment_intent.amount,
                "currency": payment_intent.currency,
                "status": payment_intent.status,
            },
        )
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to create payment intent")


def confirm_payment(payment_intent_id: str):
    """Confirm a Stripe payment intent"""
    try:
        payment_intent = PaymentIntent.retrieve(payment_intent_id)

        if payment_intent.status == "requires_confirmation":
            payment_intent = PaymentIntent.confirm(payment_intent_id)

        return ResponseFactory.success(
            message="Payment confirmed successfully",
            data={
                "payment_intent_id": payment_intent.id,
                "status": payment_intent.status,
                "amount": payment_intent.amount,
                "currency": payment_intent.currency,
            },
        )
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to confirm payment")


def get_payment_status(payment_intent_id: str):
    """Get the status of a Stripe payment intent"""
    try:
        payment_intent = PaymentIntent.retrieve(payment_intent_id)

        return ResponseFactory.success(
            message="Payment status retrieved successfully",
            data={
                "payment_intent_id": payment_intent.id,
                "status": payment_intent.status,
                "amount": payment_intent.amount,
                "currency": payment_intent.currency,
                "created": payment_intent.created,
                "last_payment_error": payment_intent.last_payment_error,
            },
        )
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to get payment status")
