"""
Notification Helper Utilities

Helper functions for sending various types of notifications using the database notification system.
Replaces Firebase push notification functionality with database-based notifications.
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.services.database_notification_service import database_notification_service
from app.model.m_church_message import MessageType, MessagePriority


def send_donation_notification(
    user_id: int,
    church_name: str,
    amount: float,
    donation_type: str = "roundup",
    db: Session = None
) -> bool:
    """
    Send donation confirmation notification to user
    
    Args:
        user_id: ID of the user who made the donation
        church_name: Name of the church
        amount: Donation amount
        donation_type: Type of donation
        db: Database session
        
    Returns:
        bool: Success status
    """
    result = database_notification_service.send_donation_confirmation(
        user_id=user_id,
        church_name=church_name,
        amount=amount,
        donation_type=donation_type,
        db=db
    )
    return result.get("success", False)


def send_payout_notification(
    church_id: int,
    amount: float,
    payout_date,
    db: Session = None
) -> bool:
    """
    Send payout notification to church admins
    
    Args:
        church_id: ID of the church
        amount: Payout amount
        payout_date: Date of payout
        db: Database session
        
    Returns:
        bool: Success status
    """
    result = database_notification_service.send_payout_notification(
        church_id=church_id,
        amount=amount,
        payout_date=payout_date,
        db=db
    )
    return result.get("success", False)


def send_kyc_status_notification(
    church_id: int,
    status: str,
    message: str,
    db: Session = None
) -> bool:
    """
    Send KYC status update notification to church admins
    
    Args:
        church_id: ID of the church
        status: KYC status
        message: Status message
        db: Database session
        
    Returns:
        bool: Success status
    """
    title = f"KYC Status Update: {status.replace('_', ' ').title()}"
    priority = MessagePriority.HIGH if status in ["APPROVED", "REJECTED"] else MessagePriority.MEDIUM
    
    result = database_notification_service.create_church_notification(
        church_id=church_id,
        title=title,
        content=message,
        message_type=MessageType.ANNOUNCEMENT,
        priority=priority,
        db=db,
        send_external=True
    )
    return result.get("success", False)


def send_system_notification(
    user_id: int,
    title: str,
    message: str,
    notification_type: str = "info",
    db: Session = None
) -> bool:
    """
    Send system notification to a specific user
    
    Args:
        user_id: ID of the user
        title: Notification title
        message: Notification message
        notification_type: Type of notification
        db: Database session
        
    Returns:
        bool: Success status
    """
    result = database_notification_service.create_user_notification(
        user_id=user_id,
        title=title,
        content=message,
        notification_type=notification_type,
        db=db,
        send_external=True
    )
    return result.get("success", False)


def send_church_announcement(
    church_id: int,
    title: str,
    message: str,
    priority: MessagePriority = MessagePriority.MEDIUM,
    db: Session = None
) -> bool:
    """
    Send announcement to all church members
    
    Args:
        church_id: ID of the church
        title: Announcement title
        message: Announcement message
        priority: Priority level
        db: Database session
        
    Returns:
        bool: Success status
    """
    result = database_notification_service.create_church_notification(
        church_id=church_id,
        title=title,
        content=message,
        message_type=MessageType.ANNOUNCEMENT,
        priority=priority,
        db=db,
        send_external=True
    )
    return result.get("success", False)


def send_roundup_summary(
    user_id: int,
    total_amount: float,
    transaction_count: int,
    church_name: str,
    period: str = "weekly",
    db: Session = None
) -> bool:
    """
    Send roundup summary notification to user
    
    Args:
        user_id: ID of the user
        total_amount: Total roundup amount
        transaction_count: Number of transactions
        church_name: Name of the church
        period: Summary period (weekly, monthly)
        db: Database session
        
    Returns:
        bool: Success status
    """
    title = f"{period.title()} Roundup Summary"
    message = f"Your {period} roundup donations totaled ${total_amount:.2f} across {transaction_count} transactions to {church_name}. Thank you for your consistent generosity!"
    
    result = database_notification_service.create_user_notification(
        user_id=user_id,
        title=title,
        content=message,
        notification_type="success",
        db=db,
        send_external=True
    )
    return result.get("success", False)


def send_referral_notification(
    church_id: int,
    referred_church_name: str,
    commission_amount: float,
    db: Session = None
) -> bool:
    """
    Send referral commission notification to church
    
    Args:
        church_id: ID of the referring church
        referred_church_name: Name of the referred church
        commission_amount: Commission amount
        db: Database session
        
    Returns:
        bool: Success status
    """
    title = "Referral Commission Earned"
    message = f"Congratulations! You've earned a ${commission_amount:.2f} referral commission for successfully referring {referred_church_name} to our platform."
    
    result = database_notification_service.create_church_notification(
        church_id=church_id,
        title=title,
        content=message,
        message_type=MessageType.ANNOUNCEMENT,
        priority=MessagePriority.HIGH,
        db=db,
        send_external=True
    )
    return result.get("success", False)
