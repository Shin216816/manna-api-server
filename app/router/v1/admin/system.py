from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.controller.admin.system import (
    get_system_status, get_health_check, get_performance_metrics
)
from app.utils.database import get_db
from app.middleware.admin_auth import admin_auth
from app.core.responses import SuccessResponse

system_router = APIRouter(tags=["System Management"])

@system_router.get("/status", response_model=SuccessResponse)
async def get_system_status_route(
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get system status"""
    return get_system_status(db)

@system_router.get("/health", response_model=SuccessResponse)
async def get_health_metrics_route(
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get health metrics"""
    return get_health_check(db)

@system_router.get("/performance", response_model=SuccessResponse)
async def get_performance_metrics_route(
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get performance metrics"""
    return get_performance_metrics(db)
