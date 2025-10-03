"""
Admin Internal Donation Batch Execution

Internal function for processing donation batches.
This is NOT an API endpoint - used only by scheduled tasks and retry mechanisms.
"""

from sqlalchemy.orm import Session
import logging
from datetime import datetime, timezone

from app.model.m_donation_batch import DonationBatch
from app.model.m_user import User
from app.services.stripe_service import create_payment_intent


def execute_donation_batch(batch_id, user_data: dict, db: Session):
    """
    Internal function to execute a donation batch by processing payment.
    This is NOT an API endpoint - used only by scheduled tasks and retry mechanisms.

    Args:
        batch_id: ID of the donation batch to process
        user_data: Dictionary containing user info (for compatibility)
        db: Database session

    Returns:
        dict: Success/failure status with details
    """
    batch = None
    try:
        # Get the batch
        batch = db.query(DonationBatch).filter_by(id=batch_id).first()
        if not batch:

            return {"success": False, "error": "Batch not found"}

        # Get user
        user = db.query(User).filter_by(id=batch.user_id).first()
        if not user or not user.stripe_customer_id:

            if batch:
                batch.status = "failed"
                batch.retry_attempts = getattr(batch, "retry_attempts", 0) + 1
                db.commit()
            return {"success": False, "error": "User not set up for payments"}

        # Skip if amount is too small
        if batch.total_amount < 1.0:

            batch.status = "failed"
            db.commit()
            return {"success": False, "error": "Amount too small"}

        # Create payment intent via Stripe
        payment_intent_data = create_payment_intent(
            amount=int(batch.total_amount * 100),  # Convert to cents
            currency="usd",
            customer_id=user.stripe_customer_id,
            metadata={
                "batch_id": str(batch_id),
                "user_id": str(batch.user_id),
                "church_id": str(batch.church_id) if batch.church_id else "default",
                "type": "donation_batch",
            },
        )

        # Update batch with success info
        batch.stripe_charge_id = payment_intent_data.get("id")
        batch.status = "success"
        batch.executed_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "success": True,
            "charge_id": payment_intent_data.get("id"),
            "amount": batch.total_amount,
        }

    except Exception as e:
        # Mark batch as failed and increment retry count
        if batch:
            batch.status = "failed"
            batch.retry_attempts = getattr(batch, "retry_attempts", 0) + 1
            batch.last_retry_at = datetime.now(timezone.utc)
            db.commit()

        return {"success": False, "error": str(e)}
