from fastapi import HTTPException
import logging
import traceback
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from sqlalchemy import func, and_, desc
from typing import Optional, List, Dict, Any

from app.model.m_user import User
from app.model.m_donation_batch import DonationBatch
from app.model.m_church import Church
from app.model.m_donation_preference import DonationPreference
# from app.model.m_donation_schedule import DonationSchedule  # Removed - not needed for roundup-only system
from app.core.responses import ResponseFactory, SuccessResponse
from app.schema.donation_schema import DonationPreferencesRequest
# from app.schema.donation_schema import DonationScheduleRequest  # Removed - not needed for roundup-only system

def get_mobile_donation_history(user_id: int, limit: int = 20, db: Optional[Session] = None) -> SuccessResponse:
    """Get donation history for mobile user"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:    
        user = User.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        donations = db.query(DonationBatch).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        ).order_by(DonationBatch.created_at.desc()).limit(limit).all()

        donations_data = []
        for donation in donations:
            church = db.query(Church).filter(Church.id == donation.church_id).first()
            
            donations_data.append({
                "id": donation.id,
                "amount": float(donation.total_amount),
                "status": donation.status,
                "church_name": church.name if church else "Unknown Church",
                "church_id": donation.church_id,
                "created_at": donation.created_at.isoformat() if donation.created_at else None,
                "processed_at": donation.processed_at.isoformat() if donation.processed_at else None,
                "transaction_count": donation.transaction_count
            })

        return ResponseFactory.success(
            message="Donation history retrieved successfully",
            data={"donations": donations_data}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to get donation history"
        )

def get_mobile_donation_summary(user_id: int, db: Session):
    """Get donation summary for mobile user"""
    try:
        user = User.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Get total donations
        total_donations = db.query(func.sum(DonationBatch.total_amount)).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        ).scalar() or 0.0

        # Get this month's donations
        current_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month_donations = db.query(func.sum(DonationBatch.total_amount)).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed",
            DonationBatch.created_at >= current_month
        ).scalar() or 0.0

        # Get donation count
        total_count = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        ).scalar() or 0

        # Get this month's count
        this_month_count = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed",
            DonationBatch.created_at >= current_month
        ).scalar() or 0

        # Get average donation
        avg_donation = total_donations / total_count if total_count > 0 else 0.0

        return ResponseFactory.success(
            message="Donation summary retrieved successfully",
            data={
                "total_donated": round(float(total_donations or 0), 2),
                "this_month_donated": round(float(this_month_donations), 2),
                "total_donations": total_count,
                "this_month_donations": this_month_count,
                "average_donation": round(float(avg_donation), 2),
                "currency": "USD"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to get donation summary"
        )

def get_mobile_impact_analytics(user_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None, db: Optional[Session] = None) -> SuccessResponse:
    """Get impact analytics for mobile user"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        user = User.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Build query
        query = db.query(DonationBatch).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        )

        if start_date:
            query = query.filter(DonationBatch.created_at >= start_date)
        if end_date:
            query = query.filter(DonationBatch.created_at <= end_date)

        donations = query.all()

        # Calculate impact metrics
        total_amount = sum(float(d.total_amount) for d in donations)
        donation_count = len(donations)
        avg_donation = total_amount / donation_count if donation_count > 0 else 0.0

        # Group by church
        church_donations = {}
        for donation in donations:
            church = db.query(Church).filter(Church.id == donation.church_id).first()
            church_name = church.name if church else "Unknown Church"
            
            if church_name not in church_donations:
                church_donations[church_name] = {
                    "amount": 0.0,
                    "count": 0
                }
            
            church_donations[church_name]["amount"] += float(donation.total_amount)
            church_donations[church_name]["count"] += 1

        # Monthly breakdown
        monthly_data = {}
        for donation in donations:
            month_key = donation.created_at.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "amount": 0.0,
                    "count": 0
                }
            
            monthly_data[month_key]["amount"] += float(donation.total_amount)
            monthly_data[month_key]["count"] += 1

        # Sort monthly data
        sorted_monthly = sorted(monthly_data.items(), key=lambda x: x[0])

        return ResponseFactory.success(
            message="Impact analytics retrieved successfully",
            data={
                "total_impact": {
                    "amount": round(float(total_amount), 2),
                    "donations": donation_count,
                    "average": round(float(avg_donation), 2)
                },
                "by_church": [
                    {
                        "church_name": church_name,
                        "amount": round(data["amount"], 2),
                        "count": data["count"]
                    }
                    for church_name, data in church_donations.items()
                ],
                "monthly_breakdown": [
                    {
                        "month": month,
                        "amount": round(data["amount"], 2),
                        "count": data["count"]
                    }
                    for month, data in sorted_monthly
                ],
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to get impact analytics"
        )

# Extended Donation Functions

def get_donation_preferences(user_id: int, db: Session):
    """Get user donation preferences"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        preferences = db.query(DonationPreference).filter(DonationPreference.user_id == user_id).first()
        
        if not preferences:
            # Create default preferences
            preferences = DonationPreference(
                user_id=user_id,
                multiplier="1x",
                frequency="monthly",
                pause=False,
                cover_processing_fees=False
            )
            db.add(preferences)
            db.commit()
            db.refresh(preferences)
        
        preferences_data = {
            "user_id": user_id,
            "multiplier": preferences.multiplier,
            "frequency": preferences.frequency,
            "pause": preferences.pause,
            "cover_processing_fees": preferences.cover_processing_fees,
            "church_id": preferences.church_id,
            "next_collection_date": _calculate_next_collection_date(str(preferences.frequency)) if not preferences.pause else None,
            "is_active": not preferences.pause
        }
        
        return ResponseFactory.success(
            message="Donation preferences retrieved successfully",
            data=preferences_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to retrieve donation preferences")


def update_donation_preferences(user_id: int, preferences_data: DonationPreferencesRequest, db: Session):
    """Update user donation preferences"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        preferences = db.query(DonationPreference).filter(DonationPreference.user_id == user_id).first()
        
        if not preferences:
            preferences = DonationPreference(user_id=user_id)
            db.add(preferences)
        
        # Update preferences
        update_dict = preferences_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(preferences, field):
                setattr(preferences, field, value)
        
        db.commit()
        db.refresh(preferences)
        
        return ResponseFactory.success(
            message="Donation preferences updated successfully",
            data={
                "user_id": user_id,
                "updated_fields": list(update_dict.keys()),
                "next_collection_date": _calculate_next_collection_date(str(preferences.frequency)) if not preferences.pause else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to update donation preferences")


# REMOVED: create_donation_schedule function
# This function is not needed for roundup-only donation system.
# Roundup donations are triggered automatically by Plaid transactions,
# not by scheduled donations. All donation settings are handled by DonationPreference.


def get_donation_dashboard(user_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None, db: Optional[Session] = None):
    """Get donation dashboard data"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Build date filters
        date_filters = [DonationBatch.user_id == user_id, DonationBatch.status == "success"]
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                date_filters.append(DonationBatch.executed_at >= start_datetime)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start date format")
        
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                date_filters.append(DonationBatch.executed_at <= end_datetime)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end date format")
        
        # Get donation data
        donations = db.query(DonationBatch).filter(and_(*date_filters)).order_by(desc(DonationBatch.executed_at)).all()
        
        total_amount = sum(donation.total_amount for donation in donations)
        total_donations = len(donations)
        
        # Get preferences
        preferences = db.query(DonationPreference).filter(DonationPreference.user_id == user_id).first()
        
        dashboard_data = {
            "user_id": user_id,
            "total_amount": float(total_amount),
            "total_donations": total_donations,
            "average_per_donation": float(total_amount / total_donations) if total_donations > 0 else 0.0,
            "preferences": {
                "multiplier": preferences.multiplier if preferences else "1x",
                "frequency": preferences.frequency if preferences else "monthly",
                "is_active": not preferences.pause if preferences else False
            },
            "recent_donations": [
                {
                    "id": donation.id,
                    "amount": donation.total_amount,
                    "date": donation.executed_at.isoformat() if donation.executed_at else None,
                    "status": donation.status
                }
                for donation in donations[:5]  # Last 5 donations
            ],
            "date_range": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
        
        return ResponseFactory.success(
            message="Donation dashboard retrieved successfully",
            data=dashboard_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to retrieve donation dashboard")


def calculate_roundups(user_id: int, start_date: str, end_date: str, multiplier: str = "1x", db: Optional[Session] = None):
    """Calculate roundups for a date range"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Parse dates
        try:
            start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
        
        # This would typically integrate with Plaid to get actual transactions
        # For now, we'll return a mock calculation
        days_between = (end_datetime - start_datetime).days
        estimated_transactions = days_between * 2  # Assume 2 transactions per day
        estimated_roundup_per_transaction = 0.50  # Assume $0.50 average roundup
        
        total_roundup = estimated_transactions * estimated_roundup_per_transaction
        
        # Apply multiplier
        if multiplier == "2x":
            total_roundup *= 2
        elif multiplier == "3x":
            total_roundup *= 3
        
        calculation_data = {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
            "multiplier": multiplier,
            "estimated_transactions": estimated_transactions,
            "estimated_roundup_per_transaction": estimated_roundup_per_transaction,
            "total_roundup": round(total_roundup, 2),
            "calculation_date": datetime.now(timezone.utc).isoformat()
        }
        
        return ResponseFactory.success(
            message="Roundup calculation completed successfully",
            data=calculation_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to calculate roundups")


def execute_donation_batch(batch_id: int, user_id: int, db: Session):
    """Execute a donation batch"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get the donation batch
        batch = db.query(DonationBatch).filter(
            and_(
                DonationBatch.id == batch_id,
                DonationBatch.user_id == user_id
            )
        ).first()
        
        if not batch:
            raise HTTPException(status_code=404, detail="Donation batch not found")
        
        if batch.status != "pending":
            raise HTTPException(status_code=400, detail="Batch is not in pending status")
        
        # Update batch status to processing
        batch.status = "processing"
        batch.processing_started_at = datetime.now(timezone.utc)
        db.commit()
        
        # Here you would typically:
        # 1. Process the roundups through Stripe
        # 2. Update the batch status based on success/failure
        # Send database notification about successful donation
        from app.utils.notification_helper import send_donation_notification
        send_donation_notification(
            user_id=user_id,
            church_name=batch.church.name,
            amount=batch.total_amount,
            donation_type="direct",
            db=db
        )
        
        # For now, we'll simulate success
        batch.status = "success"
        batch.executed_at = datetime.now(timezone.utc)
        db.commit()
        
        return ResponseFactory.success(
            message="Donation batch executed successfully",
            data={
                "batch_id": batch.id,
                "status": batch.status,
                "executed_at": batch.executed_at.isoformat() if batch.executed_at else None,
                "total_amount": batch.total_amount
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to execute donation batch")


# Helper Functions

def _calculate_next_collection_date(frequency: str) -> str:
    """Calculate next collection date based on frequency"""
    now = datetime.now(timezone.utc)
    
    if frequency == "weekly":
        next_date = now + timedelta(days=7)
    elif frequency == "bi-weekly":
        next_date = now + timedelta(days=14)
    elif frequency == "monthly":
        # Add one month
        if now.month == 12:
            next_date = now.replace(year=now.year + 1, month=1)
        else:
            next_date = now.replace(month=now.month + 1)
    else:
        next_date = now + timedelta(days=30)  # Default to monthly
    
    return next_date.strftime("%Y-%m-%d")


def _calculate_next_donation_date(start_date: datetime, frequency: str) -> str:
    """Calculate next donation date for a schedule"""
    if frequency == "weekly":
        next_date = start_date + timedelta(days=7)
    elif frequency == "bi-weekly":
        next_date = start_date + timedelta(days=14)
    elif frequency == "monthly":
        if start_date.month == 12:
            next_date = start_date.replace(year=start_date.year + 1, month=1)
        else:
            next_date = start_date.replace(month=start_date.month + 1)
    else:
        next_date = start_date + timedelta(days=30)
    
    return next_date.strftime("%Y-%m-%d")
