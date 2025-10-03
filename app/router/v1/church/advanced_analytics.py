from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.controller.church.advanced_analytics import (
    get_donation_trends_analytics, get_spending_categories_analytics,
    get_top_merchants_analytics, get_growth_metrics_analytics
)
from app.utils.database import get_db
from app.middleware.church_admin_auth import church_admin_auth
from app.core.responses import SuccessResponse

router = APIRouter(tags=["Church Advanced Analytics"])


@router.get("/donation-trends", response_model=SuccessResponse)
async def get_donation_trends_route(
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    period: str = Query("monthly", description="Period: monthly or daily"),
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get comprehensive donation trends analytics"""
    return get_donation_trends_analytics(
        current_user["church_id"], start_date, end_date, period, db
    )


@router.get("/spending-categories", response_model=SuccessResponse)
async def get_spending_categories_route(
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(10, ge=1, le=50, description="Number of categories to return"),
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get spending categories analytics from donor transactions"""
    return get_spending_categories_analytics(
        current_user["church_id"], start_date, end_date, limit, db
    )


@router.get("/top-merchants", response_model=SuccessResponse)
async def get_top_merchants_route(
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(10, ge=1, le=50, description="Number of merchants to return"),
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get top merchants analytics from donor transactions"""
    return get_top_merchants_analytics(
        current_user["church_id"], start_date, end_date, limit, db
    )


@router.get("/growth-metrics", response_model=SuccessResponse)
async def get_growth_metrics_route(
    period: str = Query("monthly", description="Period: monthly or weekly"),
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get growth metrics and forecasting analytics"""
    return get_growth_metrics_analytics(current_user["church_id"], period, db)
