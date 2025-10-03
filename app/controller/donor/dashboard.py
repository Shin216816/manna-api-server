import logging
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, and_

from app.model.m_user import User
from app.model.m_roundup_new import DonorPayout
from app.model.m_donation_preference import DonationPreference
from app.model.m_church import Church
from app.core.responses import ResponseFactory
from app.core.exceptions import UserNotFoundError
from app.utils.error_handler import handle_controller_errors
from fastapi import HTTPException

@handle_controller_errors
def get_dashboard_overview(current_user: dict, db: Session):
    """Get donor dashboard overview with key metrics"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    # Get user's donation preferences
    preferences = db.query(DonationPreference).filter(
        DonationPreference.user_id == user.id
    ).first()

    # Get recent donor payouts
    recent_payouts = db.query(DonorPayout).filter(
        DonorPayout.user_id == user.id
    ).order_by(DonorPayout.created_at.desc()).limit(5).all()

    # Get church information if user is associated with one
    church_info = None
    primary_church = user.get_primary_church(db)
    if primary_church:
        church_info = {
            "id": primary_church.id,
            "name": primary_church.name,
            "website": primary_church.website,
            "is_verified": getattr(primary_church, 'kyc_status', 'not_submitted') == 'approved'
        }

    # Calculate total donated
    total_donated = db.query(func.sum(DonorPayout.donation_amount)).filter(
        DonorPayout.user_id == user.id,
        DonorPayout.status == "completed"
    ).scalar() or 0.0

    # Calculate this month's donations
    start_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_donations = db.query(func.sum(DonorPayout.donation_amount)).filter(
        DonorPayout.user_id == user.id,
        DonorPayout.status == "completed",
        DonorPayout.created_at >= start_of_month
    ).scalar() or 0.0

    # Calculate pending roundups (simplified)
    pending_amount = 0.0
    transaction_count = 0
    next_collection_date = None
    
    if preferences and not preferences.pause:
        # Get last payout to estimate next collection
        last_payout = db.query(DonorPayout).filter(
            DonorPayout.user_id == user.id
        ).order_by(DonorPayout.created_at.desc()).first()
        
        if last_payout:
            if preferences.frequency == "biweekly":
                next_collection_date = last_payout.created_at + timedelta(days=14)
            else:  # monthly
                next_collection_date = last_payout.created_at + timedelta(days=30)

    return ResponseFactory.success(
        message="Dashboard overview retrieved successfully",
        data={
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone": user.phone,
                "is_email_verified": user.is_email_verified,
                "is_phone_verified": user.is_phone_verified
            },
            "church": church_info,
            "preferences": {
                "frequency": preferences.frequency if preferences else None,
                "multiplier": preferences.multiplier if preferences else None,
                "pause": preferences.pause if preferences else False,
                "cover_processing_fees": preferences.cover_processing_fees if preferences else False,
                "monthly_cap": preferences.monthly_cap if preferences else None
            },
            "pending_roundups": {
                "amount": pending_amount,
                "next_collection_date": next_collection_date.isoformat() if next_collection_date else None,
                "transaction_count": transaction_count
            },
            "summary": {
                "total_donated": float(total_donated),
                "this_month_donations": float(this_month_donations),
                "total_payouts": len(recent_payouts),
                "is_active": preferences.pause == False if preferences else False
            },
            "recent_activity": [
                {
                    "id": payout.id,
                    "amount": float(payout.donation_amount),
                    "status": payout.status,
                    "created_at": payout.created_at.isoformat(),
                    "type": "donor_payout"
                }
                for payout in recent_payouts
            ]
        }
    )

@handle_controller_errors
def get_impact_analytics(current_user: dict, db: Session):
    """Get donor impact analytics using real transaction history - matches donations endpoint structure"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    # Import DonationBatch for consistency with donations endpoint
    from app.model.m_donation_batch import DonationBatch
    from app.model.m_donation_preference import DonationPreference

    # Get user's donation preferences to find target church (same as donations endpoint)
    donation_prefs = db.query(DonationPreference).filter(
        DonationPreference.user_id == user.id
    ).first()
    
    if not donation_prefs:
        return ResponseFactory.success(
            message="No donation preferences found",
            data={
                "summary": {
                    "total_donated": 0.0,
                    "total_donations": 0,
                    "average_donation": 0.0,
                    "date_range": {"days": 0}
                },
                "church": {
                    "id": None,
                    "name": "Not Connected",
                    "website": None,
                    "is_verified": False,
                    "mission": "No church connected"
                }
            }
        )

    # Get all completed donation batches (same query as donations endpoint)
    all_batches = db.query(DonationBatch).filter(
        DonationBatch.user_id == user.id,
        DonationBatch.status == "completed"
    ).order_by(DonationBatch.collection_date.desc()).all()

    # Get church information - try multiple methods (same as donations endpoint)
    from app.model.m_church import Church
    church = None
    if donation_prefs and donation_prefs.target_church_id:
        church = db.query(Church).filter(Church.id == donation_prefs.target_church_id).first()
    
    # If no church from preferences, try to get from user's primary church
    if not church:
        primary_church = user.get_primary_church(db)
        if primary_church:
            church = primary_church
    
    church_info = {
        "id": church.id if church else None,
        "name": church.name if church else "Not Connected",
        "website": church.website if church else None,
        "is_verified": getattr(church, 'kyc_status', 'not_submitted') == 'approved' if church else False,
        "mission": getattr(church, 'mission', 'Supporting our community through micro-donations') if church else 'No church connected'
    }

    # Calculate summary statistics (same logic as donations endpoint)
    total_donated = sum(float(batch.amount) for batch in all_batches)
    total_donations = len(all_batches)
    average_donation = total_donated / total_donations if total_donations > 0 else 0.0

    # Calculate date range from actual donations
    donation_dates = [batch.collection_date for batch in all_batches if batch.collection_date]
    days = 0
    if len(donation_dates) > 1:
        days = (max(donation_dates) - min(donation_dates)).days + 1
    elif len(donation_dates) == 1:
        days = 1

    # Generate monthly trend data for charts (same as donations endpoint)
    monthly_data = {}
    for batch in all_batches:
        if batch.collection_date:
            month_key = batch.collection_date.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {"amount": 0.0, "count": 0}
            monthly_data[month_key]["amount"] += float(batch.amount)
            monthly_data[month_key]["count"] += 1

    # Convert to sorted list for frontend
    monthly_trend = [
        {
            "month": month,
            "amount": round(data["amount"], 2),
            "count": data["count"]
        }
        for month, data in sorted(monthly_data.items())
    ]

    return ResponseFactory.success(
        message="Impact analytics retrieved successfully",
        data={
            "summary": {
                "total_donated": round(total_donated, 2),
                "total_donations": total_donations,
                "average_donation": round(average_donation, 2),
                "date_range": {
                    "days": days
                }
            },
            "church": church_info,
            "monthly_trend": monthly_trend
        }
    )

