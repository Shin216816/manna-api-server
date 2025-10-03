from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.controller.admin.churches import (
    get_all_churches, get_church_details, approve_church_kyc, reject_church_kyc, update_church_status,
    get_church_analytics, get_church_members, get_church_donations, get_church_kyc_details, update_church_profile_admin
)
from app.controller.admin.enhanced_churches import (
    get_enhanced_church_list,
    bulk_church_action,
    get_church_performance_metrics,
    send_church_communication,
    ChurchSearchRequest,
    BulkChurchActionRequest
)
from app.schema.admin_schema import ChurchKYCReviewRequest
from app.schema.church_schema import ChurchProfileUpdateRequest
from app.utils.database import get_db
from app.middleware.admin_auth import admin_auth
from app.core.responses import SuccessResponse

churches_router = APIRouter(tags=["Church Management"])

class ChurchStatusUpdate(BaseModel):
    is_active: bool

@churches_router.get("/list", response_model=SuccessResponse)
def list_churches_route(
    status_filter: str = Query(default="all", description="Filter by status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """List all churches"""
    return get_all_churches(limit, offset, status_filter, db)

@churches_router.get("/{church_id}", response_model=SuccessResponse)
async def get_church_details_route(
    church_id: int,
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get church details"""
    return get_church_details(church_id, db)

@churches_router.post("/{church_id}/kyc/approve", response_model=SuccessResponse)
def approve_church_route(
    church_id: int,
    data: ChurchKYCReviewRequest,
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Approve church KYC"""
    return approve_church_kyc(church_id, data, db)

@churches_router.post("/{church_id}/kyc/reject", response_model=SuccessResponse)
def reject_church_route(
    church_id: int,
    data: ChurchKYCReviewRequest,
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Reject church KYC"""
    return reject_church_kyc(church_id, data, db)

@churches_router.put("/{church_id}/status", response_model=SuccessResponse)
def update_church_status_route(
    church_id: int,
    status_data: ChurchStatusUpdate,
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Update church status"""
    return update_church_status(church_id, status_data.is_active, db)

@churches_router.put("/{church_id}/profile", response_model=SuccessResponse)
def update_church_profile_route(
    church_id: int,
    profile_data: ChurchProfileUpdateRequest,
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Update church profile (admin only)"""
    admin_id = current_user.get("id")
    admin_name = f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip() or "Internal Admin"
    return update_church_profile_admin(church_id, profile_data, admin_id, admin_name, db)

@churches_router.get("/{church_id}/analytics", response_model=SuccessResponse)
async def get_church_analytics_route(
    church_id: int,
    start_date: str = Query(None, description="Start date"),
    end_date: str = Query(None, description="End date"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get church analytics"""
    return get_church_analytics(church_id, start_date, end_date, db)

@churches_router.get("/{church_id}/members", response_model=SuccessResponse)
async def get_church_members_route(
    church_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get church members"""
    return get_church_members(church_id, page, limit, db)

@churches_router.get("/{church_id}/donations", response_model=SuccessResponse)
async def get_church_donations_route(
    church_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get church donations"""
    return get_church_donations(church_id, page, limit, db)

@churches_router.get("/{church_id}/kyc", response_model=SuccessResponse)
async def get_church_kyc_route(
    church_id: int,
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get church KYC details"""
    return get_church_kyc_details(church_id, db)

# Enhanced church management endpoints
@churches_router.post("/search", response_model=SuccessResponse)
async def search_churches_route(
    search_request: ChurchSearchRequest,
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Search churches with advanced filtering"""
    return get_enhanced_church_list(search_request, db)

@churches_router.post("/bulk-action", response_model=SuccessResponse)
async def bulk_church_action_route(
    action_request: BulkChurchActionRequest,
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Perform bulk actions on multiple churches"""
    return bulk_church_action(action_request, db)

@churches_router.get("/{church_id}/performance", response_model=SuccessResponse)
async def get_church_performance_route(
    church_id: int,
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get church performance metrics"""
    return get_church_performance_metrics(church_id, start_date, end_date, db)

@churches_router.post("/{church_id}/communication", response_model=SuccessResponse)
async def send_church_communication_route(
    church_id: int,
    communication_data: dict,
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Send communication to church"""
    return send_church_communication(church_id, communication_data, db)
