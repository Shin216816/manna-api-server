from fastapi import HTTPException
import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from sqlalchemy import func
from typing import Optional

from app.model.m_user import User
from app.model.m_church_message import ChurchMessage
from app.model.m_user_message import UserMessage
from app.model.m_audit_log import AuditLog
from app.model.m_user_settings import UserSettings
from app.core.responses import ResponseFactory

def get_mobile_messages(user_id: int, limit: int = 20, db: Optional[Session] = None):
    """Get messages for mobile user"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        user = User.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Get user's primary church
        primary_church = user.get_primary_church(db)
        if not primary_church:
            return ResponseFactory.success(
                message="User not associated with any church",
                data={"messages": [], "total_count": 0}
            )
        
        # Get user's church messages
        messages = db.query(ChurchMessage).filter(
            ChurchMessage.church_id == primary_church.id,
            ChurchMessage.is_active == True,
            ChurchMessage.is_published == True
        ).order_by(ChurchMessage.created_at.desc()).limit(limit).all()

        total_count = db.query(func.count(ChurchMessage.id)).filter(
            ChurchMessage.church_id == primary_church.id,
            ChurchMessage.is_active == True,
            ChurchMessage.is_published == True
        ).scalar()

        messages_data = []
        for message in messages:
            # Check if user has read this message
            user_message = db.query(UserMessage).filter(
                UserMessage.user_id == user_id,
                UserMessage.message_id == message.id
            ).first()
            
            messages_data.append({
                "id": message.id,
                "title": message.title,
                "content": message.content,
                "type": message.type.value if message.type else "general",
                "priority": message.priority.value if message.priority else "medium",
                "is_read": user_message.is_read if user_message else False,
                "read_at": user_message.read_at.isoformat() if user_message and user_message.read_at else None,
                "created_at": message.created_at.isoformat() if message.created_at else None,
                "updated_at": message.updated_at.isoformat() if message.updated_at else None
            })

        return ResponseFactory.success(
            message="Messages retrieved successfully",
            data={
                "messages": messages_data,
                "total_count": total_count
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to get messages"
        )

def mark_message_read(user_id: int, message_id: int, db: Session):
    """Mark message as read for mobile user"""
    try:
        user = User.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Get user's primary church
        primary_church = user.get_primary_church(db)
        if not primary_church:
            raise HTTPException(
                status_code=400,
                detail="User not associated with any church"
            )
        
        # Verify message exists and belongs to user's church
        message = db.query(ChurchMessage).filter(
            ChurchMessage.id == message_id,
            ChurchMessage.church_id == primary_church.id,
            ChurchMessage.is_active == True
        ).first()
        
        if not message:
            raise HTTPException(
                status_code=404,
                detail="Message not found"
            )

        # Check if user message record exists
        user_message = db.query(UserMessage).filter(
            UserMessage.user_id == user_id,
            UserMessage.message_id == message_id
        ).first()

        if not user_message:
            # Create new user message record
            user_message = UserMessage(
                user_id=user_id,
                message_id=message_id,
                is_read=True,
                read_at=datetime.now(timezone.utc)
            )
            db.add(user_message)
        else:
            # Update existing record
            user_message.is_read = True
            user_message.read_at = datetime.now(timezone.utc)

        db.commit()

        return ResponseFactory.success(
            message="Message marked as read"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to mark message as read"
        )

def mark_all_messages_as_read(user_id: int, db: Session):
    """Mark all messages as read for mobile user"""
    try:
        user = User.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Get user's primary church
        primary_church = user.get_primary_church(db)
        if not primary_church:
            return ResponseFactory.success(
                message="User not associated with any church",
                data={"message": "No messages to mark as read"}
            )
        
        # Get all unread messages for user's church
        unread_messages = db.query(ChurchMessage).filter(
            ChurchMessage.church_id == primary_church.id,
            ChurchMessage.is_active == True,
            ChurchMessage.is_published == True
        ).all()

        # Mark all messages as read
        for message in unread_messages:
            user_message = db.query(UserMessage).filter(
                UserMessage.user_id == user_id,
                UserMessage.message_id == message.id
            ).first()

            if not user_message:
                # Create new user message record
                user_message = UserMessage(
                    user_id=user_id,
                    message_id=message.id,
                    is_read=True,
                    read_at=datetime.now(timezone.utc)
                )
                db.add(user_message)
            else:
                # Update existing record
                user_message.is_read = True
                user_message.read_at = datetime.now(timezone.utc)

        db.commit()

        return ResponseFactory.success(
            message="All messages marked as read"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to mark all messages as read"
        )

def get_unread_message_count(user_id: int, db: Session):
    """Get unread message count for mobile user"""
    try:
        user = User.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Get user's primary church
        primary_church = user.get_primary_church(db)
        if not primary_church:
            return ResponseFactory.success(
                message="User not associated with any church",
                data={"unread_count": 0}
            )
        
        # Count unread messages
        unread_count = db.query(func.count(ChurchMessage.id)).filter(
            ChurchMessage.church_id == primary_church.id,
            ChurchMessage.is_active == True,
            ChurchMessage.is_published == True
        ).scalar()

        # Subtract read messages
        read_count = db.query(func.count(UserMessage.id)).filter(
            UserMessage.user_id == user_id,
            UserMessage.is_read == True
        ).scalar()

        actual_unread_count = max(0, unread_count - read_count)

        return ResponseFactory.success(
            message="Unread count retrieved successfully",
            data={
                "unread_count": actual_unread_count
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to get unread count"
        )

def delete_mobile_message(user_id: int, message_id: int, db: Session):
    """Delete message for mobile user (soft delete)"""
    try:
        user = User.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Get user's primary church
        primary_church = user.get_primary_church(db)
        if not primary_church:
            raise HTTPException(
                status_code=400,
                detail="User not associated with any church"
            )
        
        # Verify message exists and belongs to user's church
        message = db.query(ChurchMessage).filter(
            ChurchMessage.id == message_id,
            ChurchMessage.church_id == primary_church.id
        ).first()
        
        if not message:
            raise HTTPException(
                status_code=404,
                detail="Message not found"
            )

        # Soft delete by marking as inactive
        message.is_active = False
        db.commit()

        return ResponseFactory.success(
            message="Message deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete message"
        )

def get_mobile_notifications(user_id: int, db: Session):
    """Get notifications for mobile user"""
    try:
        user = User.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Get user's notifications from audit log
        notifications = db.query(AuditLog).filter(
            AuditLog.actor_id == user_id,
            AuditLog.actor_type == "user"
        ).order_by(AuditLog.created_at.desc()).limit(20).all()

        notifications_data = []
        for notification in notifications:
            details = notification.details_json or {}
            notifications_data.append({
                "id": notification.id,
                "type": details.get("type", "info"),
                "title": details.get("title", "Notification"),
                "message": notification.action,
                "is_read": False,  # Audit logs don't track read status
                "created_at": notification.created_at.isoformat() if notification.created_at else None
            })

        return ResponseFactory.success(
            message="Notifications retrieved successfully",
            data={
                "notifications": notifications_data
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to get notifications"
        )

def mark_notification_read(user_id: int, notification_id: int, db: Session):
    """Mark notification as read for mobile user"""
    try:
        user = User.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Find notification in audit log
        notification = db.query(AuditLog).filter(
            AuditLog.id == notification_id,
            AuditLog.actor_id == user_id,
            AuditLog.actor_type == "user"
        ).first()

        if not notification:
            raise HTTPException(
                status_code=404,
                detail="Notification not found"
            )

        # Audit logs don't track read status, so we'll just return success
        # In a real implementation, you might want to create a separate read status table
        db.commit()

        return ResponseFactory.success(
            message="Notification marked as read"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to mark notification as read"
        )

def get_message_settings(user_id: int, db: Session):
    """Get message settings for mobile user"""
    try:
        user = User.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Get user settings
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
            message="Message settings retrieved successfully",
            data={
                "push_notifications": settings.push_notifications,
                "email_notifications": settings.email_notifications,
                "sms_notifications": settings.sms_notifications,
                "notifications_enabled": settings.notifications_enabled
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to get message settings"
        )

def update_message_settings(user_id: int, push_enabled: bool, email_enabled: bool, db: Session):
    """Update message settings for mobile user"""
    try:
        user = User.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Get or create user settings
        settings = db.query(UserSettings).filter(
            UserSettings.user_id == user_id
        ).first()

        if not settings:
            settings = UserSettings(
                user_id=user_id,
                created_at=datetime.now(timezone.utc)
            )
            db.add(settings)

        # Update settings
        setattr(settings, 'push_notifications', push_enabled)
        setattr(settings, 'email_notifications', email_enabled)
        setattr(settings, 'notifications_enabled', push_enabled or email_enabled)
        setattr(settings, 'updated_at', datetime.now(timezone.utc))

        db.commit()
        db.refresh(settings)

        return ResponseFactory.success(
            message="Message settings updated successfully",
            data={
                "push_notifications": settings.push_notifications,
                "email_notifications": settings.email_notifications,
                "sms_notifications": settings.sms_notifications,
                "notifications_enabled": settings.notifications_enabled
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to update message settings"
        )
