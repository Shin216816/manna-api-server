"""
Profile Schemas

Defines request and response schemas for profile endpoints:
- Profile preferences
- Security settings
- Data management
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ProfilePreferencesRequest(BaseModel):
    """Profile preferences update request"""
    push_notifications: Optional[bool] = Field(None, description="Enable push notifications")
    email_notifications: Optional[bool] = Field(None, description="Enable email notifications")
    sms_notifications: Optional[bool] = Field(None, description="Enable SMS notifications")
    donation_reminders: Optional[bool] = Field(None, description="Enable donation reminders")
    roundup_updates: Optional[bool] = Field(None, description="Enable roundup updates")
    church_messages: Optional[bool] = Field(None, description="Enable church messages")
    weekly_summary: Optional[bool] = Field(None, description="Enable weekly summary")
    monthly_report: Optional[bool] = Field(None, description="Enable monthly report")
    impact_updates: Optional[bool] = Field(None, description="Enable impact updates")


class SecuritySettingsRequest(BaseModel):
    """Security settings update request"""
    new_password: Optional[str] = Field(None, description="New password")
    current_password: Optional[str] = Field(None, description="Current password for verification")
    two_factor_enabled: Optional[bool] = Field(None, description="Enable two-factor authentication")
    login_notifications: Optional[bool] = Field(None, description="Enable login notifications")
    session_timeout: Optional[int] = Field(None, description="Session timeout in minutes")


class DeletionRequestRequest(BaseModel):
    """Account deletion request"""
    reason: str = Field(..., description="Reason for account deletion")
    feedback: Optional[str] = Field(None, description="Additional feedback")
    data_retention: Optional[bool] = Field(False, description="Request data retention")


class ProfileStatsResponse(BaseModel):
    """Profile statistics response"""
    user_id: int = Field(..., description="User ID")
    total_donations: int = Field(..., description="Total number of donations")
    total_amount: float = Field(..., description="Total amount donated")
    this_year_amount: float = Field(..., description="Amount donated this year")
    average_per_donation: float = Field(..., description="Average amount per donation")
    member_since: Optional[str] = Field(None, description="Member since date")
    last_donation_date: Optional[str] = Field(None, description="Last donation date")
    days_since_last_donation: Optional[int] = Field(None, description="Days since last donation")


class SecuritySettingsResponse(BaseModel):
    """Security settings response"""
    user_id: int = Field(..., description="User ID")
    has_password: bool = Field(..., description="Whether user has password set")
    is_email_verified: bool = Field(..., description="Whether email is verified")
    is_phone_verified: bool = Field(..., description="Whether phone is verified")
    last_login: Optional[str] = Field(None, description="Last login timestamp")
    account_created: Optional[str] = Field(None, description="Account creation timestamp")
    last_updated: Optional[str] = Field(None, description="Last update timestamp")
