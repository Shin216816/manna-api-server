"""
Admin Payout Management Routes

Provides endpoints for administrators to manage church payouts.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.controller.admin.process_payouts import (
    trigger_church_payout, get_pending_payouts, retry_failed_payout, get_payout_analytics, get_all_payouts, get_payout_by_id
)
from app.middleware.admin_auth import admin_auth
from app.utils.database import get_db
from app.core.responses import SuccessResponse

payout_router = APIRouter(tags=["Admin Payouts"])


@payout_router.post("/trigger/{church_id}", response_model=SuccessResponse)
async def trigger_church_payout_route(
    church_id: int,
    current_admin: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Manually trigger payout for a specific church"""
    return trigger_church_payout(church_id, current_admin, db)


@payout_router.get("/pending", response_model=SuccessResponse)
async def get_pending_payouts_route(
    current_admin: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get all pending payouts awaiting processing"""
    return get_pending_payouts(current_admin, db)


@payout_router.post("/retry/{payout_id}", response_model=SuccessResponse)
async def retry_failed_payout_route(
    payout_id: int,
    current_admin: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Retry a failed payout"""
    return retry_failed_payout(payout_id, current_admin, db)


@payout_router.get("/", response_model=SuccessResponse)
async def get_all_payouts_route(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status: str = Query("all", description="Filter by status"),
    current_admin: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get all payouts with pagination and filtering"""
    return get_all_payouts(page, limit, status, db)


@payout_router.get("/analytics", response_model=SuccessResponse)
async def get_payout_analytics_route(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_admin: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get payout analytics for the specified period"""
    return get_payout_analytics(current_admin, db, days)


@payout_router.get("/{payout_id}", response_model=SuccessResponse)
async def get_payout_by_id_route(
    payout_id: int,
    current_admin: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get a specific payout by ID with full breakdown data"""
    return get_payout_by_id(payout_id, db)

