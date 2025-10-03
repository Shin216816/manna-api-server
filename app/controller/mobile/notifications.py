from fastapi import HTTPException
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timezone
from typing import Dict, Any, List

from app.model.m_user import User
from app.model.m_church_message import ChurchMessage
from app.model.m_user_message import UserMessage
from app.core.responses import ResponseFactory
from app.services.database_notification_service import database_notification_service


def get_mobile_notifications(user_id: int, db: Session, limit: int = 50, offset: int = 0):
    """Get notifications for mobile app using database notification service"""
    try:
        # Use the database notification service for comprehensive notification retrieval
        result = database_notification_service.get_user_notifications(
            user_id=user_id,
            limit=limit,
            offset=offset,
            unread_only=False,
            db=db
        )
        
        if result["success"]:
            return ResponseFactory.success(
                message="Notifications retrieved successfully",
                data={
                    "notifications": result["notifications"],
                    "total": result["total_count"],
                    "unread_count": result["unread_count"],
                    "limit": result["limit"],
                    "offset": result["offset"],
                    "has_more": result.get("has_more", False)
                }
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to get notifications"))
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting notifications for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get notifications")


def mark_notification_read(user_id: int, notification_id: int, db: Session):
    """Mark a notification as read using database notification service"""
    try:
        # Convert integer ID to string format expected by service
        notification_str_id = f"church_{notification_id}"
        
        result = database_notification_service.mark_notification_read(
            user_id=user_id,
            notification_id=notification_str_id,
            db=db
        )
        
        if result["success"]:
            return ResponseFactory.success(
                message="Notification marked as read",
                data={
                    "notification_id": notification_id,
                    "is_read": True,
                    "read_at": datetime.now(timezone.utc).isoformat()
                }
            )
        else:
            raise HTTPException(status_code=404, detail=result.get("error", "Notification not found"))
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error marking notification {notification_id} as read for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")


def mark_all_notifications_read(user_id: int, db: Session):
    """Mark all notifications as read for user"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update all unread notifications
        updated_count = db.query(UserMessage).filter(
            and_(
                UserMessage.user_id == user_id,
                UserMessage.is_read == False
            )
        ).update({
            "is_read": True,
            "read_at": datetime.now(timezone.utc)
        })
        
        db.commit()
        
        return ResponseFactory.success(
            message="All notifications marked as read",
            data={
                "updated_count": updated_count,
                "user_id": user_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error marking all notifications as read for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark all notifications as read")


def delete_notification(user_id: int, notification_id: int, db: Session):
    """Delete a notification"""
    try:
        user_message = db.query(UserMessage).filter(
            and_(
                UserMessage.id == notification_id,
                UserMessage.user_id == user_id
            )
        ).first()
        
        if not user_message:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        db.delete(user_message)
        db.commit()
        
        return ResponseFactory.success(
            message="Notification deleted successfully",
            data={"notification_id": notification_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting notification {notification_id} for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete notification")


def get_notification_preferences(user_id: int, db: Session):
    """Get notification preferences for mobile app"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # For now, return default preferences
        # In a real implementation, you would have a preferences table
        preferences = {
            "email_notifications": True,
            "sms_notifications": True,
            "push_notifications": True,
            "donation_confirmations": True,
            "roundup_notifications": True,
            "schedule_reminders": True
        }
        
        return ResponseFactory.success(
            message="Notification preferences retrieved successfully",
            data={"preferences": preferences}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting notification preferences for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get notification preferences")


def update_notification_preferences(user_id: int, preferences_data: Dict[str, Any], db: Session):
    """Update notification preferences for mobile app"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # In a real implementation, you would save these to a preferences table
        # For now, just return the updated preferences
        
        allowed_preferences = [
            "email_notifications", "sms_notifications", "push_notifications",
            "donation_confirmations", "roundup_notifications", "schedule_reminders"
        ]
        
        updated_preferences = {}
        for key, value in preferences_data.items():
            if key in allowed_preferences and isinstance(value, bool):
                updated_preferences[key] = value
        
        return ResponseFactory.success(
            message="Notification preferences updated successfully",
            data={"preferences": updated_preferences}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating notification preferences for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update notification preferences")
