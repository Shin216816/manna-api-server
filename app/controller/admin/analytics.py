"""
Admin Analytics Controller

Handles admin platform analytics functionality:
- Platform overview metrics
- Growth trends and reporting
- Revenue analytics
- User and church metrics
"""

from fastapi import HTTPException
import logging
import traceback
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.model.m_user import User
from app.model.m_church import Church
from app.model.m_donation_batch import DonationBatch
from app.model.m_donation_preference import DonationPreference
from app.model.m_church_referral import ChurchReferral
from app.model.m_referral import ReferralCommission
from app.model.m_roundup_new import ChurchPayout, DonorPayout
from app.core.responses import ResponseFactory


def get_church_statistics(db: Session):
    """Get comprehensive church statistics and insights"""
    try:
        # Total churches
        total_churches = db.query(func.count(Church.id)).scalar()
        
        # Churches by status
        status_breakdown = db.query(
            Church.status,
            func.count(Church.id).label('count')
        ).group_by(Church.status).all()
        
        # Churches by KYC status
        kyc_breakdown = db.query(
            Church.kyc_status,
            func.count(Church.id).label('count')
        ).group_by(Church.kyc_status).all()
        
        # Active vs inactive
        active_churches = db.query(func.count(Church.id)).filter(Church.is_active == True).scalar()
        inactive_churches = total_churches - active_churches
        
        # Revenue statistics
        total_revenue = db.query(func.sum(DonationBatch.amount)).filter(
            DonationBatch.status == "completed"
        ).scalar() or 0.0
        
        # Average revenue per church
        avg_revenue_per_church = total_revenue / total_churches if total_churches > 0 else 0
        
        # Top performing churches (by revenue)
        top_churches = db.query(
            Church.name,
            Church.id,
            func.sum(DonationBatch.amount).label('total_revenue'),
            func.count(DonationBatch.id).label('donation_count')
        ).join(DonationBatch, Church.id == DonationBatch.church_id).filter(
            DonationBatch.status == "completed"
        ).group_by(Church.id, Church.name).order_by(
            func.sum(DonationBatch.amount).desc()
        ).limit(10).all()
        
        # Growth trends (last 6 months)
        six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
        monthly_growth = []
        
        for i in range(6):
            month_start = six_months_ago + timedelta(days=i * 30)
            month_end = month_start + timedelta(days=30)
            
            churches_this_month = db.query(func.count(Church.id)).filter(
                Church.created_at >= month_start,
                Church.created_at < month_end
            ).scalar()
            
            monthly_growth.append({
                'month': month_start.strftime('%Y-%m'),
                'new_churches': churches_this_month
            })
        
        return ResponseFactory.success(
            message="Church statistics retrieved successfully",
            data={
                "overview": {
                    "total_churches": total_churches,
                    "active_churches": active_churches,
                    "inactive_churches": inactive_churches,
                    "total_revenue": round(float(total_revenue), 2),
                    "avg_revenue_per_church": round(float(avg_revenue_per_church), 2)
                },
                "status_breakdown": {
                    status: count for status, count in status_breakdown
                },
                "kyc_breakdown": {
                    kyc_status: count for kyc_status, count in kyc_breakdown
                },
                "top_churches": [
                    {
                        "name": name,
                        "id": church_id,
                        "total_revenue": round(float(revenue), 2),
                        "donation_count": count
                    }
                    for name, church_id, revenue, count in top_churches
                ],
                "monthly_growth": monthly_growth
            }
        )
        
    except Exception as e:
        logging.error(f"Error getting church statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve church statistics")


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse date string to datetime object"""
    if not date_str:
        return None

    try:
        # Try parsing as YYYY-MM-DD format
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            # Try parsing as ISO format
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
            )


def get_platform_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
    db: Optional[Session] = None,
):
    """Get platform-wide analytics"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database session is required")

        # Parse dates or calculate from period
        if period and not start_date and not end_date:
            # Calculate date range based on period
            now = datetime.now(timezone.utc)
            if period == "week":
                start_dt = now - timedelta(days=7)
                end_dt = now
            elif period == "month":
                start_dt = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end_dt = now
            elif period == "year":
                start_dt = now.replace(
                    month=1, day=1, hour=0, minute=0, second=0, microsecond=0
                )
                end_dt = now
            else:
                start_dt = None
                end_dt = None
        else:
            # Use provided dates
            start_dt = parse_date(start_date)
            end_dt = parse_date(end_date)

        # Get total users
        total_users = db.query(func.count(User.id)).scalar()
        active_users = (
            db.query(func.count(User.id)).filter(User.is_active == True).scalar()
        )

        # Get total churches
        total_churches = db.query(func.count(Church.id)).scalar()
        active_churches = (
            db.query(func.count(Church.id)).filter(Church.is_active == True).scalar()
        )

        # Get total donations from DonorPayout (current system)
        donation_query = db.query(func.sum(DonorPayout.donation_amount)).filter(
            DonorPayout.status == "completed"
        )
        if start_dt:
            donation_query = donation_query.filter(DonorPayout.created_at >= start_dt)
        if end_dt:
            donation_query = donation_query.filter(DonorPayout.created_at <= end_dt)

        total_donations = float(donation_query.scalar() or 0)

        # Get donation count from DonorPayout
        count_query = db.query(func.count(DonorPayout.id)).filter(
            DonorPayout.status == "completed"
        )
        if start_dt:
            count_query = count_query.filter(DonorPayout.created_at >= start_dt)
        if end_dt:
            count_query = count_query.filter(DonorPayout.created_at <= end_dt)

        donation_count = count_query.scalar()

        # Get this month's data
        current_month = datetime.now(timezone.utc).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        this_month_users = (
            db.query(func.count(User.id))
            .filter(User.created_at >= current_month)
            .scalar()
        )
        this_month_churches = (
            db.query(func.count(Church.id))
            .filter(Church.created_at >= current_month)
            .scalar()
        )
        this_month_donations = float(
            db.query(func.sum(DonorPayout.donation_amount))
            .filter(
                DonorPayout.status == "completed",
                DonorPayout.created_at >= current_month,
            )
            .scalar() or 0
        )

        # Get active donors
        active_donors = (
            db.query(func.count(User.id.distinct()))
            .join(DonationPreference)
            .filter(DonationPreference.pause == False)
            .scalar()
        )

        return ResponseFactory.success(
            message="Platform analytics retrieved successfully",
            data={
                "total_gmv": round(float(total_donations or 0), 2),
                "total_revenue": round(
                    float(total_donations or 0) * 0.05, 2
                ),  # Assuming 5% platform fee
                "active_users": active_users,
                "total_churches": total_churches,
                "total_users": total_users,
                "active_churches": active_churches,
                "donation_count": donation_count,
                "this_month_users": this_month_users,
                "this_month_churches": this_month_churches,
                "this_month_donations": round(float(this_month_donations), 2),
                "active_donors": active_donors,
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to retrieve platform analytics"
        )


def get_revenue_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Optional[Session] = None,
):
    """Get revenue analytics"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database session is required")

        # Parse dates
        start_dt = parse_date(start_date)
        end_dt = parse_date(end_date)

        # Build query for donations from DonorPayout (current system)
        query = db.query(DonorPayout).filter(DonorPayout.status == "completed")

        if start_dt:
            query = query.filter(DonorPayout.created_at >= start_dt)
        if end_dt:
            query = query.filter(DonorPayout.created_at <= end_dt)

        donations = query.all()

        # Calculate revenue metrics
        total_revenue = sum(float(d.donation_amount or 0) for d in donations)
        donation_count = len(donations)
        avg_donation = total_revenue / donation_count if donation_count > 0 else 0.0

        # Monthly breakdown
        monthly_data = {}
        for donation in donations:
            month_key = donation.created_at.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {"amount": 0.0, "count": 0}
            monthly_data[month_key]["amount"] += float(donation.donation_amount)
            monthly_data[month_key]["count"] += 1

        sorted_monthly = sorted(monthly_data.items(), key=lambda x: x[0])

        # Top churches by revenue from DonorPayout
        church_revenue_query = (
            db.query(
                Church.name,
                func.sum(DonorPayout.donation_amount).label("total_revenue"),
                func.count(DonorPayout.id).label("donation_count"),
            )
            .join(DonorPayout)
            .filter(DonorPayout.status == "completed")
        )

        if start_dt:
            church_revenue_query = church_revenue_query.filter(
                DonorPayout.created_at >= start_dt
            )
        if end_dt:
            church_revenue_query = church_revenue_query.filter(
                DonorPayout.created_at <= end_dt
            )

        church_revenue = (
            church_revenue_query.group_by(Church.id, Church.name)
            .order_by(func.sum(DonorPayout.donation_amount).desc())
            .limit(10)
            .all()
        )

        return ResponseFactory.success(
            message="Revenue analytics retrieved successfully",
            data={
                "revenue": {
                    "total": round(float(total_revenue), 2),
                    "count": donation_count,
                    "average": round(float(avg_donation), 2),
                },
                "monthly_breakdown": [
                    {
                        "month": month,
                        "amount": round(data["amount"], 2),
                        "count": data["count"],
                    }
                    for month, data in sorted_monthly
                ],
                "top_churches": [
                    {
                        "name": name,
                        "total_revenue": round(float(revenue or 0), 2),
                        "donation_count": count,
                    }
                    for name, revenue, count in church_revenue
                ],
                "date_range": {"start_date": start_date, "end_date": end_date},
            },
        )

    except Exception as e:

        raise HTTPException(
            status_code=500, detail="Failed to retrieve revenue analytics"
        )


def get_user_growth_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Optional[Session] = None,
):
    """Get user growth analytics"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database session is required")

        # Parse dates
        start_dt = parse_date(start_date)
        end_dt = parse_date(end_date)

        # Get user growth over time
        if start_dt and end_dt:
            users = (
                db.query(User)
                .filter(User.created_at >= start_dt, User.created_at <= end_dt)
                .all()
            )
        else:
            # Get last 12 months by default
            end_dt = datetime.now(timezone.utc)
            start_dt = end_dt - timedelta(days=365)
            users = (
                db.query(User)
                .filter(User.created_at >= start_dt, User.created_at <= end_dt)
                .all()
            )

        # Monthly user growth
        monthly_growth = {}
        for user in users:
            month_key = user.created_at.strftime("%Y-%m")
            if month_key not in monthly_growth:
                monthly_growth[month_key] = 0
            monthly_growth[month_key] += 1

        sorted_growth = sorted(monthly_growth.items(), key=lambda x: x[0])

        # Calculate growth rate
        if len(sorted_growth) >= 2:
            current_month = sorted_growth[-1][1]
            previous_month = sorted_growth[-2][1]
            growth_rate = (
                ((current_month - previous_month) / previous_month * 100)
                if previous_month > 0
                else 0
            )
        else:
            growth_rate = 0

        return ResponseFactory.success(
            message="User growth analytics retrieved successfully",
            data={
                "total_users": len(users),
                "growth_rate": round(growth_rate, 2),
                "monthly_growth": [
                    {"month": month, "new_users": count}
                    for month, count in sorted_growth
                ],
                "date_range": {
                    "start_date": start_dt.isoformat() if start_dt else start_date,
                    "end_date": end_dt.isoformat() if end_dt else end_date,
                },
            },
        )

    except Exception as e:

        raise HTTPException(
            status_code=500, detail="Failed to retrieve user growth analytics"
        )


