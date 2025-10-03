"""
Church Notification Service

Handles sending messages and emails to church administrators when church data is changed by internal admin.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.model.m_church import Church
from app.model.m_church_admin import ChurchAdmin
from app.model.m_church_message import ChurchMessage, MessageType, MessagePriority
from app.model.m_user import User
from app.utils.send_email import send_email_with_sendgrid
from app.core.responses import ResponseFactory

logger = logging.getLogger(__name__)

class ChurchNotificationService:
    """Service for sending church notifications when data is changed by internal admin"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def send_church_data_change_notification(
        self,
        church_id: int,
        admin_id: int,
        changed_fields: List[str],
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        admin_name: str = "Internal Admin"
    ) -> Dict[str, Any]:
        """
        Send notification to church administrators when church data is changed by internal admin
        
        Args:
            church_id: ID of the church
            admin_id: ID of the admin who made the change
            changed_fields: List of fields that were changed
            old_values: Dictionary of old values
            new_values: Dictionary of new values
            admin_name: Name of the admin who made the change
            
        Returns:
            Dict with notification results
        """
        try:
            # Get church information
            church = self.db.query(Church).filter(Church.id == church_id).first()
            if not church:
                return {
                    "success": False,
                    "message": "Church not found"
                }
            
            # Get church administrators
            church_admins = self.db.query(ChurchAdmin).filter(
                ChurchAdmin.church_id == church_id,
                ChurchAdmin.is_active == True
            ).all()
            
            if not church_admins:
                return {
                    "success": False,
                    "message": "No active church administrators found"
                }
            
            # Create notification content
            title = f"Church Profile Updated by {admin_name}"
            content = self._create_change_notification_content(
                church_name=church.name,
                changed_fields=changed_fields,
                old_values=old_values,
                new_values=new_values,
                admin_name=admin_name
            )
            
            # Create church message
            church_message = ChurchMessage(
                church_id=church_id,
                title=title,
                content=content,
                type=MessageType.ANNOUNCEMENT,
                priority=MessagePriority.MEDIUM,
                is_active=True,
                is_published=True,
                published_at=datetime.now(timezone.utc)
            )
            
            self.db.add(church_message)
            self.db.flush()  # Get the message ID
            
            # Send notifications to all church administrators
            email_sent_count = 0
            message_created_count = 0
            
            for church_admin in church_admins:
                try:
                    # Get user details
                    user = self.db.query(User).filter(User.id == church_admin.user_id).first()
                    if not user or not user.email:
                        continue
                    
                    # Send email notification
                    email_success = self._send_change_notification_email(
                        to_email=user.email,
                        church_name=church.name,
                        user_name=user.first_name or "Church Administrator",
                        changed_fields=changed_fields,
                        old_values=old_values,
                        new_values=new_values,
                        admin_name=admin_name
                    )
                    
                    if email_success:
                        email_sent_count += 1
                    
                    message_created_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to send notification to church admin {church_admin.id}: {str(e)}")
                    continue
            
            self.db.commit()
            
            return {
                "success": True,
                "message": "Church data change notifications sent successfully",
                "data": {
                    "message_id": church_message.id,
                    "church_id": church_id,
                    "church_name": church.name,
                    "total_admins": len(church_admins),
                    "emails_sent": email_sent_count,
                    "messages_created": message_created_count,
                    "changed_fields": changed_fields
                }
            }
            
        except Exception as e:
            logger.error(f"Error sending church data change notification: {str(e)}")
            self.db.rollback()
            return {
                "success": False,
                "message": f"Failed to send notifications: {str(e)}"
            }
    
    def _create_change_notification_content(
        self,
        church_name: str,
        changed_fields: List[str],
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        admin_name: str
    ) -> str:
        """Create the content for the change notification message"""
        
        # Field display names
        field_names = {
            "name": "Church Name",
            "email": "Email Address",
            "phone": "Phone Number",
            "website": "Website",
            "address": "Address",
            "city": "City",
            "state": "State",
            "zip_code": "ZIP Code",
            "country": "Country"
        }
        
        content = f"Your church profile has been updated by {admin_name} from the Manna Internal Admin team.\n\n"
        content += f"Church: {church_name}\n\n"
        content += "The following information has been changed:\n\n"
        
        for field in changed_fields:
            field_display = field_names.get(field, field.replace('_', ' ').title())
            old_value = old_values.get(field, 'Not set')
            new_value = new_values.get(field, 'Not set')
            
            content += f"• {field_display}:\n"
            content += f"  - Previous: {old_value}\n"
            content += f"  - Updated: {new_value}\n\n"
        
        content += "If you have any questions about these changes, please contact our support team.\n\n"
        content += "Best regards,\nThe Manna Team"
        
        return content
    
    def _send_change_notification_email(
        self,
        to_email: str,
        church_name: str,
        user_name: str,
        changed_fields: List[str],
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        admin_name: str
    ) -> bool:
        """Send email notification about church data changes"""
        
        # Field display names
        field_names = {
            "name": "Church Name",
            "email": "Email Address",
            "phone": "Phone Number",
            "website": "Website",
            "address": "Address",
            "city": "City",
            "state": "State",
            "zip_code": "ZIP Code",
            "country": "Country"
        }
        
        # Create HTML email content
        changes_html = ""
        for field in changed_fields:
            field_display = field_names.get(field, field.replace('_', ' ').title())
            old_value = old_values.get(field, 'Not set')
            new_value = new_values.get(field, 'Not set')
            
            changes_html += f"""
            <div style="margin-bottom: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 8px; border-left: 4px solid #6366F1;">
                <h4 style="margin: 0 0 10px 0; color: #374151; font-size: 16px;">{field_display}</h4>
                <div style="margin-bottom: 8px;">
                    <strong style="color: #6b7280;">Previous:</strong> 
                    <span style="color: #dc2626;">{old_value}</span>
                </div>
                <div>
                    <strong style="color: #6b7280;">Updated:</strong> 
                    <span style="color: #059669;">{new_value}</span>
                </div>
            </div>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Church Profile Updated</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #374151; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #ffffff; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden;">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%); padding: 30px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">
                        Church Profile Updated
                    </h1>
                    <p style="color: #e0e7ff; margin: 10px 0 0 0; font-size: 16px;">
                        Your church information has been updated by our admin team
                    </p>
                </div>
                
                <!-- Content -->
                <div style="padding: 30px;">
                    <p style="font-size: 16px; margin-bottom: 20px;">
                        Hello {user_name},
                    </p>
                    
                    <p style="font-size: 16px; margin-bottom: 25px;">
                        Your church profile for <strong>{church_name}</strong> has been updated by <strong>{admin_name}</strong> from the Manna Internal Admin team.
                    </p>
                    
                    <h2 style="color: #374151; font-size: 18px; margin-bottom: 20px; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px;">
                        Changes Made
                    </h2>
                    
                    {changes_html}
                    
                    <div style="background-color: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 15px; margin: 25px 0;">
                        <p style="margin: 0; color: #92400e; font-size: 14px;">
                            <strong>Note:</strong> If you have any questions about these changes or need to make additional updates, please contact our support team.
                        </p>
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <a href="https://manna.com/support" 
                           style="display: inline-block; background-color: #6366F1; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 500;">
                            Contact Support
                        </a>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background-color: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                    <p style="margin: 0; color: #6b7280; font-size: 14px;">
                        Best regards,<br>
                        The Manna Team
                    </p>
                    <p style="margin: 10px 0 0 0; color: #9ca3af; font-size: 12px;">
                        This is an automated notification. Please do not reply to this email.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send email using SendGrid
        try:
            success = send_email_with_sendgrid(
                to_email=to_email,
                subject=f"Church Profile Updated - {church_name}",
                body_html=html_content
            )
            
            if success:
                logger.info(f"Church data change email sent successfully to {to_email}")
            else:
                logger.error(f"Failed to send church data change email to {to_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending church data change email to {to_email}: {str(e)}")
            return False
