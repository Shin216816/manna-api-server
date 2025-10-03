from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.controller.donor.roundup_collection import (
    get_roundup_collection_settings, update_roundup_collection_settings,
    get_recent_transactions_with_roundups, get_pending_roundups_summary
)
from app.utils.database import get_db
from app.middleware.auth_middleware import jwt_auth
from app.core.responses import SuccessResponse

router = APIRouter(tags=["Donor Round-up Collection"])


@router.get("/settings", response_model=SuccessResponse)
async def get_roundup_collection_settings_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get comprehensive round-up collection settings"""
    return get_roundup_collection_settings(current_user, db)


@router.put("/settings", response_model=SuccessResponse)
async def update_roundup_collection_settings_route(
    data: dict,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Update round-up collection settings"""
    return update_roundup_collection_settings(data, current_user, db)


@router.get("/transactions", response_model=SuccessResponse)
async def get_recent_transactions_with_roundups_route(
    days_back: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get recent transactions with calculated round-ups"""
    return get_recent_transactions_with_roundups(current_user, days_back, db)


@router.get("/pending", response_model=SuccessResponse)
async def get_pending_roundups_summary_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get pending round-ups summary"""
    return get_pending_roundups_summary(current_user, db)