def get_church_growth_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Optional[Session] = None,
):
    """Get church growth analytics"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database session is required")

        # Parse dates
        start_dt = parse_date(start_date)
        end_dt = parse_date(end_date)

        # Get church growth over time
        if start_dt and end_dt:
            churches = (
                db.query(Church)
                .filter(Church.created_at >= start_dt, Church.created_at <= end_dt)
                .all()
            )
        else:
            # Get last 12 months by default
            end_dt = datetime.now(timezone.utc)
            start_dt = end_dt - timedelta(days=365)
            churches = (
                db.query(Church)
                .filter(Church.created_at >= start_dt, Church.created_at <= end_dt)
                .all()
            )

        # Monthly church growth
        monthly_growth = {}
        for church in churches:
            month_key = church.created_at.strftime("%Y-%m")
            if month_key not in monthly_growth:
                monthly_growth[month_key] = 0
            monthly_growth[month_key] += 1

        sorted_growth = sorted(monthly_growth.items(), key=lambda x: x[0])

        # Calculate growth rate
        if len(sorted_growth) >= 2:
            current_month = sorted_growth[-1][1]
            previous_month = sorted_growth[-2][1]
            growth_rate = (
                ((current_month - previous_month) / previous_month * 100)
                if previous_month > 0
                else 0
            )
        else:
            growth_rate = 0

        return ResponseFactory.success(
            message="Church growth analytics retrieved successfully",
            data={
                "total_churches": len(churches),
                "growth_rate": round(growth_rate, 2),
                "monthly_growth": [
                    {"month": month, "new_churches": count}
                    for month, count in sorted_growth
                ],
                "date_range": {
                    "start_date": start_dt.isoformat() if start_dt else start_date,
                    "end_date": end_dt.isoformat() if end_dt else end_date,
                },
            },
        )

    except Exception as e:

        raise HTTPException(
            status_code=500, detail="Failed to retrieve church growth analytics"
        )


def get_donation_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Optional[Session] = None,
):
    """Get donation analytics"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database session is required")

        # Parse dates
        start_dt = parse_date(start_date)
        end_dt = parse_date(end_date)

        # Build query for donations from DonorPayout (current system)
        query = db.query(DonorPayout).filter(DonorPayout.status == "completed")

        if start_dt:
            query = query.filter(DonorPayout.created_at >= start_dt)
        if end_dt:
            query = query.filter(DonorPayout.created_at <= end_dt)

        donations = query.all()

        # Calculate donation metrics
        total_amount = sum(float(d.donation_amount or 0) for d in donations)
        donation_count = len(donations)
        avg_donation = total_amount / donation_count if donation_count > 0 else 0.0

        # Monthly donation breakdown
        monthly_data = {}
        for donation in donations:
            month_key = donation.created_at.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {"amount": 0.0, "count": 0}
            monthly_data[month_key]["amount"] += float(donation.donation_amount)
            monthly_data[month_key]["count"] += 1

        sorted_monthly = sorted(monthly_data.items(), key=lambda x: x[0])

        # Top donors from DonorPayout
        top_donors_query = (
            db.query(
                User.first_name,
                User.last_name,
                func.sum(DonorPayout.donation_amount).label("total_donated"),
                func.count(DonorPayout.id).label("donation_count"),
            )
            .join(DonorPayout)
            .filter(DonorPayout.status == "completed")
        )

        if start_dt:
            top_donors_query = top_donors_query.filter(
                DonorPayout.created_at >= start_dt
            )
        if end_dt:
            top_donors_query = top_donors_query.filter(
                DonorPayout.created_at <= end_dt
            )

        top_donors = (
            top_donors_query.group_by(User.id, User.first_name, User.last_name)
            .order_by(func.sum(DonorPayout.donation_amount).desc())
            .limit(10)
            .all()
        )

        return ResponseFactory.success(
            message="Donation analytics retrieved successfully",
            data={
                "donations": {
                    "total_amount": round(float(total_amount), 2),
                    "count": donation_count,
                    "average": round(float(avg_donation), 2),
                },
                "monthly_breakdown": [
                    {
                        "month": month,
                        "amount": round(data["amount"], 2),
                        "count": data["count"],
                    }
                    for month, data in sorted_monthly
                ],
                "top_donors": [
                    {
                        "name": f"{first_name} {last_name}",
                        "total_donated": round(float(total_donated or 0), 2),
                        "donation_count": count,
                    }
                    for first_name, last_name, total_donated, count in top_donors
                ],
                "date_range": {"start_date": start_date, "end_date": end_date},
            },
        )

    except Exception as e:

        raise HTTPException(
            status_code=500, detail="Failed to retrieve donation analytics"
        )


