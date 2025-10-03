from app.controller.church.donor_management import (
    get_active_donors,
    get_donor_analytics,
    get_donor_communication_preferences,
    update_donor_communication_preferences,
    get_donor_retention_metrics,
    export_donor_data
)
from app.controller.church.mobile_messages import send_mobile_church_message, get_donor_message_history
from app.middleware.church_admin_auth import church_admin_auth
from app.core.responses import SuccessResponse
from app.utils.database import get_db
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

donor_management_router = APIRouter(tags=["Church Donor Management"])

@donor_management_router.get("/active", response_model=SuccessResponse)
def get_active_donors_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str = Query(None, description="Search term"),
    status: str = Query(None, description="Filter by status"),
    current_user: Dict[str, Any] = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get active donors for the church with pagination"""
    church_id = current_user["church_id"]
    return get_active_donors(church_id, page, limit, search, status, db)

@donor_management_router.get("/{donor_id}/analytics", response_model=SuccessResponse)
def get_donor_analytics_endpoint(
    donor_id: int,
    current_user: Dict[str, Any] = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get detailed analytics for a specific donor"""
    church_id = current_user["church_id"]
    return get_donor_analytics(church_id, donor_id, db)

@donor_management_router.get("/{donor_id}/communication", response_model=SuccessResponse)
def get_donor_communication_preferences_endpoint(
    donor_id: int,
    current_user: Dict[str, Any] = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get communication preferences for a specific donor"""
    church_id = current_user["church_id"]
    return get_donor_communication_preferences(church_id, donor_id, db)

@donor_management_router.put("/{donor_id}/communication", response_model=SuccessResponse)
def update_donor_communication_preferences_endpoint(
    donor_id: int,
    preferences: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Update communication preferences for a specific donor"""
    church_id = current_user["church_id"]
    return update_donor_communication_preferences(church_id, donor_id, preferences, current_user["id"], db)

@donor_management_router.get("/retention/metrics", response_model=SuccessResponse)
def get_donor_retention_metrics_endpoint(
    current_user: Dict[str, Any] = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get donor retention metrics for the church"""
    church_id = current_user["church_id"]
    return get_donor_retention_metrics(church_id, db)

@donor_management_router.get("/export", response_model=SuccessResponse)
def export_donor_data_endpoint(
    format_type: str = Query("csv", description="Export format (csv, excel, json)"),
    current_user: Dict[str, Any] = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Export donor data in various formats"""
    church_id = current_user["church_id"]
    return export_donor_data(church_id, format_type, None, db)

@donor_management_router.get("/{donor_id}/messages", response_model=SuccessResponse)
def get_donor_messages_endpoint(
    donor_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: Dict[str, Any] = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get message history for a specific donor"""
    church_id = current_user["church_id"]
    offset = (page - 1) * limit
    return get_donor_message_history(church_id, donor_id, limit, offset, db)

@donor_management_router.post("/{donor_id}/message", response_model=SuccessResponse)
def send_message_to_donor_endpoint(
    donor_id: int,
    message_data: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Send a message from church admin to a specific donor"""
    church_id = current_user["church_id"]
    
    # Extract message data
    title = message_data.get("subject", "")
    content = message_data.get("message", "")
    message_type = message_data.get("type", "general")
    
    if not title or not content:
        raise HTTPException(status_code=400, detail="Subject and message are required")
    
    return send_mobile_church_message(church_id, donor_id, title, content, message_type, db)

@donor_management_router.get("/debug/church-members", response_model=SuccessResponse)
def debug_church_members_endpoint(
    current_user: Dict[str, Any] = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Debug endpoint to check what users exist in the church"""
    from app.model.m_user import User
    from sqlalchemy import func
    
    church_id = current_user["church_id"]
    
    # Get all users in the church
    all_users = db.query(
        User.id,
        User.first_name,
        User.last_name,
        User.email,
        User.role,
        User.is_active,
        User.church_id,
        User.created_at
    ).filter(User.church_id == church_id).all()
    
    # Get count by role
    role_counts = db.query(
        User.role,
        func.count(User.id).label('count')
    ).filter(
        User.church_id == church_id,
        User.is_active == True
    ).group_by(User.role).all()
    
    return ResponseFactory.success(
        message="Church members debug info",
        data={
            "church_id": church_id,
            "total_users": len(all_users),
            "role_counts": {role: count for role, count in role_counts},
            "users": [
                {
                    "id": user.id,
                    "name": f"{user.first_name} {user.last_name}",
                    "email": user.email,
                    "role": user.role,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                }
                for user in all_users
            ]
        }
    )



