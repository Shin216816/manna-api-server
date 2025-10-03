from fastapi import HTTPException
import logging
import traceback
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from sqlalchemy import func

from app.model.m_user import User
from app.model.m_donation_batch import DonationBatch
from app.model.m_donation_preference import DonationPreference
from app.model.m_plaid_items import PlaidItem
# PlaidAccount import removed - using on-demand Plaid API fetching
from app.model.m_church import Church
from app.core.responses import ResponseFactory

def get_mobile_dashboard(user_id: int, db: Session):
    """Get mobile dashboard overview"""
    try:
        user = User.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Get user's primary church
        primary_church = user.get_primary_church(db)
        church = primary_church

        # Get roundup settings
        settings = db.query(DonationPreference).filter(
            DonationPreference.user_id == user_id
        ).first()

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

        # Get bank accounts count from Plaid API
        from app.services.plaid_account_service import plaid_account_service
        bank_accounts_count = plaid_account_service.get_accounts_count(user_id, db)

        # Get recent donations (last 5)
        recent_donations = db.query(DonationBatch).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        ).order_by(DonationBatch.created_at.desc()).limit(5).all()

        recent_donations_data = []
        for donation in recent_donations:
            recent_donations_data.append({
                "id": donation.id,
                "amount": float(donation.total_amount),
                "created_at": donation.created_at.isoformat() if donation.created_at else None,
                "church_name": church.name if church else "Unknown Church"
            })

        return ResponseFactory.success(
            message="Mobile dashboard retrieved successfully",
            data={
                "user": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "phone": user.phone,
                    "profile_picture_url": user.profile_picture_url,
                    "is_email_verified": user.is_email_verified,
                    "is_phone_verified": user.is_phone_verified
                },
                "church": {
                    "id": church.id if church else None,
                    "name": church.name if church else None,
                    "address": church.address if church else None,
                    "city": church.city if church else None,
                    "state": church.state if church else None,
                    "website": church.website if church else None,
                    "is_verified": getattr(church, 'kyc_status', 'not_submitted') == 'approved' if church else False
                },
                "roundup_settings": {
                    "is_enabled": not settings.pause if settings else False,
                    "collection_frequency": settings.frequency if settings else "biweekly",
                    "cover_processing_fees": settings.cover_processing_fees if settings else True,
                    "multiplier": settings.multiplier if settings else "2x"
                },
                "summary": {
                    "total_donated": round(float(total_donations or 0), 2),
                    "this_month_donated": round(float(this_month_donations), 2),
                    "bank_accounts_linked": bank_accounts_count,
                    "currency": "USD"
                },
                "recent_donations": recent_donations_data
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to get dashboard"
        )
