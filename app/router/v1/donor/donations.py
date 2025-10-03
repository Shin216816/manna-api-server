from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.controller.donor.donations import (
    process_roundup_donation,
    get_donation_status,
    get_donation_history,
    get_donation_impact_summary
)

router = APIRouter()

@router.post("/roundup")
def process_roundup_donation_route(
    data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process a roundup donation for a donor"""
    return process_roundup_donation(current_user, data, db)

@router.post("/status")
def get_donation_status_route(
    data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the status of a donation transaction"""
    return get_donation_status(current_user, data, db)

@router.get("/history")
def get_donation_history_route(
    page: int = 1,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get donation history for a donor"""
    return get_donation_history(current_user["user_id"], page, limit, db)

@router.get("/impact-summary")
def get_donation_impact_summary_route(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive donation impact summary for the current user"""
    return get_donation_impact_summary(current_user["user_id"], db)
