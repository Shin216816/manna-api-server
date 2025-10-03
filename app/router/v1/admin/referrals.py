from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.controller.admin.referrals import (
    get_referral_commissions, get_referral_statistics, get_referral_payouts
)
from app.schema.admin_schema import ReferralPayoutRequest
from app.utils.database import get_db
from app.middleware.admin_auth import admin_auth
from app.core.responses import SuccessResponse

referrals_router = APIRouter(tags=["Referral Management"])

@referrals_router.get("/", response_model=SuccessResponse)
async def list_referrals_route(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status: str = Query(default=None, description="Filter by status"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """List all referrals"""
    return get_referral_commissions(page, limit, status, db)

@referrals_router.get("/statistics", response_model=SuccessResponse)
async def get_referral_statistics_route(
    start_date: str = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(default=None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get referral statistics"""
    return get_referral_statistics(start_date, end_date, db)

@referrals_router.get("/payouts", response_model=SuccessResponse)
async def get_referral_payouts_route(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status: str = Query(default=None, description="Filter by payout status"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get referral payouts"""
    return get_referral_payouts(page, limit, status, db)
