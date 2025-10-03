import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
from sqlalchemy import func

from app.model.m_user import User
from app.model.m_donation_batch import DonationBatch
from app.model.m_church import Church
# PaymentMethod model removed - using Stripe API directly
from app.model.m_roundup_new import DonorPayout
from app.model.m_donation_preference import DonationPreference
from app.services.stripe_service import (
    create_donation_payment_intent,
    create_ach_donation_payment_intent,
    confirm_payment_intent,
    get_payment_intent,
    refund_payment,
    list_customer_payment_methods
)
from app.core.responses import ResponseFactory
from app.core.exceptions import UserNotFoundError, ValidationError
from app.utils.error_handler import handle_controller_errors
from fastapi import HTTPException
import stripe
from app.config import config

def get_user_payment_method(user, payment_method_id=None):
    """Get user's payment method from Stripe API"""
    if not user.stripe_customer_id:
        return None
    
    try:
        # Set Stripe API key
        stripe.api_key = config.STRIPE_SECRET_KEY
        
        if payment_method_id:
            # Get specific payment method
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
            if payment_method.customer != user.stripe_customer_id:
                return None
            return payment_method
        else:
            # Get default payment method
            if user.stripe_default_payment_method_id:
                return stripe.PaymentMethod.retrieve(user.stripe_default_payment_method_id)
            
            # If no default, get the first available payment method
            payment_methods = stripe.PaymentMethod.list(
                customer=user.stripe_customer_id,
                type='card'
            )
            if payment_methods.data:
                return payment_methods.data[0]
            
            return None
    except stripe.error.StripeError:
        return None

