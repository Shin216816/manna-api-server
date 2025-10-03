from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.controller.church.payouts import (
    get_payout_history, get_payout_status, get_payout_details
)
from app.tasks.process_church_payouts import create_monthly_church_payouts
from app.utils.database import get_db
from app.middleware.church_admin_auth import church_admin_auth
from app.core.responses import SuccessResponse

payouts_router = APIRouter(tags=["Church Payouts"])

@payouts_router.get("/history", response_model=SuccessResponse)
async def get_payout_history_route(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get payout history"""
    return get_payout_history(current_user["church_id"], db, page, limit)

@payouts_router.get("/status", response_model=SuccessResponse)
async def get_payout_status_route(
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get payout status"""
    return get_payout_status(current_user["church_id"], db)

@payouts_router.get("/{payout_id}", response_model=SuccessResponse)
async def get_payout_details_route(
    payout_id: int,
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get payout details"""
    return get_payout_details(payout_id, current_user["church_id"], db)

@payouts_router.post("/create-monthly-payouts", response_model=SuccessResponse)
async def create_monthly_payouts_route(
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Manually trigger monthly payout creation for testing"""
    try:
        # This will create monthly payouts for all churches
        create_monthly_church_payouts()
        
        return {
            "success": True,
            "message": "Monthly payouts creation triggered successfully",
            "data": {"status": "processing"}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create monthly payouts")