@handle_controller_errors
def get_summary_stats(current_user: dict, db: Session):
    """Get donor summary statistics"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    # Parse date range (last 30 days)
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)

    # Get all completed donor payouts
    all_payouts = db.query(DonorPayout).filter(
        DonorPayout.user_id == user.id,
        DonorPayout.status == "completed"
    ).all()

    # Get payouts in date range
    recent_payouts = db.query(DonorPayout).filter(
        DonorPayout.user_id == user.id,
        DonorPayout.status == "completed",
        DonorPayout.created_at >= start_date,
        DonorPayout.created_at <= end_date
    ).all()

    # Calculate statistics
    total_donated = sum(float(payout.donation_amount) for payout in all_payouts)
    recent_donated = sum(float(payout.donation_amount) for payout in recent_payouts)
    total_payouts = len(all_payouts)
    recent_payouts_count = len(recent_payouts)
    avg_per_payout = total_donated / total_payouts if total_payouts > 0 else 0.0

    # Get user preferences
    preferences = db.query(DonationPreference).filter(
        DonationPreference.user_id == user.id
    ).first()

    return ResponseFactory.success(
        message="Summary statistics retrieved successfully",
        data={
            "lifetime": {
                "total_donated": total_donated,
                "total_payouts": total_payouts,
                "average_per_payout": avg_per_payout
            },
            "recent": {
                "period_days": 30,
                "total_donated": recent_donated,
                "total_payouts": recent_payouts_count,
                "average_per_payout": recent_donated / recent_payouts_count if recent_payouts_count > 0 else 0.0
            },
            "preferences": {
                "frequency": preferences.frequency if preferences else None,
                "multiplier": preferences.multiplier if preferences else None,
                "pause": preferences.pause if preferences else False,
                "cover_processing_fees": preferences.cover_processing_fees if preferences else False,
                "monthly_cap": preferences.monthly_cap if preferences else None
            }
        }
    )

@handle_controller_errors
def get_recent_activity(current_user: dict, db: Session):
    """Get donor recent activity and transactions"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    # Get recent donor payouts
    recent_payouts = db.query(DonorPayout).filter(
        DonorPayout.user_id == user.id
    ).order_by(DonorPayout.created_at.desc()).limit(10).all()

    # Get user preferences
    preferences = db.query(DonationPreference).filter(
        DonationPreference.user_id == user.id
    ).first()

    # Get church information
    church_info = None
    primary_church = user.get_primary_church(db)
    if primary_church:
        church_info = {
            "id": primary_church.id,
            "name": primary_church.name,
            "website": primary_church.website,
            "is_verified": getattr(primary_church, 'kyc_status', 'not_submitted') == 'approved'
        }

    return ResponseFactory.success(
        message="Recent activity retrieved successfully",
        data={
            "activities": [
                {
                    "id": payout.id,
                    "type": "donor_payout",
                    "amount": float(payout.donation_amount),
                    "status": payout.status,
                    "created_at": payout.created_at.isoformat(),
                    "processed_at": payout.processed_at.isoformat() if payout.processed_at else None,
                    "church": church_info
                }
                for payout in recent_payouts
            ],
            "preferences": {
                "frequency": preferences.frequency if preferences else None,
                "multiplier": preferences.multiplier if preferences else None,
                "pause": preferences.pause if preferences else False
            },
            "total_activities": len(recent_payouts)
        }
    )

