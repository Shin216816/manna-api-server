from typing import Optional
from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session
from app.middleware.auth_middleware import jwt_auth
from app.utils.database import get_db
from app.controller.church.roundups import (
    get_church_roundup_summary,
    get_church_transactions,
    get_church_roundups,
    update_church_roundup_settings,
    create_church_roundup_batch,
    get_church_roundup_analytics
)

router = APIRouter(tags=["Church Round-ups"])


@router.get("/summary")
async def get_roundup_summary(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get round-up summary for a church"""
    church_id = current_user.get("church_id")
    if not church_id:
        raise HTTPException(status_code=400, detail="Church ID not found in user data")
    return get_church_roundup_summary(church_id, current_user, db)


@router.get("/transactions")
async def get_transactions(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get transactions for a church with pagination"""
    church_id = current_user.get("church_id")
    if not church_id:
        raise HTTPException(status_code=400, detail="Church ID not found in user data")
    return get_church_transactions(church_id, page, limit, status, current_user, db)


@router.get("/")
async def get_roundups(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get round-ups for a church with pagination"""
    church_id = current_user.get("church_id")
    if not church_id:
        raise HTTPException(status_code=400, detail="Church ID not found in user data")
    return get_church_roundups(church_id, page, limit, status, current_user, db)


@router.put("/settings")
async def update_settings(
    settings_data: dict = Body(...),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Update round-up settings for a church"""
    church_id = current_user.get("church_id")
    if not church_id:
        raise HTTPException(status_code=400, detail="Church ID not found in user data")
    return update_church_roundup_settings(church_id, settings_data, current_user, db)


@router.post("/batch")
async def create_batch(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Create a batch of round-ups for a church"""
    church_id = current_user.get("church_id")
    if not church_id:
        raise HTTPException(status_code=400, detail="Church ID not found in user data")
    return create_church_roundup_batch(church_id, current_user, db)


@router.get("/analytics")
async def get_analytics(
    days: int = 30,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get round-up analytics for a church"""
    church_id = current_user.get("church_id")
    if not church_id:
        raise HTTPException(status_code=400, detail="Church ID not found in user data")
    return get_church_roundup_analytics(church_id, days, current_user, db)
