from typing import Optional

"""
Admin Referrals Controller

Handles admin referral commission functionality:
- Get referral commissions
- Process referral payouts
- Track referral relationships
"""

from fastapi import HTTPException
import logging
import traceback
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta

from app.model.m_church import Church
from app.model.m_church_referral import ChurchReferral
from app.model.m_donation_batch import DonationBatch
from app.core.responses import ResponseFactory


def get_referral_commissions(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    db: Optional[Session] = None,
):
    """Get referral commissions with pagination and filtering"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        query = db.query(ChurchReferral)

        if status:
            query = query.filter(ChurchReferral.status == status)

        total = query.count()
        referrals = query.offset((page - 1) * limit).limit(limit).all()

        commissions_data = []
        for referral in referrals:
            # Get referring church
            referring_church = (
                db.query(Church).filter_by(id=referral.referring_church_id).first()
            )

            # Get referred church
            referred_church = (
                db.query(Church).filter_by(id=referral.referred_church_id).first()
            )

            # Calculate commission amount
            commission_amount = (
                float(referral.commission_amount) if referral.commission_amount else 0.0
            )

            commissions_data.append(
                {
                    "id": referral.id,
                    "referrer_name": referring_church.name if referring_church else "Unknown",
                    "referrer_email": referring_church.email if referring_church else "N/A",
                    "referred_church_name": referred_church.name if referred_church else "Unknown",
                    "referred_church_email": referred_church.email if referred_church else "N/A",
                    "commission_amount": commission_amount,
                    "status": referral.status,
                    "created_at": (
                        referral.created_at.isoformat() if referral.created_at else None
                    ),
                    "processed_at": (
                        referral.processed_at.isoformat()
                        if referral.processed_at
                        else None
                    ),
                }
            )

        return ResponseFactory.success(
            message="Referral commissions retrieved successfully",
            data={
                "referrals": commissions_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "total_pages": (total + limit - 1) // limit,
                },
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to retrieve referral commissions"
        )


def get_referral_statistics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Optional[Session] = None,
):
    """Get referral statistics"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        # Build query for referrals
        query = db.query(ChurchReferral)

        if start_date:
            query = query.filter(ChurchReferral.created_at >= start_date)
        if end_date:
            query = query.filter(ChurchReferral.created_at <= end_date)

        referrals = query.all()

        # Calculate statistics
        total_referrals = len(referrals)
        successful_referrals = len([r for r in referrals if r.status == "completed"])
        pending_referrals = len([r for r in referrals if r.status == "pending"])
        total_commission = sum(float(r.commission_amount or 0) for r in referrals)
        paid_commission = sum(
            float(r.commission_amount or 0)
            for r in referrals
            if r.status == "completed"
        )

        # Get top referring churches
        top_referrers = (
            db.query(
                Church.name,
                func.count(ChurchReferral.id).label("referral_count"),
                func.sum(ChurchReferral.commission_amount).label("total_commission"),
            )
            .join(ChurchReferral, Church.id == ChurchReferral.referring_church_id)
            .group_by(Church.id, Church.name)
            .order_by(func.count(ChurchReferral.id).desc())
            .limit(10)
            .all()
        )

        return ResponseFactory.success(
            message="Referral statistics retrieved successfully",
            data={
                "overview": {
                    "total_referrals": total_referrals,
                    "successful_referrals": successful_referrals,
                    "pending_referrals": pending_referrals,
                    "success_rate": round(
                        float(
                            (successful_referrals / total_referrals * 100)
                            if total_referrals > 0
                            else 0
                        ),
                        2,
                    ),
                },
                "commissions": {
                    "total_commission": round(float(total_commission), 2),
                    "paid_commission": round(float(paid_commission), 2),
                    "pending_commission": round(
                        float(total_commission - paid_commission), 2
                    ),
                },
                "top_referrers": [
                    {
                        "church_name": church.name,
                        "referral_count": count,
                        "total_commission": round(float(commission), 2),
                    }
                    for church, count, commission in top_referrers
                ],
                "date_range": {"start_date": start_date, "end_date": end_date},
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to retrieve referral statistics"
        )


def get_referral_payouts(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    db: Optional[Session] = None,
):
    """Get referral payouts"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        query = db.query(ChurchReferral).filter(ChurchReferral.status == "completed")

        if status:
            query = query.filter(ChurchReferral.payout_status == status)

        total = query.count()
        payouts = query.offset((page - 1) * limit).limit(limit).all()

        payouts_data = []
        for payout in payouts:
            # Get referring church
            referring_church = (
                db.query(Church).filter_by(id=payout.referring_church_id).first()
            )

            # Get referred church
            referred_church = (
                db.query(Church).filter_by(id=payout.referred_church_id).first()
            )

            payouts_data.append(
                {
                    "id": payout.id,
                    "referring_church": {
                        "id": referring_church.id if referring_church else None,
                        "name": referring_church.name if referring_church else None,
                    },
                    "referred_church": {
                        "id": referred_church.id if referred_church else None,
                        "name": referred_church.name if referred_church else None,
                    },
                    "commission_amount": (
                        float(payout.commission_amount)
                        if payout.commission_amount
                        else 0.0
                    ),
                    "payout_status": payout.payout_status,
                    "payout_date": (
                        payout.payout_date.isoformat() if payout.payout_date else None
                    ),
                    "created_at": (
                        payout.created_at.isoformat() if payout.created_at else None
                    ),
                }
            )

        return ResponseFactory.success(
            message="Referral payouts retrieved successfully",
            data={
                "payouts": payouts_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit,
                },
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to retrieve referral payouts"
        )