def get_system_health_analytics(db: Session):
    """Get comprehensive system health analytics"""
    try:
        # System status overview
        total_churches = db.query(func.count(Church.id)).scalar()
        active_churches = db.query(func.count(Church.id)).filter(Church.is_active == True).scalar()
        
        # KYC status breakdown
        kyc_statuses = db.query(
            Church.kyc_status,
            func.count(Church.id).label('count')
        ).group_by(Church.kyc_status).all()
        
        # Church status breakdown
        church_statuses = db.query(
            Church.status,
            func.count(Church.id).label('count')
        ).group_by(Church.status).all()
        
        # Recent activity (last 7 days)
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_churches = db.query(func.count(Church.id)).filter(
            Church.created_at >= week_ago
        ).scalar()
        
        recent_users = db.query(func.count(User.id)).filter(
            User.created_at >= week_ago
        ).scalar()
        
        # Pending KYC applications
        pending_kyc = db.query(func.count(Church.id)).filter(
            Church.kyc_status.in_(['pending_review', 'under_review'])
        ).scalar()
        
        # System performance metrics from DonorPayout
        total_donations = float(db.query(func.sum(DonorPayout.donation_amount)).filter(
            DonorPayout.status == "completed"
        ).scalar() or 0)
        
        # Referral system health
        total_referrals = db.query(func.count(ChurchReferral.id)).scalar()
        active_referrals = db.query(func.count(ChurchReferral.id)).filter(
            ChurchReferral.status == "active"
        ).scalar()
        
        # Commission analytics
        total_commissions = db.query(func.sum(ReferralCommission.amount)).scalar() or 0.0
        
        return ResponseFactory.success(
            message="System health analytics retrieved successfully",
            data={
                "overview": {
                    "total_churches": total_churches,
                    "active_churches": active_churches,
                    "pending_kyc": pending_kyc,
                    "recent_churches_7d": recent_churches,
                    "recent_users_7d": recent_users,
                    "total_donations": round(float(total_donations), 2)
                },
                "kyc_breakdown": {
                    status: count for status, count in kyc_statuses
                },
                "church_status_breakdown": {
                    status: count for status, count in church_statuses
                },
                "referral_system": {
                    "total_referrals": total_referrals,
                    "active_referrals": active_referrals,
                    "total_commissions": round(float(total_commissions), 2)
                }
            }
        )
        
    except Exception as e:
        logging.error(f"Error getting system health analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system health analytics")