@handle_controller_errors
def get_church_impact_stories(current_user: dict, db: Session, page: int = 1, limit: int = 10):
    """Get impact stories from donor's church - Fixed to match frontend expectations"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    # Get user's primary church
    primary_church = user.get_primary_church(db)
    if not primary_church:
        return ResponseFactory.success(
            message="No church associated with user",
            data={
                "stories": [],
                "church": {
                    "id": None,
                    "name": "Not Connected",
                    "website": None,
                    "is_verified": False,
                    "mission": "No church connected"
                },
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total_count": 0,
                    "total_pages": 0
                }
            }
        )

    # Import ImpactStory here to avoid circular imports
    from app.model.m_impact_story import ImpactStory
    
    offset = (page - 1) * limit
    
    # Get published impact stories from the church
    stories = db.query(ImpactStory).filter(
        ImpactStory.church_id == primary_church.id,
        ImpactStory.is_active == True,
        ImpactStory.status == "published"
    ).order_by(ImpactStory.published_date.desc()).offset(offset).limit(limit).all()
    
    total_count = db.query(func.count(ImpactStory.id)).filter(
        ImpactStory.church_id == primary_church.id,
        ImpactStory.is_active == True,
        ImpactStory.status == "published"
    ).scalar()
    
    stories_data = []
    for story in stories:
        stories_data.append({
            "id": story.id,
            "title": story.title,
            "description": story.description,
            "amount_used": float(story.amount_used),
            "category": story.category,
            "image_url": story.image_url,
            "published_date": story.published_date.isoformat() if story.published_date else None,
            "people_impacted": story.people_impacted,
            "events_held": story.events_held,
            "items_purchased": story.items_purchased,
            "created_at": story.created_at.isoformat()
        })

    # Enhanced church information to match frontend expectations
    church_info = {
        "id": primary_church.id,
        "name": primary_church.name,
        "website": primary_church.website,
        "is_verified": getattr(primary_church, 'kyc_status', 'not_submitted') == 'approved',
        "mission": getattr(primary_church, 'mission', 'Supporting our community through micro-donations')
    }

    return ResponseFactory.success(
        message="Church impact stories retrieved successfully",
        data={
            "stories": stories_data,
            "church": church_info,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": (total_count + limit - 1) // limit
            }
        }
    )
