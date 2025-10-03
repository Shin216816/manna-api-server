from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.controller.mobile.roundups import (
    get_mobile_roundup_settings, update_mobile_roundup_settings,
    get_mobile_pending_roundups, quick_toggle_roundups,
    get_mobile_enhanced_roundup_status, get_mobile_transactions,
    get_mobile_donation_history, get_mobile_impact_summary
)
from app.schema.bank_schema import MobileRoundupSettingsRequest
from app.utils.database import get_db
from app.middleware.auth_middleware import jwt_auth
from app.core.responses import SuccessResponse

roundups_router = APIRouter(tags=["Mobile Roundups"])

@roundups_router.get("/status", response_model=SuccessResponse)
async def get_roundup_status_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get enhanced roundup status for mobile"""
    return get_mobile_enhanced_roundup_status(current_user["id"], db)

@roundups_router.get("/settings", response_model=SuccessResponse)
async def get_roundup_settings_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get roundup settings for mobile"""
    return get_mobile_roundup_settings(current_user["id"], db)

@roundups_router.put("/settings", response_model=SuccessResponse)
async def update_roundup_settings_route(
    data: MobileRoundupSettingsRequest,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Update roundup settings for mobile"""
    return update_mobile_roundup_settings(current_user["id"], data, db)

@roundups_router.get("/pending", response_model=SuccessResponse)
async def get_pending_roundups_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get pending roundups for mobile"""
    return get_mobile_pending_roundups(current_user["id"], db)

@roundups_router.post("/toggle", response_model=SuccessResponse)
async def toggle_roundups_route(
    pause: bool = Query(..., description="True to pause, False to resume"),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Toggle roundups on/off for mobile"""
    return quick_toggle_roundups(current_user["id"], pause, db)

@roundups_router.get("/transactions", response_model=SuccessResponse)
async def get_transactions_route(
    limit: int = Query(20, description="Number of transactions to fetch"),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get recent transactions with roundup calculations for mobile"""
    return get_mobile_transactions(current_user["id"], limit, db)

@roundups_router.get("/history", response_model=SuccessResponse)
async def get_donation_history_route(
    limit: int = Query(20, description="Number of donations to fetch"),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get donation history optimized for mobile"""
    return get_mobile_donation_history(current_user["id"], limit, db)

@roundups_router.get("/impact", response_model=SuccessResponse)
async def get_impact_summary_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get impact summary for mobile display"""
    return get_mobile_impact_summary(current_user["id"], db)

@roundups_router.post("/pause", response_model=SuccessResponse)
async def pause_roundups_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Pause roundups for mobile"""
    return quick_toggle_roundups(current_user["id"], True, db)

@roundups_router.post("/resume", response_model=SuccessResponse)
async def resume_roundups_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Resume roundups for mobile"""
    return quick_toggle_roundups(current_user["id"], False, db)

@roundups_router.get("/preview", response_model=SuccessResponse)
async def get_roundup_preview_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get roundup preview with recent transactions"""
    return get_mobile_transactions(current_user["id"], 10, db)
