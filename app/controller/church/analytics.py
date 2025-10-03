from fastapi import HTTPException
import logging
import traceback
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from sqlalchemy import func
from typing import Optional

from app.model.m_church import Church
from app.model.m_roundup_new import DonorPayout, ChurchPayout
from app.model.m_user import User
from app.core.responses import ResponseFactory


def get_church_analytics(
    church_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Optional[Session] = None,
):
    """Get comprehensive church analytics"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Query donor payouts for church analytics
        query = db.query(DonorPayout).filter(
            DonorPayout.church_id == church_id, DonorPayout.status == "completed"
        )

        if start_date:
            query = query.filter(DonorPayout.created_at >= start_date)
        if end_date:
            query = query.filter(DonorPayout.created_at <= end_date)

        donor_payouts = query.all()

        # Calculate totals from donor payouts
        total_revenue = sum(float(d.net_amount) for d in donor_payouts)
        donation_count = len(donor_payouts)
        avg_donation = total_revenue / donation_count if donation_count > 0 else 0.0
        total_transactions = sum(d.transaction_count for d in donor_payouts)

        # Daily breakdown
        daily_data = {}
        for payout in donor_payouts:
            day_key = payout.created_at.strftime("%Y-%m-%d")
            if day_key not in daily_data:
                daily_data[day_key] = {"amount": 0.0, "count": 0, "transactions": 0}

            daily_data[day_key]["amount"] += float(payout.net_amount)
            daily_data[day_key]["count"] += 1
            daily_data[day_key]["transactions"] += payout.transaction_count

        sorted_daily = sorted(daily_data.items(), key=lambda x: x[0])

        return ResponseFactory.success(
            message="Church analytics retrieved successfully",
            data={
                "overview": {
                    "total_revenue": round(float(total_revenue), 2),
                    "donation_count": donation_count,
                    "average_donation": round(float(avg_donation), 2),
                    "unique_givers": len(set(d.user_id for d in donor_payouts)),
                    "total_transactions": total_transactions,
                },
                "daily_breakdown": [
                    {
                        "date": date,
                        "amount": round(data["amount"], 2),
                        "count": data["count"],
                        "transactions": data["transactions"],
                    }
                    for date, data in sorted_daily
                ],
                "date_range": {"start_date": start_date, "end_date": end_date},
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to get analytics")


def get_donor_analytics(church_id: int, db: Session):
    """Get donor-specific analytics"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Get donor statistics from donor payouts
        donor_stats = (
            db.query(
                DonorPayout.user_id,
                func.sum(DonorPayout.net_amount).label("total_donated"),
                func.count(DonorPayout.id).label("payout_count"),
                func.avg(DonorPayout.net_amount).label("avg_payout"),
                func.sum(DonorPayout.transaction_count).label("total_transactions"),
            )
            .filter(
                DonorPayout.church_id == church_id, DonorPayout.status == "completed"
            )
            .group_by(DonorPayout.user_id)
            .all()
        )

        total_donors = len(donor_stats)
        total_amount = sum(float(stat.total_donated) for stat in donor_stats)
        avg_donor_amount = total_amount / total_donors if total_donors > 0 else 0.0

        # Top donors
        top_donors = sorted(
            donor_stats, key=lambda x: float(x.total_donated), reverse=True
        )[:10]
        top_donors_data = []
        for donor in top_donors:
            user = db.query(User).filter(User.id == donor.user_id).first()
            top_donors_data.append(
                {
                    "user_id": donor.user_id,
                    "name": (
                        f"{user.first_name} {user.last_name}" if user else "Anonymous"
                    ),
                    "total_donated": float(donor.total_donated),
                    "payout_count": donor.payout_count,
                    "avg_payout": float(donor.avg_payout),
                    "total_transactions": donor.total_transactions,
                }
            )

        return ResponseFactory.success(
            message="Donor analytics retrieved successfully",
            data={
                "total_donors": total_donors,
                "total_amount": round(float(total_amount), 2),
                "average_donor_amount": round(float(avg_donor_amount), 2),
                "top_donors": top_donors_data,
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to get donor analytics")


def get_revenue_analytics(
    church_id: int, period: str = "month", db: Optional[Session] = None
):
    """Get revenue analytics by period"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Calculate date range based on period
        now = datetime.now(timezone.utc)
        if period == "week":
            start_date = now.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - timedelta(days=7)
        elif period == "month":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == "year":
            start_date = now.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
        else:
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        donor_payouts = (
            db.query(DonorPayout)
            .filter(
                DonorPayout.church_id == church_id,
                DonorPayout.status == "completed",
                DonorPayout.created_at >= start_date,
            )
            .all()
        )

        total_revenue = sum(float(d.net_amount) for d in donor_payouts)
        payout_count = len(donor_payouts)
        avg_payout = total_revenue / payout_count if payout_count > 0 else 0.0

        # Period breakdown
        if period == "week":
            group_format = "%Y-%m-%d"
        elif period == "month":
            group_format = "%Y-%m-%d"
        elif period == "year":
            group_format = "%Y-%m"
        else:
            group_format = "%Y-%m-%d"

        period_data = {}
        for payout in donor_payouts:
            period_key = payout.created_at.strftime(group_format)
            if period_key not in period_data:
                period_data[period_key] = {"amount": 0.0, "count": 0, "transactions": 0}

            period_data[period_key]["amount"] += float(payout.net_amount)
            period_data[period_key]["count"] += 1
            period_data[period_key]["transactions"] += payout.transaction_count

        sorted_period = sorted(period_data.items(), key=lambda x: x[0])

        return ResponseFactory.success(
            message="Revenue analytics retrieved successfully",
            data={
                "period": period,
                "total_revenue": round(float(total_revenue), 2),
                "payout_count": payout_count,
                "average_payout": round(float(avg_payout), 2),
                "period_breakdown": [
                    {
                        "period": period_key,
                        "amount": round(data["amount"], 2),
                        "count": data["count"],
                        "transactions": data["transactions"],
                    }
                    for period_key, data in sorted_period
                ],
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to get revenue analytics")


def get_giving_patterns(church_id: int, db: Session):
    """Get giving patterns analysis"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        donor_payouts = (
            db.query(DonorPayout)
            .filter(
                DonorPayout.church_id == church_id, DonorPayout.status == "completed"
            )
            .all()
        )

        # Day of week analysis
        day_of_week_data = {}
        for payout in donor_payouts:
            day = payout.created_at.strftime("%A")
            if day not in day_of_week_data:
                day_of_week_data[day] = {"amount": 0.0, "count": 0}

            day_of_week_data[day]["amount"] += float(payout.net_amount)
            day_of_week_data[day]["count"] += 1

        # Hour of day analysis
        hour_of_day_data = {}
        for payout in donor_payouts:
            hour = payout.created_at.hour
            if hour not in hour_of_day_data:
                hour_of_day_data[hour] = {"amount": 0.0, "count": 0}

            hour_of_day_data[hour]["amount"] += float(payout.net_amount)
            hour_of_day_data[hour]["count"] += 1

        # Amount range analysis
        amount_ranges = {
            "0-10": {"min": 0, "max": 10, "amount": 0.0, "count": 0},
            "10-25": {"min": 10, "max": 25, "amount": 0.0, "count": 0},
            "25-50": {"min": 25, "max": 50, "amount": 0.0, "count": 0},
            "50-100": {"min": 50, "max": 100, "amount": 0.0, "count": 0},
            "100+": {"min": 100, "max": float("inf"), "amount": 0.0, "count": 0},
        }

        for payout in donor_payouts:
            amount = float(payout.net_amount)
            for range_key, range_data in amount_ranges.items():
                if range_data["min"] <= amount < range_data["max"]:
                    range_data["amount"] += amount
                    range_data["count"] += 1
                    break

        return ResponseFactory.success(
            message="Giving patterns retrieved successfully",
            data={
                "day_of_week": [
                    {
                        "day": day,
                        "amount": round(data["amount"], 2),
                        "count": data["count"],
                    }
                    for day, data in day_of_week_data.items()
                ],
                "hour_of_day": [
                    {
                        "hour": hour,
                        "amount": round(data["amount"], 2),
                        "count": data["count"],
                    }
                    for hour, data in sorted(hour_of_day_data.items())
                ],
                "amount_ranges": [
                    {
                        "range": range_key,
                        "amount": round(data["amount"], 2),
                        "count": data["count"],
                    }
                    for range_key, data in amount_ranges.items()
                ],
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to get giving patterns")


def get_performance_metrics(church_id: int, db: Session):
    """Get performance metrics including growth calculations"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        now = datetime.now(timezone.utc)

        # Current month
        current_month_start = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        current_month_end = (current_month_start + timedelta(days=32)).replace(
            day=1
        ) - timedelta(days=1)

        # Previous month
        prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        prev_month_end = current_month_start - timedelta(days=1)

        # Current month data
        current_month_payouts = (
            db.query(DonorPayout)
            .filter(
                DonorPayout.church_id == church_id,
                DonorPayout.status == "completed",
                DonorPayout.created_at >= current_month_start,
                DonorPayout.created_at <= current_month_end,
            )
            .all()
        )

        current_month_amount = sum(float(d.net_amount) for d in current_month_payouts)
        current_month_donors = len(set(d.user_id for d in current_month_payouts))

        # Previous month data
        prev_month_payouts = (
            db.query(DonorPayout)
            .filter(
                DonorPayout.church_id == church_id,
                DonorPayout.status == "completed",
                DonorPayout.created_at >= prev_month_start,
                DonorPayout.created_at <= prev_month_end,
            )
            .all()
        )

        prev_month_amount = sum(float(d.net_amount) for d in prev_month_payouts)
        prev_month_donors = len(set(d.user_id for d in prev_month_payouts))

        # Calculate growth percentages
        revenue_growth = 0.0
        if prev_month_amount > 0:
            revenue_growth = (
                (current_month_amount - prev_month_amount) / prev_month_amount
            ) * 100

        donor_growth = 0.0
        if prev_month_donors > 0:
            donor_growth = (
                (current_month_donors - prev_month_donors) / prev_month_donors
            ) * 100

        return ResponseFactory.success(
            message="Performance metrics retrieved successfully",
            data={
                "current_month": {
                    "revenue": round(float(current_month_amount), 2),
                    "donors": current_month_donors,
                    "payouts": len(current_month_payouts),
                },
                "previous_month": {
                    "revenue": round(float(prev_month_amount), 2),
                    "donors": prev_month_donors,
                    "payouts": len(prev_month_payouts),
                },
                "growth": {
                    "revenue_percentage": round(revenue_growth, 1),
                    "donor_percentage": round(donor_growth, 1),
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to get performance metrics")


def get_impact_story_analytics(church_id: int, db: Session):
    """Get impact story analytics for dashboard"""
    try:
        from app.model.m_impact_story import ImpactStory

        # Get all active impact stories for the church
        stories = (
            db.query(ImpactStory)
            .filter(ImpactStory.church_id == church_id, ImpactStory.is_active == True)
            .all()
        )

        if not stories:
            return {
                "total_stories": 0,
                "total_impact": 0.0,
                "monthly_stories": 0,
                "engagement_rate": 0.0,
                "avg_story_views": 0,
                "conversion_rate": 0.0,
                "top_category": "No stories",
                "monthly_growth": 0.0,
                "recent_stories": [],
            }

        # Calculate current month boundaries
        current_month_start = datetime.now(timezone.utc).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        current_month_end = datetime.now(timezone.utc)
        prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

        # Basic metrics
        total_stories = len(stories)
        total_impact = sum(float(story.amount_used) for story in stories)

        # Monthly stories
        monthly_stories = len(
            [s for s in stories if s.created_at >= current_month_start]
        )
        prev_month_stories = len(
            [
                s
                for s in stories
                if prev_month_start <= s.created_at < current_month_start
            ]
        )

        # Calculate growth
        monthly_growth = 0.0
        if prev_month_stories > 0:
            monthly_growth = (
                (monthly_stories - prev_month_stories) / prev_month_stories
            ) * 100

        # Category analysis
        categories = {}
        for story in stories:
            cat = story.category or "other"
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1

        top_category = (
            max(categories.items(), key=lambda x: x[1])[0]
            if categories
            else "No stories"
        )

        # Engagement metrics (mock for now - would need real tracking)
        engagement_rate = 85.0  # This should come from real analytics
        avg_story_views = 156  # This should come from real analytics
        conversion_rate = 23.5  # This should come from real analytics

        # Recent stories
        recent_stories = []
        for story in sorted(stories, key=lambda x: x.created_at, reverse=True)[:5]:
            recent_stories.append(
                {
                    "id": story.id,
                    "title": story.title,
                    "amount_used": float(story.amount_used),
                    "category": story.category,
                    "created_at": story.created_at.isoformat(),
                    "status": story.status,
                }
            )

        return {
            "total_stories": total_stories,
            "total_impact": round(float(total_impact), 2),
            "monthly_stories": monthly_stories,
            "engagement_rate": engagement_rate,
            "avg_story_views": avg_story_views,
            "conversion_rate": conversion_rate,
            "top_category": top_category,
            "monthly_growth": round(float(monthly_growth), 1),
            "recent_stories": recent_stories,
        }

    except Exception as e:

        return {
            "total_stories": 0,
            "total_impact": 0.0,
            "monthly_stories": 0,
            "engagement_rate": 0.0,
            "avg_story_views": 0,
            "conversion_rate": 0.0,
            "top_category": "Error",
            "monthly_growth": 0.0,
            "recent_stories": [],
        }


def get_promotional_analytics(church_id: int, db: Session):
    """Get promotional content analytics for dashboard"""
    try:
        # For now, we'll return analytics based on available data
        # In the future, this could track actual promotional content usage

        # Get church data to calculate some metrics
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            return {
                "total_downloads": 0,
                "content_views": 0,
                "shares_generated": 0,
                "conversion_rate": 0.0,
                "active_users": 0,
                "monthly_growth": 0.0,
                "top_content_type": "No data",
                "peak_usage_time": "No data",
            }

        # Get user count for this church
        from app.model.m_user import User

        total_users = (
            db.query(func.count(User.id))
            .filter(User.church_id == church_id, User.role == "donor")
            .scalar()
            or 0
        )

        # Get active users (users with donation preferences or transactions)
        from app.model.m_donation_preference import DonationPreference
        # TransactionStatus and TransactionType enums removed - using DonationBatch status instead
        from app.model.m_roundup_new import DonorPayout

        active_users = (
            db.query(func.count(func.distinct(User.id)))
            .join(DonationPreference, User.id == DonationPreference.user_id)
            .filter(User.church_id == church_id, DonationPreference.pause == False)
            .scalar()
            or 0
        )

        # Calculate some promotional metrics based on available data
        # These would ideally come from actual promotional content tracking

        # Estimate content views based on active users
        content_views = (
            active_users * 3
        )  # Assume each active user views 3 pieces of content

        # Estimate downloads based on active users
        total_downloads = int(
            active_users * 0.6
        )  # Assume 60% of active users download resources

        # Estimate shares based on active users
        shares_generated = int(
            active_users * 0.3
        )  # Assume 30% of active users share content

        # Calculate conversion rate (views to action)
        conversion_rate = 0.0
        if content_views > 0:
            conversion_rate = (total_downloads / content_views) * 100

        # Calculate monthly growth (mock for now)
        monthly_growth = 12.5  # This should come from real analytics

        # Determine top content type based on church activity
        if active_users > 0:
            if total_downloads > shares_generated:
                top_content_type = "Downloadable Resources"
            else:
                top_content_type = "Social Media Content"
        else:
            top_content_type = "No active users"

        # Determine peak usage time based on church type
        peak_usage_time = "Sunday AM"  # This should come from real analytics

        return {
            "total_downloads": total_downloads,
            "content_views": content_views,
            "shares_generated": shares_generated,
            "conversion_rate": round(conversion_rate, 1),
            "active_users": active_users,
            "monthly_growth": monthly_growth,
            "top_content_type": top_content_type,
            "peak_usage_time": peak_usage_time,
        }

    except Exception as e:

        return {
            "total_downloads": 0,
            "content_views": 0,
            "shares_generated": 0,
            "conversion_rate": 0.0,
            "active_users": 0,
            "monthly_growth": 0.0,
            "top_content_type": "Error",
            "peak_usage_time": "Error",
        }
