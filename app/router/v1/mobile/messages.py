from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.controller.mobile.messages import (
    get_mobile_messages, mark_message_read, mark_all_messages_as_read,
    get_unread_message_count, delete_mobile_message, get_mobile_notifications,
    mark_notification_read, get_message_settings, update_message_settings
)
from app.utils.database import get_db
from app.middleware.auth_middleware import jwt_auth
from app.core.responses import SuccessResponse

messages_router = APIRouter(tags=["Mobile Messages"])

@messages_router.get("/", response_model=SuccessResponse)
async def get_church_messages_route(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get church messages for mobile"""
    return get_mobile_messages(current_user["id"], limit, db)

@messages_router.post("/{message_id}/read", response_model=SuccessResponse)
async def mark_message_as_read_route(
    message_id: int,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Mark message as read for mobile"""
    return mark_message_read(current_user["id"], message_id, db)

@messages_router.post("/read-all", response_model=SuccessResponse)
async def mark_all_messages_as_read_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Mark all messages as read for mobile"""
    return mark_all_messages_as_read(current_user["id"], db)

@messages_router.get("/unread-count", response_model=SuccessResponse)
async def get_unread_message_count_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get unread message count for mobile"""
    return get_unread_message_count(current_user["id"], db)

@messages_router.delete("/{message_id}", response_model=SuccessResponse)
async def delete_message_route(
    message_id: int,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Delete message for mobile"""
    return delete_mobile_message(current_user["id"], message_id, db)

@messages_router.get("/notifications", response_model=SuccessResponse)
async def get_notifications_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get notifications for mobile"""
    return get_mobile_notifications(current_user["id"], db)

@messages_router.post("/notifications/mark-read", response_model=SuccessResponse)
async def mark_notification_read_route(
    notification_id: int,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Mark notification as read for mobile"""
    return mark_notification_read(current_user["id"], notification_id, db)

@messages_router.get("/settings", response_model=SuccessResponse)
async def get_message_settings_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get message settings for mobile"""
    return get_message_settings(current_user["id"], db)

@messages_router.put("/settings", response_model=SuccessResponse)
async def update_message_settings_route(
    push_enabled: bool = Query(..., description="Enable push notifications"),
    email_enabled: bool = Query(..., description="Enable email notifications"),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Update message settings for mobile"""
    return update_message_settings(current_user["id"], push_enabled, email_enabled, db)
