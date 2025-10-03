"""
Church Dashboard Controller

Handles church dashboard functionality:
- Dashboard overview data
- Analytics and reporting
- Payout history
- Church performance metrics
"""

from fastapi import HTTPException
import logging
import traceback
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, or_
from datetime import datetime, timezone, timedelta
from typing import Optional
from app.model.m_church import Church
from app.model.m_impact_story import ImpactStory
from app.model.m_user import User
from app.model.m_church_admin import ChurchAdmin
from app.model.m_roundup_new import DonorPayout, ChurchPayout
from app.model.m_donation_preference import DonationPreference
from app.model.m_plaid_items import PlaidItem
from app.model.m_church_referral import ChurchReferral
from app.model.m_referral import ReferralCommission
# Transaction model removed - using DonorPayout instead
# from app.model.m_payout import Payout  # Old model - using ChurchPayout instead
from app.model.m_donation_preference import DonationPreference
from app.core.responses import ResponseFactory
from app.services.analytics_service import ChurchDashboardService
from app.services.analytics_service import ChurchDashboardService
from app.services.analytics_service import get_church_spending_analytics
import math


def get_church_referral_info(church_id: int, db: Session) -> dict:
    """Get church referral information for dashboard"""
    try:
        # Get active referral code
        referral = db.query(ChurchReferral).filter(
            ChurchReferral.referring_church_id == church_id,
            ChurchReferral.status == "active"
        ).first()

        if not referral:
            return {
                "has_referral_code": False,
                "referral_code": None,
                "total_referrals": 0,
                "total_commission_earned": 0.0,
                "pending_commission": 0.0
            }

        # Get referral statistics
        total_referrals = db.query(func.count(ChurchReferral.id)).filter(
            ChurchReferral.referring_church_id == church_id,
            ChurchReferral.status == "active"
        ).scalar() - 1  # Exclude self-referral

        # Get total commission earned
        total_commission = db.query(func.sum(ReferralCommission.commission_amount)).filter(
            ReferralCommission.church_id == church_id,
            ReferralCommission.status == "paid"
        ).scalar() or 0.0

        # Get pending commission
        pending_commission = db.query(func.sum(ReferralCommission.commission_amount)).filter(
            ReferralCommission.church_id == church_id,
            ReferralCommission.status == "pending"
        ).scalar() or 0.0

        return {
            "has_referral_code": True,
            "referral_code": referral.referral_code,
            "created_at": referral.created_at.isoformat(),
            "expires_at": referral.expires_at.isoformat() if referral.expires_at else None,
            "commission_rate": referral.commission_rate,
            "total_referrals": total_referrals,
            "total_commission_earned": float(total_commission),
            "pending_commission": float(pending_commission)
        }

    except Exception as e:
        logging.error(f"Error getting referral info: {str(e)}")
        return {
            "has_referral_code": False,
            "referral_code": None,
            "total_referrals": 0,
            "total_commission_earned": 0.0,
            "pending_commission": 0.0,
            "error": str(e)
        }


