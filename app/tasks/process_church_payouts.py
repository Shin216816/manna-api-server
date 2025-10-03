"""
Church Payout Processing Task

Processes automatic payouts of donations to churches using the CORRECT workflow:
1. Calculate church earnings from donor_payouts (minus system fees)
2. Execute Stripe transfer to church
3. If transfer succeeds, create ChurchPayout record with stripe_transfer_id
4. Mark donor_payouts as allocated

This ensures churches receive their donations in a timely manner with proper workflow order.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timezone, timedelta
import logging

from app.model.m_roundup_new import DonorPayout, ChurchPayout
from app.model.m_church import Church
from app.services.church_payout_service import ChurchPayoutService
from app.utils.database import SessionLocal
from app.core.constants import get_business_constant


def create_monthly_church_payouts():
    """
    Create monthly payouts for all churches based on calendar months.
    This ensures churches receive payouts on a predictable monthly schedule.
    """
    db = SessionLocal()
    try:

        # Get current month boundaries
        now = datetime.now(timezone.utc)
        current_month_start = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        # Check if we've already created payouts for this month
        existing_payouts = (
            db.query(Payout)
            .filter(
                and_(
                    Payout.period_start >= current_month_start,
                    Payout.period_start < current_month_start + timedelta(days=32),
                )
            )
            .all()
        )

        if existing_payouts:
            return

        # Get all active churches
        churches = (
            db.query(Church)
            .filter(
                and_(
                    Church.status == "active",
                    Church.kyc_status == "verified",
                    Church.stripe_account_id.isnot(None),
                )
            )
            .all()
        )

        for church in churches:
            try:
                create_monthly_payout_for_church(church, current_month_start, db)
            except Exception as e:

                continue

    except Exception as e:
        pass
    finally:
        db.close()


def create_monthly_payout_for_church(
    church: Church, month_start: datetime, db: Session
):
    """Create a monthly payout for a specific church"""
    try:
        # Calculate month boundaries
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(
            days=1
        )

        # Get all successful donations for this month
        # TransactionType and TransactionStatus enums removed - using DonationBatch status instead

        monthly_donations = (
            db.query(DonorPayout)
            .filter(
                and_(
                    DonorPayout.church_id == church.id,
                    DonorPayout.status == "completed",
                    DonorPayout.processed_at >= month_start,
                    DonorPayout.processed_at <= month_end,
                )
            )
            .all()
        )

        if not monthly_donations:
            return

        # Calculate total amount for the month
        total_amount = sum(
            float(donation.donation_amount) for donation in monthly_donations
        )

        # Skip if amount is too small (minimum $1.00)
        if total_amount < 1.00:

            return

        # Check if payout already exists for this month using ChurchPayout
        existing_payout = (
            db.query(ChurchPayout)
            .filter(
                and_(
                    ChurchPayout.church_id == church.id,
                    ChurchPayout.period_start == month_start.strftime("%Y-%m-%d"),
                    ChurchPayout.period_end == month_end.strftime("%Y-%m-%d"),
                )
            )
            .first()
        )

        if existing_payout:
            return

        # Use ChurchPayoutService to process the payout properly
        try:
            result = ChurchPayoutService.process_church_payout(db, church.id)
            if result["success"]:
                pass
            else:
                pass

        except Exception as e:

            raise e

    except Exception as e:

        db.rollback()
        raise e


def process_pending_church_payouts():
    """
    Process pending church payouts using the CORRECT workflow:
    1. Find donor payouts that have passed hold period and are unallocated
    2. Group by church and process payouts using ChurchPayoutService
    """
    db = SessionLocal()
    try:

        # Get payout hold period from config (default 7 days)
        hold_period_days = int(get_business_constant("PAYOUT_HOLD_PERIOD_DAYS", 7) or 7)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=hold_period_days)

        # Get donor payouts that are ready for church payout
        ready_donor_payouts = (
            db.query(DonorPayout)
            .filter(
                and_(
                    DonorPayout.status == "completed",  # Successfully processed
                    DonorPayout.allocated_at.is_(
                        None
                    ),  # Not yet allocated to church payout
                    DonorPayout.processed_at <= cutoff_date,  # Past hold period
                )
            )
            .all()
        )

        if not ready_donor_payouts:

            return

        # Group by church
        churches_with_ready_payouts = {}
        for dp in ready_donor_payouts:
            if dp.church_id not in churches_with_ready_payouts:
                churches_with_ready_payouts[dp.church_id] = []
            churches_with_ready_payouts[dp.church_id].append(dp)

        # Process each church using the correct service
        for church_id, payouts in churches_with_ready_payouts.items():
            try:
                result = ChurchPayoutService.process_church_payout(db, church_id)
                if result["success"]:
                    pass
                else:
                    pass

            except Exception as e:

                continue

    except Exception as e:
        pass
    finally:
        db.close()


def process_single_payout(payout: ChurchPayout, db: Session):
    """Process a single pending payout"""
    try:
        # Get church details
        church = db.query(Church).filter_by(id=payout.church_id).first()
        if not church:

            return

        # Check if church has Stripe Connect account
        if not church.stripe_account_id:
            return

        # Skip if amount is too small (minimum $1.00)
        if float(str(payout.amount)) < 1.00:

            payout.status = "cancelled"
            payout.failure_reason = "Amount too small for payout"
            db.commit()
            return

        # Update payout status to processing
        payout.status = "processing"
        db.commit()

        # Process Stripe transfer
        try:
            transfer = transfer_to_church(
                amount_cents=int(float(str(payout.amount)) * 100),  # Convert to cents
                destination_account_id=church.stripe_account_id,
                metadata={
                    "payout_id": str(payout.id),
                    "church_id": str(payout.church_id),
                    "church_name": church.name,
                    "payout_type": (
                        "monthly"
                        if "monthly_payout" in (payout.payout_metadata or "")
                        else "batch"
                    ),
                    "period_start": (
                        payout.period_start.isoformat() if payout.period_start else None
                    ),
                    "period_end": (
                        payout.period_end.isoformat() if payout.period_end else None
                    ),
                    "flow_type": "platform_first",
                },
            )

            # Update payout with transfer details
            payout.stripe_transfer_id = transfer.id
            payout.stripe_account_id = church.stripe_account_id
            payout.status = "completed"
            payout.processed_at = datetime.now(timezone.utc)

            db.commit()

        except Exception as transfer_error:
            # Mark payout as failed
            payout.status = "failed"
            payout.failed_at = datetime.now(timezone.utc)
            payout.failure_reason = str(transfer_error)
            db.commit()

            raise transfer_error

    except Exception as e:

        db.rollback()
        raise e


def retry_failed_payouts():
    """Retry failed payouts that might have had temporary issues"""
    db = SessionLocal()
    try:

        # Get failed payouts from the last 24 hours
        retry_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        failed_payouts = (
            db.query(Payout)
            .filter(and_(Payout.status == "failed", Payout.failed_at >= retry_cutoff))
            .all()
        )

        for payout in failed_payouts:
            try:
                retry_payout(payout, db)
            except Exception as e:

                continue

    except Exception as e:
        pass
    finally:
        db.close()


def retry_payout(payout: ChurchPayout, db: Session):
    """Retry a specific failed payout"""
    try:
        church = db.query(Church).filter_by(id=payout.church_id).first()
        if not church or not church.stripe_account_id:

            return

        # Reset payout status
        payout.status = "processing"
        payout.failed_at = None
        setattr(payout, "failure_reason", None)

        # Retry the transfer
        transfer = transfer_to_church(
            amount_cents=int(float(str(payout.amount)) * 100),
            destination_account_id=church.stripe_account_id,
            metadata={
                "payout_id": str(payout.id),
                "church_id": str(payout.church_id),
                "retry": "true",
            },
        )

        # Update payout with success
        setattr(payout, "stripe_transfer_id", transfer.id)
        setattr(payout, "status", "completed")
        setattr(payout, "processed_at", datetime.now(timezone.utc))

        db.commit()

    except Exception as e:
        # Mark as failed again
        setattr(payout, "status", "failed")
        setattr(payout, "failed_at", datetime.now(timezone.utc))
        setattr(payout, "failure_reason", f"Retry failed: {str(e)}")
        db.commit()

        raise e