@handle_controller_errors
def process_roundup_donation_enhanced(
    current_user: dict,
    data: Dict[str, Any],
    db: Session
):
    """Process a roundup donation with enhanced payment processing"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        amount_cents = data.get("amount_cents")
        roundup_period_key = data.get("roundup_period_key")
        roundup_multiplier = data.get("roundup_multiplier", 1.0)
        transaction_count = data.get("transaction_count", 0)
        payment_method_id = data.get("payment_method_id")
        
        if not amount_cents or amount_cents <= 0:
            raise ValidationError("Valid amount is required")
        
        if not roundup_period_key:
            raise ValidationError("Roundup period key is required")

        if not user.stripe_customer_id:
            raise ValidationError("Stripe customer not found")

        # Get payment method from Stripe
        payment_method = get_user_payment_method(user, payment_method_id)
        
        if not payment_method:
            raise ValidationError("No payment method found")

        # Get user's primary church ID
        primary_church = user.get_primary_church(db)
        if not primary_church:
            raise ValidationError("User not associated with any church")
        
        church_id = primary_church.id
        church = primary_church

        metadata = {
            "user_id": str(user.id),
            "church_id": str(church_id),
            "roundup_period": roundup_period_key,
            "roundup_multiplier": str(roundup_multiplier),
            "transaction_count": str(transaction_count),
            "purpose": "roundup_donation",
            "donation_type": "roundup"
        }

        if payment_method.type == "ach":
            payment_intent = create_ach_donation_payment_intent(
                amount_cents=amount_cents,
                customer_id=user.stripe_customer_id,
                payment_method_id=payment_method.id,
                donation_type="roundup",
                metadata=metadata,
                description=f"Roundup donation - {roundup_multiplier}x multiplier for {church.name}"
            )
        else:
            payment_intent = create_donation_payment_intent(
                amount_cents=amount_cents,
                customer_id=user.stripe_customer_id,
                payment_method_id=payment_method.id,
                donation_type="roundup",
                metadata=metadata,
                description=f"Roundup donation - {roundup_multiplier}x multiplier for {church.name}"
            )

        # Create donation batch for tracking
        donation_batch = DonationBatch(
            user_id=user.id,
            church_id=church_id,
            batch_number=f"roundup_{roundup_period_key}_{int(datetime.utcnow().timestamp())}",
            amount=amount_cents / 100.0,  # Convert cents to dollars
            transaction_count=transaction_count,
            status="processing",
            collection_date=datetime.utcnow(),
            processing_fee=0.0,  # Will be calculated later
            net_amount=amount_cents / 100.0,  # Will be updated after processing
            stripe_transfer_id=payment_intent.get("id")
        )

        db.add(donation_batch)
        db.commit()

        return ResponseFactory.success(
            message="Roundup donation initiated successfully",
            data={
                "donation_batch_id": donation_batch.id,
                "payment_intent_id": payment_intent.get("id"),
                "amount_cents": amount_cents,
                "status": payment_intent.get("status"),
                "client_secret": payment_intent.get("client_secret")
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to process roundup donation")

@handle_controller_errors
def confirm_donation_payment(
    current_user: dict,
    data: Dict[str, Any],
    db: Session
):
    """Confirm a donation payment intent"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        payment_intent_id = data.get("payment_intent_id")
        if not payment_intent_id:
            raise ValidationError("Payment intent ID is required")

        # Find donation batch by payment intent ID
        donation_batch = db.query(DonationBatch).filter(
            DonationBatch.stripe_transfer_id == payment_intent_id,
            DonationBatch.user_id == user.id
        ).first()

        if not donation_batch:
            raise ValidationError("Donation batch not found")

        payment_intent = confirm_payment_intent(payment_intent_id)

        if payment_intent.get("status") == "succeeded":
            donation_batch.status = "completed"
            donation_batch.payout_date = datetime.utcnow()
            # Update with actual processing fee if available
            if payment_intent.get("charges", {}).get("data"):
                charge = payment_intent["charges"]["data"][0]
                if charge.get("balance_transaction"):
                    # Fetch balance transaction to get actual fees
                    from app.services.stripe_service import get_balance_transaction
                    balance_transaction = get_balance_transaction(charge["balance_transaction"])
                    if balance_transaction:
                        processing_fee = balance_transaction.get("fee", 0) / 100.0
                        donation_batch.processing_fee = processing_fee
                        donation_batch.net_amount = donation_batch.amount - processing_fee
        elif payment_intent.get("status") == "failed":
            donation_batch.status = "failed"

        db.commit()

        return ResponseFactory.success(
            message="Payment confirmation completed",
            data={
                "donation_batch_id": donation_batch.id,
                "status": donation_batch.status,
                "payment_intent_status": payment_intent.get("status")
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to confirm donation payment")

@handle_controller_errors
def get_donation_status(
    current_user: dict,
    data: Dict[str, Any],
    db: Session
):
    """Get the status of a donation payment"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        payment_intent_id = data.get("payment_intent_id")
        if not payment_intent_id:
            raise ValidationError("Payment intent ID is required")

        # Find donation batch by payment intent ID
        donation_batch = db.query(DonationBatch).filter(
            DonationBatch.stripe_transfer_id == payment_intent_id,
            DonationBatch.user_id == user.id
        ).first()

        if not donation_batch:
            raise ValidationError("Donation batch not found")

        payment_intent = get_payment_intent(payment_intent_id)

        return ResponseFactory.success(
            message="Donation status retrieved successfully",
            data={
                "donation_batch_id": donation_batch.id,
                "amount": donation_batch.amount,
                "status": donation_batch.status,
                "payment_intent_status": payment_intent.get("status"),
                "created_at": donation_batch.created_at.isoformat() if donation_batch.created_at else None,
                "payout_date": donation_batch.payout_date.isoformat() if donation_batch.payout_date else None
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get donation status")

@handle_controller_errors
def get_donation_history_enhanced(
    current_user: dict,
    db: Session,
    limit: int = 50,
    offset: int = 0
):
    """Get enhanced donation history for a donor"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        # Get donation batches instead of transactions
        db_donation_batches = db.query(DonationBatch).filter(
            DonationBatch.user_id == user.id
        ).order_by(DonationBatch.created_at.desc()).offset(offset).limit(limit).all()

        transactions = []
        for batch in db_donation_batches:
            transaction_data = {
                "id": batch.id,
                "amount": float(batch.amount),
                "amount_cents": int(batch.amount * 100),  # Convert to cents for compatibility
                "type": "roundup",  # All batches are roundup donations
                "status": batch.status,
                "description": f"Roundup donation batch - {batch.batch_number}",
                "created_at": batch.created_at.isoformat() if batch.created_at else None,
                "processed_at": batch.payout_date.isoformat() if batch.payout_date else None,
                "transaction_count": batch.transaction_count,
                "processing_fee": float(batch.processing_fee),
                "net_amount": float(batch.net_amount)
            }

            transactions.append(transaction_data)

        total_count = db.query(DonationBatch).filter(
            DonationBatch.user_id == user.id
        ).count()

        return ResponseFactory.success(
            message="Donation history retrieved successfully",
            data={
                "transactions": transactions,
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get donation history")

@handle_controller_errors
def refund_donation(
    current_user: dict,
    data: Dict[str, Any],
    db: Session
):
    """Refund a donation"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        transaction_id = data.get("transaction_id")
        amount_cents = data.get("amount_cents")
        reason = data.get("reason", "requested_by_customer")
        
        if not transaction_id:
            raise ValidationError("Transaction ID is required")

        # Find donation batch by ID
        donation_batch = db.query(DonationBatch).filter(
            DonationBatch.id == transaction_id,
            DonationBatch.user_id == user.id,
            DonationBatch.status == "completed"
        ).first()

        if not donation_batch:
            raise ValidationError("Donation batch not found or not eligible for refund")

        if not donation_batch.stripe_transfer_id:
            raise ValidationError("No Stripe transfer ID found for refund")

        # For refunds, we need to get the charge ID from Stripe
        # This would require fetching the payment intent and getting the charge ID
        from app.services.stripe_service import get_payment_intent
        payment_intent = get_payment_intent(donation_batch.stripe_transfer_id)
        
        if not payment_intent.get("charges", {}).get("data"):
            raise ValidationError("No charge found for refund")

        charge_id = payment_intent["charges"]["data"][0]["id"]
        
        refund = refund_payment(
            charge_id=charge_id,
            amount_cents=amount_cents,
            reason=reason
        )

        if refund.get("status") == "succeeded":
            donation_batch.status = "refunded"
            db.commit()

        return ResponseFactory.success(
            message="Donation refunded successfully",
            data={
                "donation_batch_id": donation_batch.id,
                "refund_id": refund.get("id"),
                "refund_status": refund.get("status"),
                "refund_amount": refund.get("amount")
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to refund donation")

@handle_controller_errors
def get_donation_summary(
    current_user: dict,
    db: Session
):
    """Get donation summary for a donor"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        # Calculate totals from DonationBatch instead of Transaction
        total_donations = db.query(func.sum(DonationBatch.amount)).filter(
            DonationBatch.user_id == user.id,
            DonationBatch.status == "completed"
        ).scalar() or 0

        # All donation batches are roundup donations
        roundup_donations = total_donations

        total_transactions = db.query(DonationBatch).filter(
            DonationBatch.user_id == user.id,
            DonationBatch.status == "completed"
        ).count()

        this_month_donations = db.query(func.sum(DonationBatch.amount)).filter(
            DonationBatch.user_id == user.id,
            DonationBatch.status == "completed",
            DonationBatch.created_at >= datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        ).scalar() or 0

        return ResponseFactory.success(
            message="Donation summary retrieved successfully",
            data={
                "total_donations_cents": int(total_donations * 100),  # Convert to cents
                "roundup_donations_cents": int(roundup_donations * 100),  # Convert to cents
                "total_transactions": total_transactions,
                "this_month_donations_cents": int(this_month_donations * 100)  # Convert to cents
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get donation summary")

# Legacy functions for backward compatibility
@handle_controller_errors
def process_roundup_donation(current_user: dict, data: Dict[str, Any], db: Session):
    """Process a roundup donation for a donor (legacy function)"""
    return process_roundup_donation_enhanced(current_user, data, db)

@handle_controller_errors
def get_donation_history(current_user: dict, db: Session):
    """Get donation history for a donor showing batched roundups with payout dates (legacy function)"""
    return get_donation_history_enhanced(current_user, db)

@handle_controller_errors
def get_donation_analytics(current_user: dict, db: Session):
    """Get donor donation analytics and trends"""
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    # Get last 12 months of data
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=365)

    # Get donation batches in date range
    batches = (
        db.query(DonationBatch)
        .filter(
            DonationBatch.user_id == user.id,
            DonationBatch.status == "completed",
            DonationBatch.created_at >= start_date,
            DonationBatch.created_at <= end_date,
        )
        .order_by(DonationBatch.created_at)
        .all()
    )

    # Calculate monthly totals
    monthly_totals = {}
    for batch in batches:
        month_key = batch.created_at.strftime("%Y-%m")
        if month_key not in monthly_totals:
            monthly_totals[month_key] = {"amount": 0.0, "count": 0}
        monthly_totals[month_key]["amount"] += float(batch.total_amount)
        monthly_totals[month_key]["count"] += 1

    # Generate time series data
    time_series = []
    current_date = start_date
    while current_date <= end_date:
        month_key = current_date.strftime("%Y-%m")
        time_series.append(
            {
                "month": month_key,
                "amount": monthly_totals.get(month_key, {}).get("amount", 0.0),
                "count": monthly_totals.get(month_key, {}).get("count", 0),
            }
        )
        current_date = (current_date + timedelta(days=32)).replace(day=1)

    # Calculate summary statistics
    total_amount = sum(float(batch.total_amount) for batch in batches)
    total_batches = len(batches)
    avg_per_batch = total_amount / total_batches if total_batches > 0 else 0.0

    return ResponseFactory.success(
        message="Donation analytics retrieved successfully",
        data={
            "time_series": time_series,
            "summary": {
                "total_amount": total_amount,
                "total_batches": total_batches,
                "average_per_batch": avg_per_batch,
                "period_months": 12,
            },
        },
    )

@handle_controller_errors
def get_donation_impact(current_user: dict, db: Session):
    """Get donor donation impact metrics"""
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    # Get all completed donation batches
    all_batches = (
        db.query(DonationBatch)
        .filter(DonationBatch.user_id == user.id, DonationBatch.status == "completed")
        .all()
    )

    # Calculate impact metrics
    total_donated = sum(float(batch.total_amount) for batch in all_batches)
    total_batches = len(all_batches)
    avg_per_batch = total_donated / total_batches if total_batches > 0 else 0.0

    # Get church information
    church_info = None
    primary_church = user.get_primary_church(db)
    if primary_church:
        church_info = {
            "id": primary_church.id,
            "name": primary_church.name,
            "website": primary_church.website,
            "is_verified": getattr(primary_church, "kyc_status", "not_submitted")
            == "approved",
        }

    # Calculate impact breakdown
    impact_breakdown = {
        "total_impact": total_donated,
        "donation_count": total_batches,
        "average_impact": avg_per_batch,
        "currency": "USD",
    }

    return ResponseFactory.success(
        message="Donation impact retrieved successfully",
        data={"impact": impact_breakdown, "church": church_info},
    )

@handle_controller_errors
def get_donation_history(user_id: int, page: int = 1, limit: int = 20, db: Session = None):
    """Get comprehensive donation history for a donor"""
    try:
        # Get user's donation preferences to find target church
        donation_prefs = db.query(DonationPreference).filter(
            DonationPreference.user_id == user_id
        ).first()
        
        if not donation_prefs:
            return ResponseFactory.success(
                message="No donation history found",
                data={
                    "donations": [],
                    "pagination": {
                        "page": page,
                        "limit": limit,
                        "total": 0,
                        "pages": 0
                    },
                    "summary": {
                        "total_donated": 0.0,
                        "total_donations": 0,
                        "average_donation": 0.0,
                        "first_donation": None,
                        "last_donation": None
                    }
                }
            )

        # Get donation batches for the user
        query = db.query(DonationBatch).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        ).order_by(DonationBatch.collection_date.desc())

        total_donations = query.count()
        donations = query.offset((page - 1) * limit).limit(limit).all()

        # Get church information - try multiple methods
        church = None
        if donation_prefs and donation_prefs.target_church_id:
            church = db.query(Church).filter(Church.id == donation_prefs.target_church_id).first()
        
        # If no church from preferences, try to get from user's primary church
        if not church:
            user = User.get_by_id(db, user_id)
            if user:
                primary_church = user.get_primary_church(db)
                if primary_church:
                    church = primary_church
        
        church_info = {
            "id": church.id if church else None,
            "name": church.name if church else "Not Connected",
            "logo_url": None  # Church model doesn't have logo_url field
        }

        # Format donation data
        donations_data = []
        for donation in donations:
            donations_data.append({
                "id": donation.id,
                "amount": float(donation.amount),
                "transaction_count": donation.transaction_count,
                "collection_date": donation.collection_date.isoformat(),
                "status": donation.status,
                "church": church_info,
                "roundup_period": {
                    "start_date": (donation.collection_date - timedelta(days=14)).isoformat() if donation.collection_date else None,
                    "end_date": donation.collection_date.isoformat() if donation.collection_date else None
                }
            })

        # Calculate summary statistics
        total_donated = sum(float(d.amount) for d in donations)
        average_donation = total_donated / len(donations) if donations else 0.0
        
        first_donation = donations[-1] if donations else None
        last_donation = donations[0] if donations else None

        return ResponseFactory.success(
            message="Donation history retrieved successfully",
            data={
                "donations": donations_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total_donations,
                    "pages": (total_donations + limit - 1) // limit
                },
                "summary": {
                    "total_donated": round(total_donated, 2),
                    "total_donations": total_donations,
                    "average_donation": round(average_donation, 2),
                    "first_donation": first_donation.collection_date.isoformat() if first_donation else None,
                    "last_donation": last_donation.collection_date.isoformat() if last_donation else None
                },
                "church": church_info
            }
        )

    except Exception as e:
        logging.error(f"Error getting donation history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get donation history")

@handle_controller_errors
def get_donation_impact_summary(user_id: int, db: Session = None):
    """Get comprehensive donation impact summary"""
    try:
        # Get user's donation preferences
        donation_prefs = db.query(DonationPreference).filter(
            DonationPreference.user_id == user_id
        ).first()
        
        if not donation_prefs:
            return ResponseFactory.success(
                message="No donation preferences found",
                data={
                    "impact_summary": {
                        "total_donated": 0.0,
                        "total_roundups": 0,
                        "average_roundup": 0.0,
                        "impact_stories": [],
                        "monthly_trend": []
                    }
                }
            )

        # Get church information
        church = db.query(Church).filter(Church.id == donation_prefs.target_church_id).first()
        
        # Get all completed donations
        donations = db.query(DonationBatch).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        ).order_by(DonationBatch.collection_date.asc()).all()

        # Calculate impact metrics
        total_donated = sum(float(d.amount) for d in donations)
        total_roundups = sum(d.transaction_count for d in donations)
        average_roundup = total_donated / total_roundups if total_roundups > 0 else 0.0

        # Calculate monthly trend
        monthly_data = {}
        for donation in donations:
            month_key = donation.collection_date.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {"amount": 0.0, "count": 0}
            monthly_data[month_key]["amount"] += float(donation.amount)
            monthly_data[month_key]["count"] += donation.transaction_count

        monthly_trend = [
            {
                "month": month,
                "amount": round(data["amount"], 2),
                "roundup_count": data["count"]
            }
            for month, data in sorted(monthly_data.items())
        ]

        # Generate impact stories (placeholder - would be real impact stories from church)
        impact_stories = [
            {
                "id": 1,
                "title": "Community Food Bank Support",
                "description": f"Your ${total_donated:.2f} in roundup donations helped provide meals for families in need.",
                "amount_contributed": round(total_donated * 0.3, 2),  # 30% of total
                "date": donations[-1].collection_date.isoformat() if donations else None
            }
        ] if donations else []

        return ResponseFactory.success(
            message="Donation impact summary retrieved successfully",
            data={
                "impact_summary": {
                    "total_donated": round(total_donated, 2),
                    "total_roundups": total_roundups,
                    "average_roundup": round(average_roundup, 2),
                    "impact_stories": impact_stories,
                    "monthly_trend": monthly_trend,
                    "church": {
                        "id": church.id if church else None,
                        "name": church.name if church else "Unknown Church",
                        "mission": "Supporting our community through micro-donations"
                    }
                }
            }
        )

    except Exception as e:
        logging.error(f"Error getting donation impact summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get donation impact summary")