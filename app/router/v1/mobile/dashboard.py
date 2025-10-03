from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.controller.mobile.dashboard import get_mobile_dashboard
from app.controller.mobile.roundups import (
    get_mobile_enhanced_roundup_status, get_mobile_transactions, get_mobile_impact_summary
)
from app.controller.mobile.messages import get_mobile_notifications
from app.utils.database import get_db
from app.middleware.auth_middleware import jwt_auth
from app.core.responses import SuccessResponse

dashboard_router = APIRouter(tags=["Mobile Dashboard"])

@dashboard_router.get("/", response_model=SuccessResponse)
async def get_mobile_dashboard_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard for mobile"""
    return get_mobile_dashboard(current_user["id"], db)

@dashboard_router.get("/roundup-status", response_model=SuccessResponse)
async def get_roundup_status_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get roundup status for mobile dashboard"""
    return get_mobile_enhanced_roundup_status(current_user["id"], db)

@dashboard_router.get("/recent-transactions", response_model=SuccessResponse)
async def get_recent_transactions_route(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get recent transactions for mobile dashboard"""
    return get_mobile_transactions(current_user["id"], limit, db)

@dashboard_router.get("/donation-summary", response_model=SuccessResponse)
async def get_donation_summary_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get donation summary for mobile dashboard"""
    return get_mobile_impact_summary(current_user["id"], db)

@dashboard_router.get("/notifications", response_model=SuccessResponse)
async def get_dashboard_notifications_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get notifications for mobile dashboard"""
    return get_mobile_notifications(current_user["id"], db)

# Additional endpoints that tests expect
@dashboard_router.get("/summary", response_model=SuccessResponse)
async def get_dashboard_summary_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get dashboard summary for mobile (alias for main dashboard)"""
    return get_mobile_dashboard(current_user["id"], db)

@dashboard_router.get("/history", response_model=SuccessResponse)
async def get_dashboard_history_route(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get donation history for dashboard"""
    from app.controller.mobile.donations import get_mobile_donation_history
    return get_mobile_donation_history(current_user["id"], limit, db)

@dashboard_router.get("/impact", response_model=SuccessResponse)
async def get_dashboard_impact_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get impact summary for dashboard"""
    return get_mobile_impact_summary(current_user["id"], db)
