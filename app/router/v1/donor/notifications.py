"""
Donor Notifications Router

Handles donor notification endpoints for fetching, marking as read, and managing notifications.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.controller.mobile.notifications import (
    get_mobile_notifications,
    mark_notification_read,
    mark_all_notifications_read,
    delete_notification,
    get_notification_preferences,
    update_notification_preferences
)
from app.core.responses import ResponseFactory
from app.middleware.auth_middleware import get_current_user
from app.utils.database import get_db

router = APIRouter(tags=["Donor Notifications"])


@router.get("/test", response_model=None)
async def test_notifications_endpoint():
    """
    Test endpoint for notifications - no authentication required
    """
    return {
        "success": True,
        "message": "Notifications endpoint is working",
        "data": {
            "test": True,
            "timestamp": "2025-09-17T05:00:00Z",
            "cors_test": "CORS headers should be present"
        }
    }

@router.get("/cors-test", response_model=None)
async def cors_test_endpoint():
    """
    CORS test endpoint - no authentication required
    """
    return {
        "success": True,
        "message": "CORS test successful",
        "data": {
            "cors_working": True,
            "timestamp": "2025-09-17T05:43:00Z"
        }
    }

@router.get("", response_model=None)
@router.get("/", response_model=None)
async def get_notifications(
    limit: int = Query(default=50, description="Number of notifications to return"),
    offset: int = Query(default=0, description="Number of notifications to skip"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get donor notifications
    
    Retrieves notifications for the authenticated donor user.
    Includes church messages, system notifications, and other relevant alerts.
    """
    user_id = current_user["user_id"]
    return get_mobile_notifications(user_id, db, limit, offset)


@router.post("/{notification_id}/read", response_model=None)
async def mark_notification_as_read(
    notification_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a notification as read
    
    Marks a specific notification as read for the authenticated donor user.
    """
    user_id = current_user["user_id"]
    return mark_notification_read(user_id, notification_id, db)


@router.post("/read-all", response_model=None)
async def mark_all_notifications_as_read(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark all notifications as read
    
    Marks all unread notifications as read for the authenticated donor user.
    """
    user_id = current_user["user_id"]
    return mark_all_notifications_read(user_id, db)


@router.delete("/{notification_id}", response_model=None)
async def delete_notification_by_id(
    notification_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a notification
    
    Deletes a specific notification for the authenticated donor user.
    """
    user_id = current_user["user_id"]
    return delete_notification(user_id, notification_id, db)


@router.get("/preferences", response_model=None)
async def get_notification_preferences_endpoint(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get notification preferences
    
    Retrieves notification preferences for the authenticated donor user.
    """
    user_id = current_user["user_id"]
    return get_notification_preferences(user_id, db)


@router.post("/preferences", response_model=None)
async def update_notification_preferences_endpoint(
    preferences_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update notification preferences
    
    Updates notification preferences for the authenticated donor user.
    """
    user_id = current_user["user_id"]
    return update_notification_preferences(user_id, preferences_data, db)


@router.post("/create-sample", response_model=None)
async def create_sample_notifications_endpoint(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create sample notifications for testing
    
    Creates sample notifications for the authenticated donor user.
    This endpoint is for development/testing purposes only.
    """
    from app.services.database_notification_service import database_notification_service
    
    user_id = current_user["user_id"]
    result = database_notification_service.create_sample_notifications(user_id, db)
    
    if result["success"]:
        return ResponseFactory.success(
            message="Sample notifications created successfully",
            data=result
        )
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to create sample notifications"))