def get_operational_analytics(db: Session):
    """Get operational analytics including payouts, transactions, and errors"""
    try:
        # Payout analytics
        total_payouts = db.query(func.count(ChurchPayout.id)).scalar()
        completed_payouts = db.query(func.count(ChurchPayout.id)).filter(
            ChurchPayout.status == "completed"
        ).scalar()
        pending_payouts = db.query(func.count(ChurchPayout.id)).filter(
            ChurchPayout.status == "pending"
        ).scalar()
        
        total_payout_amount = db.query(func.sum(ChurchPayout.net_payout_amount)).filter(
            ChurchPayout.status == "completed"
        ).scalar() or 0.0
        
        # Donation analytics
        total_donations = db.query(func.count(DonorPayout.id)).scalar()
        completed_donations = db.query(func.count(DonorPayout.id)).filter(
            DonorPayout.status == "completed"
        ).scalar()
        
        total_donation_amount = db.query(func.sum(DonorPayout.donation_amount)).filter(
            DonorPayout.status == "completed"
        ).scalar() or 0.0
        
        # Recent activity (last 30 days)
        month_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_payouts = db.query(func.count(ChurchPayout.id)).filter(
            ChurchPayout.created_at >= month_ago
        ).scalar()
        
        recent_donations = db.query(func.count(DonorPayout.id)).filter(
            DonorPayout.created_at >= month_ago
        ).scalar()
        
        # Top performing churches by revenue
        top_churches = db.query(
            Church.name,
            Church.id,
            func.sum(ChurchPayout.net_payout_amount).label('total_payouts'),
            func.count(ChurchPayout.id).label('payout_count')
        ).join(ChurchPayout, Church.id == ChurchPayout.church_id).filter(
            ChurchPayout.status == "completed"
        ).group_by(Church.id, Church.name).order_by(
            func.sum(ChurchPayout.net_payout_amount).desc()
        ).limit(10).all()
        
        return ResponseFactory.success(
            message="Operational analytics retrieved successfully",
            data={
                "payouts": {
                    "total": total_payouts,
                    "completed": completed_payouts,
                    "pending": pending_payouts,
                    "total_amount": round(float(total_payout_amount), 2),
                    "recent_30d": recent_payouts
                },
                "donations": {
                    "total": total_donations,
                    "completed": completed_donations,
                    "total_amount": round(float(total_donation_amount), 2),
                    "recent_30d": recent_donations
                },
                "top_churches": [
                    {
                        "name": name,
                        "id": church_id,
                        "total_payouts": round(float(total_payouts or 0), 2),
                        "payout_count": payout_count
                    }
                    for name, church_id, total_payouts, payout_count in top_churches
                ]
            }
        )
        
    except Exception as e:
        logging.error(f"Error getting operational analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve operational analytics")


