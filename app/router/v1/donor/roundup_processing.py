from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.controller.donor.roundup_processing import (
    get_pending_roundups,
    collect_pending_roundups,
    get_roundup_summary
)
from app.utils.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.core.responses import SuccessResponse

router = APIRouter(tags=["Donor"])

@router.get("/pending", response_model=SuccessResponse)
async def get_pending_roundups_route(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get pending roundups
    
    Retrieves all pending roundup transactions that are ready
    to be collected and processed as donations.
    """
    return get_pending_roundups(current_user["user_id"], db)

@router.post("/collect", response_model=SuccessResponse)
async def collect_pending_roundups_route(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Collect pending roundups
    
    Processes and collects all pending roundup transactions,
    converting them into donations for the church.
    """
    return collect_pending_roundups(current_user["user_id"], db)

@router.get("/summary", response_model=SuccessResponse)
async def get_roundup_summary_route(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get roundup summary
    
    Provides a summary of roundup activity including total
    amounts, transaction counts, and recent activity.
    """
    return get_roundup_summary(current_user["user_id"], db)

@router.post("/collect-roundups", response_model=SuccessResponse)
async def collect_roundups_route(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Collect roundups (alternative endpoint)
    
    Alternative endpoint for collecting pending roundups.
    Same functionality as the collect endpoint.
    """
    return collect_pending_roundups(current_user["user_id"], db)