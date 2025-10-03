"""
Referral Commission Payout Scheduler

Automatically processes referral commission payouts based on configured schedules.
Handles commission calculations and Stripe transfers for referring churches.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timezone, timedelta
import logging

from app.model.m_church_referral import ChurchReferral
from app.model.m_church import Church
from app.model.m_donation_batch import DonationBatch
from app.services.stripe_service import transfer_to_church

# Using database notification system instead of Firebase
from app.utils.database import SessionLocal
from app.utils.audit import create_audit_log
from app.core.constants import get_business_constant


def process_referral_commissions():
    """
    Process referral commissions automatically.
    Calculates commissions from donations and processes payouts.
    """
    db = SessionLocal()
    try:

        # Get commission processing settings
        min_commission_amount = float(
            get_business_constant("MIN_COMMISSION_PAYOUT", 5.0) or 5.0
        )
        commission_hold_days = int(
            get_business_constant("COMMISSION_HOLD_DAYS", 30) or 30
        )

        # Get cutoff date for commission processing
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=commission_hold_days)

        # Get all unpaid referrals with sufficient commission amounts
        unpaid_referrals = (
            db.query(ChurchReferral)
            .filter(
                and_(
                    ChurchReferral.commission_paid == False,
                    ChurchReferral.total_commission_earned >= min_commission_amount,
                    ChurchReferral.created_at <= cutoff_date,
                )
            )
            .all()
        )

        processed_count = 0
        failed_count = 0

        for referral in unpaid_referrals:
            try:
                success = process_single_referral_commission(referral, db)
                if success:
                    processed_count += 1
                else:
                    failed_count += 1
            except Exception as e:

                failed_count += 1
                continue

    except Exception as e:
        pass
    finally:
        db.close()


def process_single_referral_commission(referral: ChurchReferral, db: Session) -> bool:
    """Process commission payout for a single referral"""
    try:
        # Get referring church
        referring_church = (
            db.query(Church).filter_by(id=referral.referring_church_id).first()
        )
        if not referring_church:

            return False

        # Check if church has Stripe account
        if not referring_church.stripe_account_id:

            return False

        # Calculate commission amount
        commission_amount = float(referral.total_commission_earned or 0)
        if commission_amount <= 0:

            return False

        # Process Stripe transfer
        try:
            transfer = transfer_to_church(
                amount_cents=int(commission_amount * 100),  # Convert to cents
                destination_account_id=referring_church.stripe_account_id,
                metadata={
                    "referral_id": referral.id,
                    "type": "commission",
                    "referrer_church_id": referring_church.id,
                    "referred_church_id": referral.referred_church_id,
                    "processed_automatically": True,
                },
            )

            # Update referral record
            referral.commission_paid = True
            referral.payout_date = datetime.now(timezone.utc)
            referral.payout_status = "completed"
            referral.stripe_transfer_id = transfer.id
            referral.payout_amount = commission_amount
            db.commit()

            # Send database notification to church admin about commission payout
            from app.model.m_church_message import (
                ChurchMessage,
                MessageType,
                MessagePriority,
            )
            from app.model.m_church_admin import ChurchAdmin

            # Create church message for commission payout notification
            commission_message = ChurchMessage(
                church_id=referral.referring_church_id,
                title="Referral Commission Received",
                content=f"You've received a referral commission of ${commission_amount:.2f} for referring {referral.referred_church.name}. The commission has been transferred to your account.",
                type=MessageType.ANNOUNCEMENT,
                priority=MessagePriority.MEDIUM,
                is_active=True,
                is_published=True,
                published_at=datetime.now(timezone.utc),
            )
            db.add(commission_message)
            db.flush()  # Get the message ID

            # Send to all church admins
            church_admins = (
                db.query(ChurchAdmin)
                .filter(
                    ChurchAdmin.church_id == referral.referring_church_id,
                    ChurchAdmin.is_active == True,
                )
                .all()
            )

            for admin in church_admins:
                user_message = UserMessage(
                    user_id=admin.user_id,
                    message_id=commission_message.id,
                    is_read=False,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(user_message)

            # Create audit log
            create_audit_log(
                db=db,
                actor_type="system",
                actor_id=0,
                action="automated_referral_payout",
                metadata={
                    "resource_type": "referral",
                    "resource_id": referral.id,
                    "referral_id": referral.id,
                    "transfer_id": transfer.id,
                    "amount": commission_amount,
                    "church_id": referring_church.id,
                    "church_name": referring_church.name,
                },
            )

            return True

        except Exception as transfer_error:

            db.rollback()
            return False

    except Exception as e:

        db.rollback()
        return False


def calculate_pending_commissions():
    """
    Calculate pending commissions from recent donations.
    This should be called after donation batches are processed.
    """
    db = SessionLocal()
    try:

        # Get pending commissions from church_referrals table
        pending_commissions = (
            db.query(ChurchReferral)
            .filter(
                ChurchReferral.commission_paid == False,
                ChurchReferral.total_commission_earned > 0,
            )
            .all()
        )

        for commission in pending_commissions:
            try:
                # Check if this church was referred by another church
                referral = (
                    db.query(ChurchReferral)
                    .filter_by(referred_church_id=donation.church_id)
                    .first()
                )

                if referral:
                    # Calculate commission
                    commission_amount = float(donation.total_amount) * commission_rate

                    # Update referral record
                    referral.commission_amount = (
                        referral.commission_amount or 0
                    ) + commission_amount
                    referral.total_donations = (referral.total_donations or 0) + float(
                        donation.total_amount
                    )
                    referral.last_donation_date = datetime.now(timezone.utc)

                    # Mark donation as commission processed
                    donation.commission_processed = True

            except Exception as e:

                continue

        db.commit()

    except Exception as e:

        db.rollback()
    finally:
        db.close()


def retry_failed_commission_payouts():
    """
    Retry failed commission payouts.
    """
    db = SessionLocal()
    try:

        # Get failed payouts (you might need to add a status field to track this)
        failed_referrals = (
            db.query(ChurchReferral)
            .filter(
                and_(
                    ChurchReferral.commission_paid == False,
                    ChurchReferral.payout_attempts < 3,  # Assuming this field exists
                )
            )
            .all()
        )

        retry_count = 0
        for referral in failed_referrals:
            try:
                success = process_single_referral_commission(referral, db)
                if success:
                    retry_count += 1
            except Exception as e:

                continue

    except Exception as e:
        pass
    finally:
        db.close()
