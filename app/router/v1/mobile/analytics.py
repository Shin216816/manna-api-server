from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.controller.mobile.analytics import (
    get_mobile_user_analytics, get_mobile_impact_analytics
)
from app.utils.database import get_db
from app.middleware.auth_middleware import jwt_auth
from app.core.responses import SuccessResponse

analytics_router = APIRouter(tags=["Mobile Analytics"])

@analytics_router.get("/user", response_model=SuccessResponse)
async def get_user_analytics_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get user analytics data"""
    return get_mobile_user_analytics(current_user["id"], db)

@analytics_router.get("/impact", response_model=SuccessResponse)
async def get_impact_analytics_route(
    start_date: str = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(default=None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get impact analytics for mobile"""
    return get_mobile_impact_analytics(current_user["id"], start_date, end_date, db)
