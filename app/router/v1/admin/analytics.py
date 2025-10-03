from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.controller.admin.analytics import (
    get_platform_analytics, get_revenue_analytics, get_user_growth_analytics,
    get_church_growth_analytics, get_donation_analytics, get_system_health_analytics,
    get_operational_analytics, get_comprehensive_analytics, get_financial_analytics_detailed
)
from app.utils.database import get_db
from app.middleware.admin_auth import admin_auth
from app.core.responses import SuccessResponse

analytics_router = APIRouter(tags=["Platform Analytics"])

@analytics_router.get("/", response_model=SuccessResponse)
async def get_platform_analytics_route(
    period: str = Query(None, description="Analytics period: week, month, year"),
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get platform analytics"""
    return get_platform_analytics(start_date, end_date, period, db)

@analytics_router.get("/revenue", response_model=SuccessResponse)
async def get_revenue_analytics_route(
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get revenue analytics"""
    return get_revenue_analytics(start_date, end_date, db)

@analytics_router.get("/user-growth", response_model=SuccessResponse)
async def get_user_growth_route(
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get user growth analytics"""
    return get_user_growth_analytics(start_date, end_date, db)

@analytics_router.get("/church-growth", response_model=SuccessResponse)
async def get_church_growth_route(
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get church growth analytics"""
    return get_church_growth_analytics(start_date, end_date, db)

@analytics_router.get("/donations", response_model=SuccessResponse)
async def get_donation_analytics_route(
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get donation analytics"""
    return get_donation_analytics(start_date, end_date, db)

@analytics_router.get("/system-health", response_model=SuccessResponse)
async def get_system_health_route(
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get system health analytics"""
    return get_system_health_analytics(db)

@analytics_router.get("/operational", response_model=SuccessResponse)
async def get_operational_analytics_route(
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get operational analytics"""
    return get_operational_analytics(db)

@analytics_router.get("/financial-detailed", response_model=SuccessResponse)
async def get_financial_detailed_route(
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get detailed financial analytics with enhanced data for charts"""
    return get_financial_analytics_detailed(start_date, end_date, db)

@analytics_router.get("/comprehensive", response_model=SuccessResponse)
async def get_comprehensive_analytics_route(
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get comprehensive analytics combining all metrics"""
    return get_comprehensive_analytics(start_date, end_date, db)
