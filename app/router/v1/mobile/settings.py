from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.middleware.auth_middleware import jwt_auth
from app.core.responses import SuccessResponse
from fastapi import HTTPException
from app.core.responses import ResponseFactory

settings_router = APIRouter(tags=["Mobile Settings"])

@settings_router.get("/", response_model=SuccessResponse)
async def get_settings_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get all settings for mobile"""
    from app.controller.mobile.settings import get_mobile_settings
    return get_mobile_settings(current_user["id"], db)

@settings_router.put("/", response_model=SuccessResponse)
async def update_settings_route(
    settings_data: dict,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Update settings for mobile"""
    from app.controller.mobile.settings import update_mobile_settings
    return update_mobile_settings(current_user["id"], settings_data, db)

@settings_router.put("/notifications", response_model=SuccessResponse)
async def update_notification_settings_route(
    push_enabled: bool = Query(..., description="Enable push notifications"),
    email_enabled: bool = Query(..., description="Enable email notifications"),
    sms_enabled: bool = Query(..., description="Enable SMS notifications"),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Update notification settings for mobile"""
    from app.controller.mobile.settings import update_notification_preferences
    preferences = {
        "push_notifications": push_enabled,
        "email_notifications": email_enabled,
        "sms_notifications": sms_enabled
    }
    return update_notification_preferences(current_user["id"], preferences, db)

@settings_router.put("/privacy", response_model=SuccessResponse)
async def update_privacy_settings_route(
    data_sharing: bool = Query(..., description="Allow data sharing"),
    analytics_enabled: bool = Query(..., description="Enable analytics"),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Update privacy settings for mobile"""
    from app.controller.mobile.settings import update_privacy_settings
    privacy_data = {
        "share_analytics": analytics_enabled,
        "share_profile": data_sharing
    }
    return update_privacy_settings(current_user["id"], privacy_data, db)