def get_church_dashboard(
    church_id: int, db: Session, current_user: Optional[dict] = None
):
    """Get simplified church dashboard data for MVP"""
    try:
        # Get church info
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Get total members (donors) for this church
        total_members = (
            db.query(func.count(User.id))
            .filter(
                User.church_id == church_id,
                User.role == "donor",
                User.is_active == True,
            )
            .scalar()
        )
        # Alias for clarity: existing donors equals current total active donors
        existing_donors_total = int(total_members or 0)

        # Get active donors - users who have made donations (simplified for MVP)
        active_donors = (
            db.query(func.count(func.distinct(DonorPayout.user_id)))
            .filter(
                DonorPayout.church_id == church_id, 
                DonorPayout.status == "completed"
            )
            .scalar()
        )

        # Get total donations (simplified for MVP)
        total_donations = (
            db.query(func.sum(DonorPayout.donation_amount))
            .filter(
                DonorPayout.church_id == church_id,
                DonorPayout.status == "completed",
            )
            .scalar()
            or 0
        )
        total_donations = float(total_donations) if total_donations else 0.0

        # Get this month's donations
        current_month = datetime.now(timezone.utc).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        this_month_donations = (
            db.query(func.sum(DonorPayout.donation_amount))
            .filter(
                DonorPayout.church_id == church_id,
                DonorPayout.status == "completed",
                DonorPayout.created_at >= current_month,
            )
            .scalar()
            or 0
        )
        this_month_donations = float(this_month_donations) if this_month_donations else 0.0

        # Get donation count
        donation_count = (
            db.query(func.count(DonorPayout.id))
            .filter(
                DonorPayout.church_id == church_id,
                DonorPayout.status == "completed",
            )
            .scalar()
        )

        # Get recent donations (simplified for MVP)
        recent_donations = (
            db.query(DonorPayout)
            .filter(
                DonorPayout.church_id == church_id,
                DonorPayout.status == "completed",
            )
            .order_by(DonorPayout.created_at.desc())
            .limit(10)
            .all()
        )

        recent_donations_data = []
        for donation in recent_donations:
            user = db.query(User).filter_by(id=donation.user_id).first()
            recent_donations_data.append(
                {
                    "id": donation.id,
                    "amount": float(donation.donation_amount),
                    "date": donation.created_at.isoformat(),
                    "donor_name": (
                        f"{user.first_name} {user.last_name}" if user else "Unknown"
                    ),
                    "transaction_count": donation.plaid_transaction_count or 1,
                }
            )

        # Get top donors (simplified for MVP)
        top_donors = (
            db.query(
                User.id,
                User.first_name,
                User.last_name,
                func.sum(DonorPayout.donation_amount).label("total_donated"),
            )
            .join(DonorPayout)
            .filter(
                User.church_id == church_id,
                User.role == "donor",
                User.is_active == True,
                DonorPayout.status == "completed",
            )
            .group_by(User.id)
            .order_by(desc("total_donated"))
            .limit(5)
            .all()
        )

        top_donors_data = []
        for donor in top_donors:
            total_donated_dollars = float(donor.total_donated) if donor.total_donated else 0.0
            top_donors_data.append(
                {
                    "id": donor.id,
                    "name": f"{donor.first_name} {donor.last_name}",
                    "total_donated": round(total_donated_dollars, 2),
                }
            )

        # Get church admin info
        church_admin = db.query(ChurchAdmin).filter_by(church_id=church_id).first()
        admin_user = None
        if church_admin:
            admin_user = db.query(User).filter_by(id=church_admin.user_id).first()

        # Get payout data (simplified for MVP)
        from app.controller.admin.dashboard import calculate_next_payout_date
        next_payout_date = calculate_next_payout_date().strftime("%Y-%m-%d")
        next_payout_amount = round(
            float(this_month_donations) * 0.95, 2
        )  # 95% of this month's donations

        # Get payouts history (simplified for MVP)
        payouts_query = (
            db.query(ChurchPayout)
            .filter(ChurchPayout.church_id == church_id)
            .order_by(ChurchPayout.created_at.desc())
            .limit(10)
            .all()
        )

        payouts = []
        for payout in payouts_query:
            payouts.append(
                {
                    "id": payout.id,
                    "amount": float(payout.net_payout_amount),
                    "gross_amount": float(payout.gross_donation_amount),
                    "system_fee": float(payout.system_fee_amount),
                    "donor_count": payout.donor_count,
                    "donation_count": payout.donation_count,
                    "period_start": payout.period_start,
                    "period_end": payout.period_end,
                    "stripe_transfer_id": payout.stripe_transfer_id,
                    "date": payout.created_at.strftime("%Y-%m-%d"),
                    "status": payout.status,
                    "created_at": payout.created_at.isoformat(),
                    "processed_at": (
                        payout.processed_at.isoformat()
                        if payout.processed_at
                        else None
                    ),
                    "reference": f"PAY-{payout.id:06d}-{payout.created_at.strftime('%Y%m')}",
                }
            )

        # Get pending payouts summary
        pending_payouts_summary = (
            db.query(
                func.sum(ChurchPayout.net_payout_amount).label("total_pending_amount"),
                func.count(ChurchPayout.id).label("pending_count"),
            )
            .filter(
                ChurchPayout.church_id == church_id,
                ChurchPayout.status.in_(["pending", "processing"]),
            )
            .first()
        )

        pending_amount = (
            float(pending_payouts_summary.total_pending_amount)
            if pending_payouts_summary.total_pending_amount
            else 0.0
        )
        pending_count = pending_payouts_summary.pending_count or 0

        # Build monthly donor growth trend (last 6 full months including current month)
        try:
            now_utc = datetime.now(timezone.utc)
            anchor = now_utc.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            def add_months(dt, months):
                year = dt.year + (dt.month - 1 + months) // 12
                month = (dt.month - 1 + months) % 12 + 1
                return dt.replace(year=year, month=month, day=1)

            months = [add_months(anchor, -i) for i in range(5, -1, -1)]  # last 6 months

            monthly_donor_trend = []
            for month_start in months:
                month_end = add_months(month_start, 1)

                new_donors_count = (
                    db.query(func.count(User.id))
                    .filter(
                        User.church_id == church_id,
                        User.role == "donor",
                        User.is_active == True,
                        User.created_at >= month_start,
                        User.created_at < month_end,
                    )
                    .scalar()
                    or 0
                )

                total_donors_cumulative = (
                    db.query(func.count(User.id))
                    .filter(
                        User.church_id == church_id,
                        User.role == "donor",
                        User.is_active == True,
                        User.created_at < month_end,
                    )
                    .scalar()
                    or 0
                )

                existing_donors = int(total_donors_cumulative) - int(new_donors_count)
                if existing_donors < 0:
                    existing_donors = 0

                monthly_donor_trend.append(
                    {
                        "month": month_start.strftime("%Y-%m"),
                        "new_donors": int(new_donors_count),
                        "existing_donors": existing_donors,
                        "total_donors": int(total_donors_cumulative),
                    }
                )
        except Exception as trend_err:
            logging.error(f"Failed building monthly donor trend: {trend_err}")
            monthly_donor_trend = []

        # Build impact analytics for "Share Your Impact" card
        try:
            # Total active stories
            total_stories = (
                db.query(func.count(ImpactStory.id))
                .filter(
                    ImpactStory.church_id == church_id,
                    ImpactStory.is_active == True,
                )
                .scalar()
                or 0
            )

            # Total impact is the sum of amount_used across active stories
            total_impact_amount = (
                db.query(func.sum(ImpactStory.amount_used))
                .filter(
                    ImpactStory.church_id == church_id,
                    ImpactStory.is_active == True,
                )
                .scalar()
                or 0
            )
            total_impact_amount = float(total_impact_amount) if total_impact_amount else 0.0

            # Stories created this month
            month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_stories = (
                db.query(func.count(ImpactStory.id))
                .filter(
                    ImpactStory.church_id == church_id,
                    ImpactStory.is_active == True,
                    ImpactStory.created_at >= month_start,
                )
                .scalar()
                or 0
            )

            # Previous month stories for growth
            def add_months(dt, months):
                year = dt.year + (dt.month - 1 + months) // 12
                month = (dt.month - 1 + months) % 12 + 1
                return dt.replace(year=year, month=month, day=1)

            prev_month_start = add_months(month_start, -1)
            prev_month_end = month_start
            prev_month_stories = (
                db.query(func.count(ImpactStory.id))
                .filter(
                    ImpactStory.church_id == church_id,
                    ImpactStory.is_active == True,
                    ImpactStory.created_at >= prev_month_start,
                    ImpactStory.created_at < prev_month_end,
                )
                .scalar()
                or 0
            )

            if prev_month_stories == 0:
                monthly_growth = 100.0 if monthly_stories > 0 else 0.0
            else:
                monthly_growth = ((monthly_stories - prev_month_stories) / prev_month_stories) * 100.0

            # Top category among active stories
            top_category_row = (
                db.query(ImpactStory.category, func.count(ImpactStory.id).label("cnt"))
                .filter(
                    ImpactStory.church_id == church_id,
                    ImpactStory.is_active == True,
                )
                .group_by(ImpactStory.category)
                .order_by(desc("cnt"))
                .first()
            )
            top_category = top_category_row[0] if top_category_row else None

            impact_analytics = {
                "total_stories": int(total_stories),
                "total_impact": round(total_impact_amount, 2),
                "monthly_stories": int(monthly_stories),
                # Placeholders for unavailable metrics in MVP
                "engagement_rate": 0.0,
                "avg_story_views": 0,
                "conversion_rate": 0.0,
                "top_category": top_category or "No stories",
                "monthly_growth": round(monthly_growth, 1),
            }
        except Exception as impact_err:
            logging.error(f"Failed building impact analytics: {impact_err}")
            impact_analytics = {
                "total_stories": 0,
                "total_impact": 0.0,
                "monthly_stories": 0,
                "engagement_rate": 0.0,
                "avg_story_views": 0,
                "conversion_rate": 0.0,
                "top_category": "No stories",
                "monthly_growth": 0.0,
            }

        return ResponseFactory.success(
            message="Church dashboard retrieved successfully",
            data={
                "admin": {
                    "id": admin_user.id if admin_user else None,
                    "name": (
                        f"{admin_user.first_name} {admin_user.last_name}"
                        if admin_user
                        else "Church Admin"
                    ),
                    "email": admin_user.email if admin_user else church.email,
                },
                "church": {
                    "id": church.id,
                    "name": church.name,
                    "email": church.email,
                    "status": church.status,
                    "kyc_status": church.kyc_status,
                    "is_active": church.is_active,
                    "charges_enabled": church.charges_enabled,
                    "payouts_enabled": church.payouts_enabled,
                    "referral_code": church.referral_code,
                },
                "overview": {
                    "total_members": total_members,
                    "active_donors": active_donors,
                    "existing_donors_total": existing_donors_total,
                    "total_donations": round(float(total_donations or 0), 2),
                    "this_month_donations": round(float(this_month_donations or 0), 2),
                    "donation_count": donation_count,
                    "average_donation": (
                        round(float(total_donations or 0) / donation_count, 2)
                        if donation_count > 0
                        else 0.0
                    ),
                },
                "payouts": {
                    "next_payout_date": next_payout_date,
                    "next_payout_amount": next_payout_amount,
                    "pending_amount": round(pending_amount, 2),
                    "pending_count": pending_count,
                    "history": payouts,
                },
                "monthly_donor_trend": monthly_donor_trend,
                "existing_donors_total": existing_donors_total,
                "recent_donations": recent_donations_data,
                "top_donors": top_donors_data,
                "impact_analytics": impact_analytics,
                "kyc_status": {
                    "status": church.kyc_status,
                    "submitted_at": church.kyc_submitted_at.isoformat() if church.kyc_submitted_at else None,
                    "next_step": "complete_kyc" if church.kyc_status == "not_submitted" else "dashboard"
                }
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Church dashboard error for church_id {church_id}: {str(e)}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve church dashboard: {str(e)}"
        )


def get_church_analytics(
    church_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Optional[Session] = None,
):
    """Get detailed church analytics"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Build query for donations using DonorPayout model
        query = db.query(DonorPayout).filter(
            DonorPayout.church_id == church_id,
            DonorPayout.status == "completed",
        )

        if start_date:
            query = query.filter(DonorPayout.created_at >= start_date)
        if end_date:
            query = query.filter(DonorPayout.created_at <= end_date)

        donations = query.all()

        # Calculate analytics
        total_amount = sum(float(d.donation_amount) for d in donations)
        donation_count = len(donations)
        avg_donation = total_amount / donation_count if donation_count > 0 else 0.0

        # Get donor count
        unique_donors = (
            db.query(func.count(func.distinct(DonorPayout.user_id)))
            .filter(
                DonorPayout.church_id == church_id,
                DonorPayout.status == "completed",
            )
            .scalar()
        )

        # Monthly breakdown
        monthly_data = {}
        for donation in donations:
            month_key = donation.created_at.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {"amount": 0.0, "count": 0}
            monthly_data[month_key]["amount"] += float(donation.donation_amount)
            monthly_data[month_key]["count"] += 1

        sorted_monthly = sorted(monthly_data.items(), key=lambda x: x[0])

        return ResponseFactory.success(
            message="Church analytics retrieved successfully",
            data={
                "church_id": church_id,
                "church_name": church.name,
                "analytics": {
                    "total_amount": round(float(total_amount), 2),
                    "donation_count": donation_count,
                    "average_donation": round(float(avg_donation), 2),
                    "unique_donors": unique_donors,
                },
                "monthly_breakdown": [
                    {
                        "month": month,
                        "amount": round(data["amount"], 2),
                        "count": data["count"],
                    }
                    for month, data in sorted_monthly
                ],
                "date_range": {"start_date": start_date, "end_date": end_date},
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to retrieve church analytics"
        )


def get_church_members(
    church_id: int, page: int = 1, limit: int = 20, db: Optional[Session] = None
):
    """Get church members with pagination"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        query = db.query(User).filter(
            User.church_id == church_id, User.role == "donor", User.is_active == True
        )
        total = query.count()
        members = query.offset((page - 1) * limit).limit(limit).all()

        members_data = []
        for member in members:
            # Get member's total donations
            total_donations = (
                db.query(func.sum(DonorPayout.donation_amount))
                .filter(
                    DonorPayout.user_id == member.id,
                    DonorPayout.status == "completed",
                )
                .scalar()
                or 0
            )
            total_donations = float(total_donations) if total_donations else 0.0

            # Get member's donation preferences
            preferences = (
                db.query(DonationPreference).filter_by(user_id=member.id).first()
            )

            members_data.append(
                {
                    "id": member.id,
                    "first_name": member.first_name,
                    "last_name": member.last_name,
                    "email": member.email,
                    "phone": member.phone,
                    "is_active": member.is_active,
                    "created_at": (
                        member.created_at.isoformat() if member.created_at else None
                    ),
                    "last_login": (
                        member.last_login.isoformat() if member.last_login else None
                    ),
                    "total_donations": round(float(total_donations or 0), 2),
                    "roundup_enabled": not preferences.pause if preferences else False,
                    "donation_frequency": (
                        preferences.frequency if preferences else None
                    ),
                }
            )

        return ResponseFactory.success(
            message="Church members retrieved successfully",
            data={
                "members": members_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit,
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve church members")


def get_church_donations(
    church_id: int, page: int = 1, limit: int = 20, db: Optional[Session] = None
):
    """Get church donations with pagination"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        query = db.query(DonorPayout).filter(
            DonorPayout.church_id == church_id,
            DonorPayout.status == "completed",
        )
        total = query.count()
        donations = (
            query.order_by(DonorPayout.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        donations_data = []
        for donation in donations:
            user = db.query(User).filter_by(id=donation.user_id).first()
            donations_data.append(
                {
                    "id": donation.id,
                    "amount": float(donation.donation_amount),
                    "transaction_count": donation.plaid_transaction_count or 1,
                    "created_at": donation.created_at.isoformat(),
                    "processed_at": (
                        donation.processed_at.isoformat()
                        if donation.processed_at
                        else None
                    ),
                    "donor_name": (
                        f"{user.first_name} {user.last_name}" if user else "Unknown"
                    ),
                    "donor_email": user.email if user else None,
                }
            )

        return ResponseFactory.success(
            message="Church donations retrieved successfully",
            data={
                "donations": donations_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit,
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to retrieve church donations"
        )
