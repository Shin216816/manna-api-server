from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.controller.admin.users import (
    get_all_users, get_user_details, update_user_status, get_user_analytics,
    get_user_donations, get_user_church, get_user_activity
)
from app.utils.database import get_db
from app.middleware.admin_auth import admin_auth
from app.core.responses import SuccessResponse

users_router = APIRouter(tags=["User Management"])

class UserStatusUpdate(BaseModel):
    is_active: bool

@users_router.get("/list", response_model=SuccessResponse)
def list_users_route(
    search: str = Query(default="", description="Search by name or email"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    role: str = Query(default=None, description="Filter by user role"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """List all users (defaults to donor users only)"""
    page = (offset // limit) + 1
    # For admin, we pass 0 to get all users regardless of church
    # If no role specified, defaults to donor users only
    return get_all_users(page, limit, search, 0, role, db)

@users_router.get("/{user_id}", response_model=SuccessResponse)
async def get_user_details_route(
    user_id: int,
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get user details"""
    return get_user_details(user_id, db)

@users_router.put("/{user_id}/status", response_model=SuccessResponse)
def update_user_status_route(
    user_id: int,
    status_data: UserStatusUpdate,
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Update user status"""
    return update_user_status(user_id, status_data.is_active, db)

@users_router.get("/{user_id}/analytics", response_model=SuccessResponse)
async def get_user_analytics_route(
    user_id: int,
    start_date: str = Query(None, description="Start date"),
    end_date: str = Query(None, description="End date"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get user analytics"""
    return get_user_analytics(user_id, start_date, end_date, db)

@users_router.get("/{user_id}/donations", response_model=SuccessResponse)
async def get_user_donations_route(
    user_id: int,
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get user donations"""
    return get_user_donations(user_id, page, limit, db)

@users_router.get("/{user_id}/activity", response_model=SuccessResponse)
async def get_user_activity_route(
    user_id: int,
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get comprehensive user activity for admin management"""
    return get_user_activity(user_id, db)
