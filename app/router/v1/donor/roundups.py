from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.middleware.auth_middleware import jwt_auth
from app.controller.donor.roundups import (
    get_roundup_settings, update_roundup_settings, get_pending_roundups,
    toggle_roundups, calculate_roundups, get_roundup_history, get_monthly_estimates
)
from app.schema.donor_schema import (
    DonorRoundupSettingsRequest, DonorPendingRoundupsRequest,
    DonorToggleRoundupsRequest, DonorCalculateRoundupsRequest,
    DonorRoundupHistoryRequest
)
from typing import Optional

router = APIRouter()

@router.get("/settings")
def donor_get_roundup_settings(current_user: dict = Depends(jwt_auth), db: Session = Depends(get_db)):
    """Get donor roundup settings"""
    return get_roundup_settings(current_user, db)

@router.put("/settings")
def donor_update_roundup_settings(current_user: dict = Depends(jwt_auth), data: DonorRoundupSettingsRequest = Body(...), db: Session = Depends(get_db)):
    """Update donor roundup settings"""
    return update_roundup_settings(current_user, data, db)

@router.get("/pending")
def donor_get_pending_roundups(
    include_transactions: bool = Query(False, description="Include transaction details"),
    days_back: int = Query(7, description="Number of days to look back for transactions"),
    current_user: dict = Depends(jwt_auth), 
    db: Session = Depends(get_db)
):
    """Get donor pending roundups data"""
    request_data = DonorPendingRoundupsRequest(
        include_transactions=include_transactions,
        days_back=days_back
    )
    return get_pending_roundups(current_user, request_data, db)

@router.post("/toggle")
def donor_toggle_roundups(current_user: dict = Depends(jwt_auth), data: DonorToggleRoundupsRequest = Body(...), db: Session = Depends(get_db)):
    """Toggle roundup donations on/off"""
    return toggle_roundups(current_user, data, db)

@router.post("/calculate")
def donor_calculate_roundups_preview(current_user: dict = Depends(jwt_auth), data: DonorCalculateRoundupsRequest = Body(...), db: Session = Depends(get_db)):
    """Calculate roundups for a preview period"""
    return calculate_roundups(current_user, data, db)

@router.post("/estimate")
def donor_get_monthly_estimates(current_user: dict = Depends(jwt_auth), db: Session = Depends(get_db)):
    """Get monthly roundup estimates for all multiplier options"""
    return get_monthly_estimates(current_user, db)

@router.get("/history")
def donor_get_roundup_history(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    frequency: Optional[str] = Query(None, description="Filter by frequency"),
    limit: int = Query(50, description="Number of records to fetch"),
    current_user: dict = Depends(jwt_auth), 
    db: Session = Depends(get_db)
):
    """Get donor roundup history"""
    request_data = DonorRoundupHistoryRequest(
        start_date=start_date,
        end_date=end_date,
        status=status,
        frequency=frequency,
        limit=limit
    )
    return get_roundup_history(current_user, request_data, db)
