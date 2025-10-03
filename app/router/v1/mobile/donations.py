from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from app.controller.mobile.donations import (
    get_mobile_donation_history, get_mobile_donation_summary, get_mobile_impact_analytics
)
from app.controller.mobile.roundups import (
    get_mobile_impact_summary, get_mobile_roundup_settings, update_mobile_roundup_settings,
    get_mobile_pending_roundups, quick_toggle_roundups
)
from app.utils.database import get_db
from app.middleware.auth_middleware import jwt_auth
from app.core.responses import SuccessResponse

donations_router = APIRouter(tags=["Mobile Donations"])

@donations_router.get("/history", response_model=SuccessResponse)
async def get_donation_history_route(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get donation history for mobile"""
    return get_mobile_donation_history(current_user["id"], limit, db)

@donations_router.get("/summary", response_model=SuccessResponse)
async def get_donation_summary_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get donation summary for mobile"""
    return get_mobile_donation_summary(current_user["id"], db)

@donations_router.get("/impact", response_model=SuccessResponse)
async def get_donation_impact_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get donation impact for mobile"""
    return get_mobile_impact_summary(current_user["id"], db)

@donations_router.get("/dashboard", response_model=SuccessResponse)
async def get_donation_dashboard_route(
    start_date: str = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(default=None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get donation dashboard for mobile"""
    return get_mobile_impact_analytics(current_user["id"], start_date, end_date, db)

# Roundup preferences endpoints (since this is a roundup-only donation system)
@donations_router.get("/preferences", response_model=SuccessResponse)
async def get_roundup_preferences_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get roundup preferences (donation preferences for roundup system)"""
    return get_mobile_roundup_settings(current_user["id"], db)

@donations_router.put("/preferences", response_model=SuccessResponse)
async def update_roundup_preferences_route(
    preferences: dict = Body(...),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Update roundup preferences (donation preferences for roundup system)"""
    from types import SimpleNamespace
    preferences_obj = SimpleNamespace(**preferences)
    return update_mobile_roundup_settings(current_user["id"], preferences_obj, db)

@donations_router.post("/pause", response_model=SuccessResponse)
async def pause_donations_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Pause roundup donations"""
    return quick_toggle_roundups(current_user["id"], True, db)

@donations_router.post("/resume", response_model=SuccessResponse)
async def resume_donations_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Resume roundup donations"""
    return quick_toggle_roundups(current_user["id"], False, db)

