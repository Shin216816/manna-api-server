"""
Notification Schemas

Defines request and response schemas for notification endpoints:
- Notification preferences
- Notification management
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class NotificationPreferencesRequest(BaseModel):
    """Notification preferences update request"""
    push_notifications: Optional[bool] = Field(None, description="Enable push notifications")
    email_notifications: Optional[bool] = Field(None, description="Enable email notifications")
    sms_notifications: Optional[bool] = Field(None, description="Enable SMS notifications")
    donation_reminders: Optional[bool] = Field(None, description="Enable donation reminders")
    roundup_updates: Optional[bool] = Field(None, description="Enable roundup updates")
    church_messages: Optional[bool] = Field(None, description="Enable church messages")
    weekly_summary: Optional[bool] = Field(None, description="Enable weekly summary")
    monthly_report: Optional[bool] = Field(None, description="Enable monthly report")
    impact_updates: Optional[bool] = Field(None, description="Enable impact updates")


class NotificationResponse(BaseModel):
    """Notification response model"""
    id: int = Field(..., description="Notification ID")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    type: str = Field(..., description="Notification type")
    is_read: bool = Field(..., description="Whether notification is read")
    created_at: str = Field(..., description="Creation timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class NotificationListResponse(BaseModel):
    """Notification list response model"""
    notifications: List[NotificationResponse] = Field(..., description="List of notifications")
    total_count: int = Field(..., description="Total number of notifications")
    unread_count: int = Field(..., description="Number of unread notifications")