def get_financial_analytics_detailed(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Optional[Session] = None
):
    """Get detailed financial analytics with enhanced data for charts"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database session is required")
        
        # Parse dates
        start_dt = parse_date(start_date)
        end_dt = parse_date(end_date)
        
        # Get monthly revenue breakdown with more details
        monthly_query = db.query(
            func.date_trunc('month', DonorPayout.created_at).label('month'),
            func.sum(DonorPayout.donation_amount).label('amount'),
            func.count(DonorPayout.id).label('count'),
            func.avg(DonorPayout.donation_amount).label('avg_amount')
        ).filter(DonorPayout.status == "completed")
        
        if start_dt:
            monthly_query = monthly_query.filter(DonorPayout.created_at >= start_dt)
        if end_dt:
            monthly_query = monthly_query.filter(DonorPayout.created_at <= end_dt)
            
        monthly_data = monthly_query.group_by(
            func.date_trunc('month', DonorPayout.created_at)
        ).order_by('month').all()
        
        # Get church revenue performance
        church_revenue_query = db.query(
            Church.name,
            Church.id,
            func.sum(DonorPayout.donation_amount).label('total_revenue'),
            func.count(DonorPayout.id).label('donation_count'),
            func.avg(DonorPayout.donation_amount).label('avg_donation')
        ).join(DonorPayout).filter(DonorPayout.status == "completed")
        
        if start_dt:
            church_revenue_query = church_revenue_query.filter(DonorPayout.created_at >= start_dt)
        if end_dt:
            church_revenue_query = church_revenue_query.filter(DonorPayout.created_at <= end_dt)
            
        church_revenue = church_revenue_query.group_by(
            Church.id, Church.name
        ).order_by(func.sum(DonorPayout.donation_amount).desc()).limit(20).all()
        
        # Calculate growth rates
        monthly_breakdown = []
        for i, (month, amount, count, avg_amount) in enumerate(monthly_data):
            prev_amount = monthly_data[i-1][1] if i > 0 else 0
            growth_rate = ((amount - prev_amount) / prev_amount * 100) if prev_amount > 0 else 0
            
            monthly_breakdown.append({
                "month": month.strftime("%Y-%m"),
                "amount": float(amount or 0),
                "count": count or 0,
                "avg_amount": float(avg_amount or 0),
                "growth_rate": float(round(growth_rate, 2))
            })
        
        # Format church data
        church_breakdown = []
        for name, church_id, total_revenue, donation_count, avg_donation in church_revenue:
            church_breakdown.append({
                "name": name,
                "church_id": church_id,
                "total_revenue": float(total_revenue or 0),
                "donation_count": donation_count or 0,
                "avg_donation": float(avg_donation or 0)
            })
        
        return ResponseFactory.success(
            message="Detailed financial analytics retrieved successfully",
            data={
                "monthly_breakdown": monthly_breakdown,
                "church_breakdown": church_breakdown,
                "summary": {
                    "total_revenue": sum(item["amount"] for item in monthly_breakdown),
                    "total_transactions": sum(item["count"] for item in monthly_breakdown),
                    "avg_transaction": sum(item["amount"] for item in monthly_breakdown) / max(sum(item["count"] for item in monthly_breakdown), 1),
                    "total_churches": len(church_breakdown),
                    "top_church_revenue": church_breakdown[0]["total_revenue"] if church_breakdown else 0
                }
            }
        )
        
    except Exception as e:
        logging.error(f"Error getting detailed financial analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve detailed financial analytics")


def get_comprehensive_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Optional[Session] = None
):
    """Get comprehensive analytics combining all metrics"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database session is required")
        
        # Get all analytics data
        platform_data = get_platform_analytics(start_date, end_date, None, db)
        revenue_data = get_revenue_analytics(start_date, end_date, db)
        user_growth_data = get_user_growth_analytics(start_date, end_date, db)
        church_growth_data = get_church_growth_analytics(start_date, end_date, db)
        donation_data = get_donation_analytics(start_date, end_date, db)
        system_health_data = get_system_health_analytics(db)
        operational_data = get_operational_analytics(db)
        financial_detailed = get_financial_analytics_detailed(start_date, end_date, db)
        
        return ResponseFactory.success(
            message="Comprehensive analytics retrieved successfully",
            data={
                "platform": platform_data.data,
                "revenue": revenue_data.data,
                "user_growth": user_growth_data.data,
                "church_growth": church_growth_data.data,
                "donations": donation_data.data,
                "system_health": system_health_data.data,
                "operational": operational_data.data,
                "financial_detailed": financial_detailed.data,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logging.error(f"Error getting comprehensive analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve comprehensive analytics")
