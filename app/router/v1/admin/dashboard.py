"""
Comprehensive Dashboard Router

Provides comprehensive dashboard functionality for internal admin:
- Real-time platform metrics
- Advanced analytics and insights
- System health monitoring
- Business intelligence features
- Payout management and scheduling
- Donor analytics and patterns
- Church performance tracking
- Financial metrics and reporting
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone, timedelta

from app.utils.database import get_db
from app.middleware.admin_auth import admin_auth
from app.core.responses import ResponseFactory
from app.controller.admin.dashboard import (
    get_dashboard_overview,
    get_realtime_metrics,
    get_payout_management_data,
    get_donor_analytics,
    get_church_performance_analytics,
    get_system_health_metrics,
    get_system_alerts
)
from app.services.donor_schedule_service import DonorScheduleService

router = APIRouter(tags=["Dashboard"])


@router.get("/overview")
async def get_dashboard_overview_endpoint(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user = Depends(admin_auth)
):
    """Get comprehensive dashboard overview with all platform metrics, financial data, growth analytics, and system health"""
    return get_dashboard_overview(start_date, end_date, db)


@router.get("/realtime")
async def get_realtime_metrics_endpoint(
    db: Session = Depends(get_db),
    current_user = Depends(admin_auth)
):
    """Get real-time system and business metrics including processing rates and error monitoring"""
    return get_realtime_metrics(db)


@router.get("/payouts")
async def get_payout_management_endpoint(
    db: Session = Depends(get_db),
    current_user = Depends(admin_auth)
):
    """Get comprehensive payout management data including pending payouts, history, and next payout scheduling"""
    return get_payout_management_data(db)


@router.get("/payout-countdown")
async def get_payout_countdown_endpoint(
    db: Session = Depends(get_db),
    current_user = Depends(admin_auth)
):
    """Get real-time payout countdown information"""
    try:
        from app.controller.admin.dashboard import calculate_next_payout_date
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc)
        next_payout_date = calculate_next_payout_date()
        
        # Calculate time remaining
        time_diff = next_payout_date - now
        total_seconds = int(time_diff.total_seconds())
        
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return ResponseFactory.success(
            message="Payout countdown retrieved successfully",
            data={
                "next_payout_date": next_payout_date.isoformat(),
                "current_time": now.isoformat(),
                "time_remaining": {
                    "total_seconds": total_seconds,
                    "days": days,
                    "hours": hours,
                    "minutes": minutes,
                    "seconds": seconds
                },
                "formatted_time_remaining": f"{days}d {hours}h {minutes}m" if days > 0 else f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m",
                "is_overdue": total_seconds < 0
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/donor-analytics")
async def get_donor_analytics_endpoint(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user = Depends(admin_auth)
):
    """Get comprehensive donor analytics including patterns, top donors, and donation behaviors"""
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    return get_donor_analytics(db, start_dt, end_dt)


@router.get("/church-performance")
async def get_church_performance_endpoint(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user = Depends(admin_auth)
):
    """Get comprehensive church performance analytics including KYC status, revenue metrics, and growth tracking"""
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    return get_church_performance_analytics(db, start_dt, end_dt)


@router.get("/system-health")
async def get_system_health_endpoint(
    db: Session = Depends(get_db),
    current_user = Depends(admin_auth)
):
    """Get comprehensive system health metrics including performance, error rates, and resource utilization"""
    return ResponseFactory.success(
        message="System health metrics retrieved successfully",
        data=get_system_health_metrics(db)
    )


@router.get("/alerts")
async def get_system_alerts_endpoint(
    db: Session = Depends(get_db),
    current_user = Depends(admin_auth)
):
    """Get system alerts and notifications for monitoring and issue detection"""
    return ResponseFactory.success(
        message="System alerts retrieved successfully",
        data=get_system_alerts(db)
    )


@router.get("/daily-donations")
async def get_daily_donations_endpoint(
    target_date: Optional[str] = Query(None, description="Target date (YYYY-MM-DD), defaults to today"),
    db: Session = Depends(get_db),
    current_user = Depends(admin_auth)
):
    """Get daily donation summary including upcoming donors and estimated amounts"""
    try:
        target_dt = None
        if target_date:
            target_dt = datetime.fromisoformat(target_date)
        
        summary = DonorScheduleService.get_daily_donation_summary(db, target_dt)
        return ResponseFactory.success(
            message="Daily donation summary retrieved successfully",
            data=summary
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upcoming-donors")
async def get_upcoming_donors_endpoint(
    days_ahead: int = Query(7, description="Number of days to look ahead"),
    db: Session = Depends(get_db),
    current_user = Depends(admin_auth)
):
    """Get list of donors who will donate in the next N days"""
    try:
        upcoming_donors = DonorScheduleService.get_upcoming_donors(db, days_ahead)
        return ResponseFactory.success(
            message="Upcoming donors retrieved successfully",
            data={
                "days_ahead": days_ahead,
                "total_donors": len(upcoming_donors),
                "total_estimated_amount": round(sum(donor["estimated_amount"] for donor in upcoming_donors), 2),
                "donors": upcoming_donors
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tomorrow-donors")
async def get_tomorrow_donors_endpoint(
    db: Session = Depends(get_db),
    current_user = Depends(admin_auth)
):
    """Get list of donors who will donate tomorrow"""
    try:
        tomorrow = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        tomorrow_donors = DonorScheduleService.get_donors_due_for_donation(db, tomorrow)
        
        return ResponseFactory.success(
            message="Tomorrow's donors retrieved successfully",
            data={
                "date": tomorrow.strftime("%Y-%m-%d"),
                "total_donors": len(tomorrow_donors),
                "total_estimated_amount": round(sum(donor["estimated_amount"] for donor in tomorrow_donors), 2),
                "donors": tomorrow_donors
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
