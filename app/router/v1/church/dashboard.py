from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.controller.church.dashboard import (
    get_church_dashboard, get_church_analytics, get_church_members, get_church_donations
)
from app.utils.database import get_db
from app.middleware.church_admin_auth import church_admin_auth
from app.core.responses import SuccessResponse

dashboard_router = APIRouter(tags=["Church Admin"])

@dashboard_router.get("/", response_model=SuccessResponse)
async def get_dashboard_route(
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """
    Get church dashboard
    
    Retrieves the main dashboard data for the church including
    key metrics, recent activity, and summary statistics.
    """
    return get_church_dashboard(current_user["church_id"], db, current_user)

@dashboard_router.get("/analytics", response_model=SuccessResponse)
async def get_analytics_route(
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """
    Get church analytics
    
    Retrieves detailed analytics and reporting data for the church
    within the specified date range.
    """
    return get_church_analytics(current_user["church_id"], start_date, end_date, db)

@dashboard_router.get("/members", response_model=SuccessResponse)
async def get_members_route(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get church members"""
    return get_church_members(current_user["church_id"], page, limit, db)

@dashboard_router.get("/donations", response_model=SuccessResponse)
async def get_donations_route(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get church donations"""
    return get_church_donations(current_user["church_id"], page, limit, db)
