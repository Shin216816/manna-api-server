from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.middleware.auth_middleware import jwt_church_admin_auth
from app.controller.church.referrals import (
    generate_referral_code,
    get_referral_info,
    use_referral_code,
    calculate_referral_commissions,
    get_referral_commissions,
    process_commission_payouts,
    get_referral_analytics,
    validate_referral_code
)
from app.core.responses import SuccessResponse
from typing import List

router = APIRouter()

@router.post("/referral-code/generate", response_model=SuccessResponse)
async def generate_referral_code_endpoint(
    current_admin: dict = Depends(jwt_church_admin_auth),
    db: Session = Depends(get_db)
):
    """Generate a unique referral code for the church"""
    church_id = current_admin.get("church_id")
    return generate_referral_code(church_id, db)

@router.get("/referral-info", response_model=SuccessResponse)
async def get_referral_info_endpoint(
    current_admin: dict = Depends(jwt_church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get church's referral information and statistics"""
    church_id = current_admin.get("church_id")
    return get_referral_info(church_id, db)

@router.post("/referral-code/use", response_model=SuccessResponse)
async def use_referral_code_endpoint(
    request: dict,
    current_admin: dict = Depends(jwt_church_admin_auth),
    db: Session = Depends(get_db)
):
    """Use a referral code when a new church registers"""
    referral_code = request.get("referral_code")
    if not referral_code:
        raise HTTPException(status_code=400, detail="Referral code is required")
    church_id = current_admin.get("church_id")
    return use_referral_code(referral_code, church_id, db)

@router.post("/referral-code/validate", response_model=SuccessResponse)
async def validate_referral_code_endpoint(
    request: dict,
    db: Session = Depends(get_db)
):
    """Validate a referral code without using it"""
    referral_code = request.get("referral_code")
    if not referral_code:
        raise HTTPException(status_code=400, detail="Referral code is required")
    return validate_referral_code(referral_code, db)

@router.post("/commissions/calculate", response_model=SuccessResponse)
async def calculate_referral_commissions_endpoint(
    current_admin: dict = Depends(jwt_church_admin_auth),
    db: Session = Depends(get_db)
):
    """Calculate and record referral commissions for the church"""
    church_id = current_admin.get("church_id")
    return calculate_referral_commissions(church_id, db)

@router.get("/commissions", response_model=SuccessResponse)
async def get_referral_commissions_endpoint(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_admin: dict = Depends(jwt_church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get referral commission history for the church"""
    church_id = current_admin.get("church_id")
    return get_referral_commissions(church_id, page, limit, db)

@router.post("/commissions/process-payouts", response_model=SuccessResponse)
async def process_commission_payouts_endpoint(
    current_admin: dict = Depends(jwt_church_admin_auth),
    db: Session = Depends(get_db)
):
    """Process pending commission payouts for the church"""
    church_id = current_admin.get("church_id")
    return process_commission_payouts(church_id, db)

@router.get("/analytics", response_model=SuccessResponse)
async def get_referral_analytics_endpoint(
    days: int = Query(30, ge=1, le=365),
    current_admin: dict = Depends(jwt_church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get detailed referral analytics for the church"""
    church_id = current_admin.get("church_id")
    return get_referral_analytics(church_id, days, db)