"""
Database Notification Service

Replaces Firebase push notifications with a comprehensive database-based notification system.
Handles creation, delivery, and management of notifications through the database.
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.model.m_church_message import ChurchMessage, MessageType, MessagePriority
from app.model.m_user_message import UserMessage
from app.model.m_church_admin import ChurchAdmin
from app.model.m_user import User
from app.model.m_audit_log import AuditLog
from app.model.m_user_settings import UserSettings
from app.utils.send_email import send_email_with_sendgrid
from app.utils.send_sms import send_sms_with_twilio


class DatabaseNotificationService:
    """Service for handling database-based notifications"""
    
    @staticmethod
    def create_church_notification(
        church_id: int,
        title: str,
        content: str,
        message_type: MessageType = MessageType.GENERAL,
        priority: MessagePriority = MessagePriority.MEDIUM,
        db: Session = None,
        send_external: bool = True
    ) -> Dict[str, Any]:
        """
        Create a notification for all church members
        
        Args:
            church_id: ID of the church
            title: Notification title
            content: Notification content
            message_type: Type of message (announcement, event, etc.)
            priority: Priority level (low, medium, high, urgent)
            db: Database session
            send_external: Whether to send email/SMS notifications
            
        Returns:
            Dict with notification details and delivery status
        """
        try:
            # Create church message
            church_message = ChurchMessage(
                church_id=church_id,
                title=title,
                content=content,
                type=message_type,
                priority=priority,
                is_active=True,
                is_published=True,
                published_at=datetime.now(timezone.utc)
            )
            db.add(church_message)
            db.flush()  # Get the message ID
            
            # Get all church admins
            church_admins = db.query(ChurchAdmin).filter(
                ChurchAdmin.church_id == church_id,
                ChurchAdmin.is_active == True
            ).all()
            
            delivered_count = 0
            email_sent_count = 0
            sms_sent_count = 0
            
            # Send to all church admins
            for admin in church_admins:
                # Create user message record
                user_message = UserMessage(
                    user_id=admin.user_id,
                    message_id=church_message.id,
                    is_read=False,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(user_message)
                delivered_count += 1
                
                # Send external notifications if enabled
                if send_external:
                    user = admin.user
                    if user:
                        # Get user notification preferences
                        settings = db.query(UserSettings).filter(
                            UserSettings.user_id == user.id
                        ).first()
                        
                        # Send email notification if enabled
                        if settings and settings.email_notifications and user.email:
                            email_body = f"""
                            <html>
                                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                                    <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px;">
                                        <h2 style="color: #6366F1; margin-bottom: 20px;">{title}</h2>
                                        <div style="background-color: #ffffff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                            <p style="font-size: 16px; color: #6b7280; margin-bottom: 10px;">Dear {user.first_name or 'Church Administrator'},</p>
                                            <p style="font-size: 16px; color: #6b7280; margin-bottom: 10px;">{content}</p>
                                            <p style="font-size: 16px; color: #6b7280; margin-bottom: 10px;">Best regards,<br>The Manna Team</p>
                                        </div>
                                    </div>
                                </body>
                            </html>
                            """
                            
                            if send_email_with_sendgrid(
                                to_email=user.email,
                                subject=f"Church Notification: {title}",
                                body_html=email_body
                            ):
                                email_sent_count += 1
                        
                        # Send SMS notification if enabled and urgent
                        if (settings and settings.sms_notifications and 
                            user.phone and priority == MessagePriority.URGENT):
                            sms_message = f"URGENT: {title}\n\n{content[:140]}..."
                            if send_sms_with_twilio(user.phone, sms_message):
                                sms_sent_count += 1
            
            db.commit()
            
            # Create audit log
            audit_log = AuditLog(
                actor_type="system",
                action="CHURCH_NOTIFICATION_SENT",
                resource_type="church",
                resource_id=church_id,
                additional_data={
                    "message_id": church_message.id,
                    "title": title,
                    "type": message_type.value,
                    "priority": priority.value,
                    "delivered_count": delivered_count,
                    "email_sent_count": email_sent_count,
                    "sms_sent_count": sms_sent_count
                }
            )
            db.add(audit_log)
            db.commit()
            
            logging.info(f"Church notification sent: {title} to {delivered_count} users")
            
            return {
                "success": True,
                "message_id": church_message.id,
                "delivered_count": delivered_count,
                "email_sent_count": email_sent_count,
                "sms_sent_count": sms_sent_count
            }
            
        except Exception as e:
            logging.error(f"Error creating church notification: {str(e)}")
            db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def create_user_notification(
        user_id: int,
        title: str,
        content: str,
        notification_type: str = "info",
        db: Session = None,
        send_external: bool = True
    ) -> Dict[str, Any]:
        """
        Create a notification for a specific user
        
        Args:
            user_id: ID of the user
            title: Notification title
            content: Notification content
            notification_type: Type of notification (info, warning, error, success)
            db: Database session
            send_external: Whether to send email/SMS notifications
            
        Returns:
            Dict with notification details and delivery status
        """
        try:
            # Create audit log entry for user notification
            audit_log = AuditLog(
                actor_type="system",
                actor_id=user_id,
                action="USER_NOTIFICATION",
                details_json={
                    "type": notification_type,
                    "title": title,
                    "content": content,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            db.add(audit_log)
            
            # Send external notifications if enabled
            email_sent = False
            sms_sent = False
            
            if send_external:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    # Get user notification preferences
                    settings = db.query(UserSettings).filter(
                        UserSettings.user_id == user_id
                    ).first()
                    
                    # Send email notification if enabled
                    if settings and settings.email_notifications and user.email:
                        email_body = f"""
                        <html>
                            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                                <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px;">
                                    <h2 style="color: #6366F1; margin-bottom: 20px;">{title}</h2>
                                    <div style="background-color: #ffffff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                        <p style="font-size: 16px; color: #6b7280; margin-bottom: 10px;">Dear {user.first_name or 'User'},</p>
                                        <p style="font-size: 16px; color: #6b7280; margin-bottom: 10px;">{content}</p>
                                        <p style="font-size: 16px; color: #6b7280; margin-bottom: 10px;">Best regards,<br>The Manna Team</p>
                                    </div>
                                </div>
                            </body>
                        </html>
                        """
                        
                        email_sent = send_email_with_sendgrid(
                            to_email=user.email,
                            subject=f"Notification: {title}",
                            body_html=email_body
                        )
                    
                    # Send SMS notification if enabled and high priority
                    if (settings and settings.sms_notifications and 
                        user.phone and notification_type in ["warning", "error"]):
                        sms_message = f"{title}\n\n{content[:140]}..."
                        sms_sent = send_sms_with_twilio(user.phone, sms_message)
            
            db.commit()
            
            logging.info(f"User notification sent: {title} to user {user_id}")
            
            return {
                "success": True,
                "notification_id": audit_log.id,
                "email_sent": email_sent,
                "sms_sent": sms_sent
            }
            
        except Exception as e:
            logging.error(f"Error creating user notification: {str(e)}")
            db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_user_notifications(
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Get notifications for a user with optimized queries
        
        Args:
            user_id: ID of the user
            limit: Maximum number of notifications to return
            offset: Offset for pagination
            unread_only: Whether to return only unread notifications
            db: Database session
            
        Returns:
            Dict with notifications and metadata
        """
        try:
            from sqlalchemy import and_, or_, desc, func
            
            # Get church messages with church message details in one query
            church_messages_query = db.query(
                UserMessage.id.label('user_message_id'),
                UserMessage.is_read,
                UserMessage.read_at,
                UserMessage.created_at.label('user_message_created_at'),
                ChurchMessage.id.label('church_message_id'),
                ChurchMessage.title,
                ChurchMessage.content,
                ChurchMessage.type,
                ChurchMessage.priority,
                ChurchMessage.created_at.label('church_message_created_at')
            ).join(
                ChurchMessage, UserMessage.message_id == ChurchMessage.id
            ).filter(
                UserMessage.user_id == user_id
            )
            
            if unread_only:
                church_messages_query = church_messages_query.filter(UserMessage.is_read == False)
            
            church_messages = church_messages_query.order_by(
                desc(UserMessage.created_at)
            ).all()
            
            # Get audit log notifications for user
            audit_notifications_query = db.query(AuditLog).filter(
                AuditLog.actor_id == user_id,
                AuditLog.action == "USER_NOTIFICATION"
            )
            
            audit_notifications = audit_notifications_query.order_by(
                desc(AuditLog.created_at)
            ).all()
            
            notifications = []
            
            # Process church messages
            for msg in church_messages:
                notifications.append({
                    "id": f"church_{msg.user_message_id}",
                    "type": "church_message",
                    "title": msg.title or "Church Message",
                    "content": msg.content or "",
                    "message_type": msg.type.value if msg.type else "general",
                    "priority": msg.priority.value if msg.priority else "medium",
                    "is_read": msg.is_read,
                    "read_at": msg.read_at.isoformat() if msg.read_at else None,
                    "created_at": msg.user_message_created_at.isoformat() if msg.user_message_created_at else None,
                    "church_message_id": msg.church_message_id
                })
            
            # Process audit log notifications
            for audit_log in audit_notifications:
                details = audit_log.details_json or {}
                notifications.append({
                    "id": f"audit_{audit_log.id}",
                    "type": "system_notification",
                    "title": details.get("title", "System Notification"),
                    "content": details.get("content", audit_log.action),
                    "message_type": details.get("type", "info"),
                    "priority": details.get("priority", "medium"),
                    "is_read": False,  # Audit logs don't track read status
                    "read_at": None,
                    "created_at": audit_log.created_at.isoformat() if audit_log.created_at else None,
                    "audit_log_id": audit_log.id
                })
            
            # Sort by created_at (most recent first)
            notifications.sort(key=lambda x: x["created_at"] or "1970-01-01T00:00:00", reverse=True)
            
            # Apply pagination to combined results
            total_count = len(notifications)
            paginated_notifications = notifications[offset:offset + limit]
            
            # Get unread count for church messages only (audit logs don't track read status)
            unread_count = db.query(UserMessage).filter(
                UserMessage.user_id == user_id,
                UserMessage.is_read == False
            ).count()
            
            return {
                "success": True,
                "notifications": paginated_notifications,
                "total_count": total_count,
                "unread_count": unread_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count
            }
            
        except Exception as e:
            logging.error(f"Error getting user notifications for user {user_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "notifications": [],
                "total_count": 0,
                "unread_count": 0,
                "limit": limit,
                "offset": offset,
                "has_more": False
            }
    
    @staticmethod
    def mark_notification_read(
        user_id: int,
        notification_id: str,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Mark a notification as read
        
        Args:
            user_id: ID of the user
            notification_id: ID of the notification (format: "church_123" or "audit_456")
            db: Database session
            
        Returns:
            Dict with success status
        """
        try:
            if notification_id.startswith("church_"):
                # Handle church message
                user_message_id = int(notification_id.replace("church_", ""))
                user_message = db.query(UserMessage).filter(
                    UserMessage.id == user_message_id,
                    UserMessage.user_id == user_id
                ).first()
                
                if user_message:
                    user_message.is_read = True
                    user_message.read_at = datetime.now(timezone.utc)
                    db.commit()
                    return {"success": True, "message": "Church message marked as read"}
                else:
                    return {"success": False, "error": "Church message not found"}
            
            elif notification_id.startswith("audit_"):
                # Audit log notifications don't have read status
                # Just return success for compatibility
                return {"success": True, "message": "System notification acknowledged"}
            
            else:
                return {"success": False, "error": "Invalid notification ID format"}
                
        except Exception as e:
            logging.error(f"Error marking notification as read: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def send_donation_confirmation(
        user_id: int,
        church_name: str,
        amount: float,
        donation_type: str = "roundup",
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Send donation confirmation notification
        
        Args:
            user_id: ID of the user who made the donation
            church_name: Name of the church that received the donation
            amount: Donation amount
            donation_type: Type of donation (roundup, direct, etc.)
            db: Database session
            
        Returns:
            Dict with notification status
        """
        title = "Donation Confirmed"
        content = f"Your ${amount:.2f} {donation_type} donation to {church_name} has been processed successfully. Thank you for your generosity!"
        
        return DatabaseNotificationService.create_user_notification(
            user_id=user_id,
            title=title,
            content=content,
            notification_type="success",
            db=db,
            send_external=True
        )
    
    @staticmethod
    def send_payout_notification(
        church_id: int,
        amount: float,
        payout_date: datetime,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Send payout notification to church admins
        
        Args:
            church_id: ID of the church receiving the payout
            amount: Payout amount
            payout_date: Date of the payout
            db: Database session
            
        Returns:
            Dict with notification status
        """
        title = "Payout Processed"
        content = f"A payout of ${amount:.2f} has been processed to your church account on {payout_date.strftime('%B %d, %Y')}. The funds should appear in your bank account within 1-2 business days."
        
        return DatabaseNotificationService.create_church_notification(
            church_id=church_id,
            title=title,
            content=content,
            message_type=MessageType.ANNOUNCEMENT,
            priority=MessagePriority.HIGH,
            db=db,
            send_external=True
        )
    
    @staticmethod
    def create_sample_notifications(user_id: int, db: Session = None) -> Dict[str, Any]:
        """
        Create sample notifications for testing purposes
        
        Args:
            user_id: ID of the user
            db: Database session
            
        Returns:
            Dict with creation status
        """
        try:
            # Create sample church message
            church_message = ChurchMessage(
                church_id=1,  # Assuming church ID 1 exists
                title="Welcome to Manna!",
                content="Thank you for joining our church community. We're excited to have you as part of our family!",
                type=MessageType.WELCOME,
                priority=MessagePriority.HIGH,
                is_active=True,
                is_published=True,
                published_at=datetime.now(timezone.utc)
            )
            db.add(church_message)
            db.flush()
            
            # Create user message
            user_message = UserMessage(
                user_id=user_id,
                message_id=church_message.id,
                is_read=False,
                created_at=datetime.now(timezone.utc)
            )
            db.add(user_message)
            
            # Create sample audit log notification
            audit_log = AuditLog(
                actor_type="system",
                actor_id=user_id,
                action="USER_NOTIFICATION",
                details_json={
                    "title": "Account Setup Complete",
                    "content": "Your Manna account has been successfully set up. You can now start making donations and managing your giving preferences.",
                    "type": "success",
                    "priority": "medium"
                }
            )
            db.add(audit_log)
            
            db.commit()
            
            return {
                "success": True,
                "message": "Sample notifications created successfully",
                "church_message_id": church_message.id,
                "user_message_id": user_message.id,
                "audit_log_id": audit_log.id
            }
            
        except Exception as e:
            logging.error(f"Error creating sample notifications: {str(e)}")
            db.rollback()
            return {
                "success": False,
                "error": str(e)
            }


# Create service instance
database_notification_service = DatabaseNotificationService()
