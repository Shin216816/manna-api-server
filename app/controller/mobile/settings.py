from fastapi import HTTPException
import logging
import traceback
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.model.m_user import User
from app.model.m_user_settings import UserSettings
from app.core.messages import get_auth_message
from app.core.responses import ResponseFactory, SuccessResponse

def get_mobile_settings(user_id: int, db: Session) -> SuccessResponse:
    """Get mobile app settings for user"""
    try:
        user = User.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail=get_auth_message("USER_NOT_FOUND")
            )

        settings = db.query(UserSettings).filter(
            UserSettings.user_id == user_id
        ).first()

        if not settings:
            # Create default settings
            settings = UserSettings(
                user_id=user_id,
                notifications_enabled=True,
                email_notifications=True,
                sms_notifications=False,
                push_notifications=True,
                privacy_share_analytics=True,
                privacy_share_profile=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)

        return ResponseFactory.success(
            message="Settings retrieved successfully",
            data={
                "notifications": {
                    "enabled": settings.notifications_enabled,
                    "email": settings.email_notifications,
                    "sms": settings.sms_notifications,
                    "push": settings.push_notifications
                },
                "privacy": {
                    "share_analytics": settings.privacy_share_analytics,
                    "share_profile": settings.privacy_share_profile
                },
                "updated_at": settings.updated_at
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to get settings"
        )

def update_mobile_settings(user_id: int, settings_data: dict, db: Session) -> SuccessResponse:
    """Update mobile app settings for user"""
    try:
        user = User.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail=get_auth_message("USER_NOT_FOUND")
            )

        settings = db.query(UserSettings).filter(
            UserSettings.user_id == user_id
        ).first()

        if not settings:
            settings = UserSettings(
                user_id=user_id,
                created_at=datetime.now(timezone.utc)
            )
            db.add(settings)

        # Update notification settings
        if "notifications" in settings_data:
            notifications = settings_data["notifications"]
            if "enabled" in notifications:
                settings.notifications_enabled = notifications["enabled"]
            if "email" in notifications:
                settings.email_notifications = notifications["email"]
            if "sms" in notifications:
                settings.sms_notifications = notifications["sms"]
            if "push" in notifications:
                settings.push_notifications = notifications["push"]

        # Update privacy settings
        if "privacy" in settings_data:
            privacy = settings_data["privacy"]
            if "share_analytics" in privacy:
                settings.privacy_share_analytics = privacy["share_analytics"]
            if "share_profile" in privacy:
                settings.privacy_share_profile = privacy["share_profile"]

        setattr(settings, 'updated_at', datetime.now(timezone.utc))
        db.commit()
        db.refresh(settings)

        return ResponseFactory.success(
            message="Settings updated successfully",
            data={
                "notifications": {
                    "enabled": settings.notifications_enabled,
                    "email": settings.email_notifications,
                    "sms": settings.sms_notifications,
                    "push": settings.push_notifications
                },
                "privacy": {
                    "share_analytics": settings.privacy_share_analytics,
                    "share_profile": settings.privacy_share_profile
                },
                "updated_at": settings.updated_at
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to update settings"
        )

def update_notification_preferences(user_id: int, preferences: dict, db: Session) -> SuccessResponse:
    """Update notification preferences for mobile user"""
    try:
        user = User.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail=get_auth_message("USER_NOT_FOUND")
            )

        settings = db.query(UserSettings).filter(
            UserSettings.user_id == user_id
        ).first()

        if not settings:
            settings = UserSettings(
                user_id=user_id,
                created_at=datetime.now(timezone.utc)
            )
            db.add(settings)

        # Update notification preferences
        allowed_preferences = ["enabled", "email", "sms", "push"]
        for pref in allowed_preferences:
            if pref in preferences:
                if pref == "enabled":
                    settings.notifications_enabled = preferences[pref]
                elif pref == "email":
                    settings.email_notifications = preferences[pref]
                elif pref == "sms":
                    settings.sms_notifications = preferences[pref]
                elif pref == "push":
                    settings.push_notifications = preferences[pref]

        setattr(settings, 'updated_at', datetime.now(timezone.utc))
        db.commit()
        db.refresh(settings)

        return ResponseFactory.success(
            message="Notification preferences updated successfully",
            data={
                "enabled": settings.notifications_enabled,
                "email": settings.email_notifications,
                "sms": settings.sms_notifications,
                "push": settings.push_notifications
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to update notification preferences"
        )

def update_privacy_settings(user_id: int, privacy_data: dict, db: Session) -> SuccessResponse:
    """Update privacy settings for mobile user"""
    try:
        user = User.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail=get_auth_message("USER_NOT_FOUND")
            )

        settings = db.query(UserSettings).filter(
            UserSettings.user_id == user_id
        ).first()

        if not settings:
            settings = UserSettings(
                user_id=user_id,
                created_at=datetime.now(timezone.utc)
            )
            db.add(settings)

        # Update privacy settings
        if "share_analytics" in privacy_data:
            settings.privacy_share_analytics = privacy_data["share_analytics"]
        if "share_profile" in privacy_data:
            settings.privacy_share_profile = privacy_data["share_profile"]

        setattr(settings, 'updated_at', datetime.now(timezone.utc))
        db.commit()
        db.refresh(settings)

        return ResponseFactory.success(
            message="Privacy settings updated successfully",
            data={
                "share_analytics": settings.privacy_share_analytics,
                "share_profile": settings.privacy_share_profile
            }
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail="Failed to update privacy settings"
        )
