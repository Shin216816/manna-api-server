from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.controller.church.members import (
    get_church_members, get_member_details, get_member_giving_history, search_members,
    update_member_status, add_member_note, get_member_notes, export_members
)
from app.utils.database import get_db
from app.middleware.church_admin_auth import church_admin_auth
from app.core.responses import SuccessResponse

members_router = APIRouter(tags=["Church Members"])

@members_router.get("/", response_model=SuccessResponse)
async def get_members_route(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get church members"""
    return get_church_members(current_user["church_id"], page, limit, db)

@members_router.get("/{member_id}", response_model=SuccessResponse)
async def get_member_details_route(
    member_id: int,
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get member details"""
    return get_member_details(current_user["church_id"], member_id, db)

@members_router.get("/{member_id}/giving", response_model=SuccessResponse)
async def get_member_giving_route(
    member_id: int,
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get member giving history"""
    return get_member_giving_history(member_id, current_user["church_id"], page, limit, db)

@members_router.get("/search", response_model=SuccessResponse)
async def search_members_route(
    query: str = Query(..., description="Search query"),
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Search members"""
    return search_members(current_user["church_id"], query, page, limit, db)

@members_router.put("/{member_id}/status", response_model=SuccessResponse)
async def update_member_status_route(
    member_id: int,
    status: str = Query(..., description="Member status: active, inactive, blocked"),
    notes: str = Query(default=None, description="Optional notes for status change"),
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Update member status"""
    return update_member_status(member_id, current_user["church_id"], status, current_user["id"], notes, db)

@members_router.post("/{member_id}/notes", response_model=SuccessResponse)
async def add_member_note_route(
    member_id: int,
    note: str = Query(..., description="Note about the member"),
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Add a note about a member"""
    return add_member_note(member_id, current_user["church_id"], note, current_user["id"], db)

@members_router.get("/{member_id}/notes", response_model=SuccessResponse)
async def get_member_notes_route(
    member_id: int,
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get all notes for a member"""
    return get_member_notes(member_id, current_user["church_id"], db)

@members_router.get("/export", response_model=SuccessResponse)
async def export_members_route(
    format_type: str = Query(default="csv", description="Export format: csv or json"),
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Export members data"""
    return export_members(current_user["church_id"], format_type, db)
