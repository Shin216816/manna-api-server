import stripe
import logging
import traceback
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime, timezone

from app.model.m_church import Church
from app.services.kyc_service import KYCService
from app.core.exceptions import StripeError


def handle_stripe_webhook(
    payload: Dict[str, Any], signature: str, db: Session
) -> Dict[str, Any]:
    """Handle Stripe webhook events"""
    try:
        # Verify webhook signature
        from app.config import config

        event = stripe.Webhook.construct_event(
            payload, signature, config.STRIPE_WEBHOOK_SECRET
        )

        event_type = event["type"]
        event_data = event["data"]["object"]

        # Handle different event types
        if event_type == "account.updated":
            return handle_account_updated(event_data, db)
        elif event_type == "account.application.authorized":
            return handle_account_authorized(event_data, db)
        elif event_type == "account.application.deauthorized":
            return handle_account_deauthorized(event_data, db)
        elif event_type == "payment_intent.succeeded":
            return handle_payment_intent_succeeded(event_data, db)
        elif event_type == "payment_intent.payment_failed":
            return handle_payment_intent_failed(event_data, db)
        elif event_type == "customer.subscription.created":
            return handle_subscription_created(event_data, db)
        elif event_type == "customer.subscription.updated":
            return handle_subscription_updated(event_data, db)
        elif event_type == "customer.subscription.deleted":
            return handle_subscription_deleted(event_data, db)
        else:

            return {"status": "ignored", "event_type": event_type}

    except ValueError as e:

        raise HTTPException(status_code=400, detail="Invalid payload")
    except Exception as e:
        if "Invalid signature" in str(e):

            raise HTTPException(status_code=400, detail="Invalid signature")
        else:

            raise HTTPException(status_code=500, detail="Webhook processing failed")


def handle_account_updated(account_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Handle account.updated webhook event"""
    try:
        stripe_account_id = account_data["id"]

        # Find church by Stripe account ID
        church = (
            db.query(Church)
            .filter(Church.stripe_account_id == stripe_account_id)
            .first()
        )
        if not church:

            return {
                "status": "church_not_found",
                "stripe_account_id": stripe_account_id,
            }

        # Sync account status
        status_data = KYCService.sync_stripe_account_status(church, db)

        return {
            "status": "success",
            "church_id": church.id,
            "kyc_state": status_data["kyc_state"],
            "charges_enabled": status_data["charges_enabled"],
            "payouts_enabled": status_data["payouts_enabled"],
        }

    except Exception as e:

        return {"status": "error", "error": str(e)}


def handle_account_authorized(
    account_data: Dict[str, Any], db: Session
) -> Dict[str, Any]:
    """Handle account.application.authorized webhook event"""
    try:
        stripe_account_id = account_data["id"]

        # Find church by Stripe account ID
        church = (
            db.query(Church)
            .filter(Church.stripe_account_id == stripe_account_id)
            .first()
        )
        if not church:

            return {
                "status": "church_not_found",
                "stripe_account_id": stripe_account_id,
            }

        # Log the authorization
        from app.model.m_audit_log import AuditLog

        audit_log = AuditLog(
            actor_type="webhook",
            church_id=church.id,
            action="ACCOUNT_AUTHORIZED",
            details_json={
                "stripe_account_id": stripe_account_id,
                "event_type": "account.application.authorized",
            },
        )
        db.add(audit_log)
        db.commit()

        return {
            "status": "success",
            "church_id": church.id,
            "stripe_account_id": stripe_account_id,
        }

    except Exception as e:

        return {"status": "error", "error": str(e)}


def handle_account_deauthorized(
    account_data: Dict[str, Any], db: Session
) -> Dict[str, Any]:
    """Handle account.application.deauthorized webhook event"""
    try:
        stripe_account_id = account_data["id"]

        # Find church by Stripe account ID
        church = (
            db.query(Church)
            .filter(Church.stripe_account_id == stripe_account_id)
            .first()
        )
        if not church:

            return {
                "status": "church_not_found",
                "stripe_account_id": stripe_account_id,
            }

        # Update church status
        church.kyc_state = "SUSPENDED"
        church.payouts_enabled = False
        church.disabled_reason = "Account deauthorized by Stripe"
        db.commit()

        # Log the deauthorization
        from app.model.m_audit_log import AuditLog

        audit_log = AuditLog(
            actor_type="webhook",
            church_id=church.id,
            action="ACCOUNT_DEAUTHORIZED",
            details_json={
                "stripe_account_id": stripe_account_id,
                "event_type": "account.application.deauthorized",
                "previous_state": "ACTIVE",
            },
        )
        db.add(audit_log)
        db.commit()

        return {
            "status": "success",
            "church_id": church.id,
            "stripe_account_id": stripe_account_id,
            "kyc_state": "SUSPENDED",
        }

    except Exception as e:

        return {"status": "error", "error": str(e)}


def handle_payment_intent_succeeded(
    payment_intent_data: Dict[str, Any], db: Session
) -> Dict[str, Any]:
    """Handle payment_intent.succeeded webhook event"""
    try:
        from app.model.m_roundup_new import DonorPayout
        from datetime import datetime, timezone

        # Create donor payout record using correct model
        donor_payout = DonorPayout(
            user_id=payment_intent_data["metadata"].get("user_id"),
            church_id=payment_intent_data["metadata"].get("church_id"),
            donation_amount=payment_intent_data["amount"]
            / 100.0,  # Convert cents to dollars
            stripe_payment_intent_id=payment_intent_data["id"],
            status="completed",
            processed_at=datetime.now(timezone.utc),
        )
        db.add(donor_payout)
        db.commit()

        return {"status": "success", "payment_id": payment_intent_data["id"]}

    except Exception as e:

        return {"status": "error", "error": str(e)}


def handle_payment_intent_failed(
    payment_intent_data: Dict[str, Any], db: Session
) -> Dict[str, Any]:
    """Handle payment_intent.payment_failed webhook event"""
    try:

        return {"status": "success", "payment_id": payment_intent_data["id"]}

    except Exception as e:

        return {"status": "error", "error": str(e)}


def handle_subscription_created(
    subscription_data: Dict[str, Any], db: Session
) -> Dict[str, Any]:
    """Handle customer.subscription.created webhook event"""
    try:

        return {"status": "success", "subscription_id": subscription_data["id"]}

    except Exception as e:

        return {"status": "error", "error": str(e)}


def handle_subscription_updated(
    subscription_data: Dict[str, Any], db: Session
) -> Dict[str, Any]:
    """Handle customer.subscription.updated webhook event"""
    try:

        return {"status": "success", "subscription_id": subscription_data["id"]}

    except Exception as e:

        return {"status": "error", "error": str(e)}


def handle_subscription_deleted(
    subscription_data: Dict[str, Any], db: Session
) -> Dict[str, Any]:
    """Handle customer.subscription.deleted webhook event"""
    try:

        return {"status": "success", "subscription_id": subscription_data["id"]}

    except Exception as e:

        return {"status": "error", "error": str(e)}
