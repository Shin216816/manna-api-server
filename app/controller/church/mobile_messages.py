import logging
from sqlalchemy.orm import Session
from typing import Optional
from app.model.m_church import Church
from app.model.m_church_message import ChurchMessage
from app.model.m_user import User
from app.model.m_user_message import UserMessage
from app.core.responses import ResponseFactory
from datetime import datetime
from sqlalchemy import func


def get_mobile_church_messages(
    user_id: int, limit: int = 20, offset: int = 0, db: Optional[Session] = None
):
    """Get church messages for donor"""
    if db is None:
        return ResponseFactory.error(message="Database session required")
    try:
        # Get messages for the user through user_messages table
        messages = (
            db.query(ChurchMessage, UserMessage)
            .join(UserMessage, ChurchMessage.id == UserMessage.message_id)
            .filter(UserMessage.user_id == user_id)
            .filter(ChurchMessage.is_active == True)
            .order_by(ChurchMessage.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        message_list = []
        for church_message, user_message in messages:
            # Get church name
            church = db.query(Church).filter_by(id=church_message.church_id).first()
            church_name = church.name if church else "Unknown Church"
            
            message_list.append(
                {
                    "id": church_message.id,
                    "church_name": church_name,
                    "title": church_message.title,
                    "message": church_message.content,
                    "type": church_message.type,
                    "date": church_message.created_at.isoformat(),
                    "is_read": user_message.is_read,
                    "read_at": user_message.read_at.isoformat() if user_message.read_at else None,
                }
            )

        # Get total count for pagination
        total_count = (
            db.query(func.count(UserMessage.id))
            .join(ChurchMessage, ChurchMessage.id == UserMessage.message_id)
            .filter(UserMessage.user_id == user_id)
            .filter(ChurchMessage.is_active == True)
            .scalar()
            or 0
        )

        return ResponseFactory.success(
            message="Church messages retrieved",
            data={"messages": message_list, "total_count": total_count},
        )

    except Exception as e:
        logging.error(f"Error retrieving church messages: {str(e)}")
        return ResponseFactory.error(
            message="Error retrieving church messages",
            data={"messages": [], "total_count": 0},
        )


def send_mobile_church_message(
    church_id: int,
    recipient_id: int,
    title: str,
    content: str,
    message_type: str = "general",
    db: Optional[Session] = None,
):
    """Send a message from church to donor (for church admins)"""
    if db is None:
        return ResponseFactory.error(message="Database session required")
    try:
        # Validate message type
        valid_types = ["general", "announcement", "event", "prayer_request"]
        if message_type not in valid_types:
            return ResponseFactory.error(
                message=f"Invalid message type. Must be one of: {', '.join(valid_types)}",
                error_code="400",
            )

        # Verify church exists
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            return ResponseFactory.error(message="Church not found", error_code="404")

        # Verify recipient exists
        recipient = db.query(User).filter_by(id=recipient_id).first()
        if not recipient:
            return ResponseFactory.error(
                message="Recipient not found", error_code="404"
            )

        # Create the church message
        message = ChurchMessage(
            church_id=church_id,
            title=title,
            content=content,
            type=message_type,
            is_active=True,
            is_published=True,
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        # Create the user message link to track the specific donor
        user_message = UserMessage(
            user_id=recipient_id,
            message_id=message.id,
            is_read=False
        )

        db.add(user_message)
        db.commit()
        db.refresh(user_message)

        return ResponseFactory.success(
            message="Message sent successfully",
            data={
                "message_id": message.id,
                "church_name": church.name,
                "recipient_name": f"{recipient.first_name} {recipient.last_name}".strip(),
                "title": title,  # Return original title without recipient prefix
                "content": message.content,
                "type": message.type,
                "date": message.created_at.isoformat(),
            },
        )

    except Exception as e:

        return ResponseFactory.error(message="Error sending message", error_code="500")


def get_donor_message_history(
    church_id: int,
    donor_id: int,
    limit: int = 20,
    offset: int = 0,
    db: Optional[Session] = None,
):
    """Get message history for a specific donor from the church"""
    if db is None:
        return ResponseFactory.error(message="Database session required")
    try:
        # Verify church exists
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            return ResponseFactory.error(message="Church not found", error_code="404")

        # Verify donor exists
        donor = db.query(User).filter_by(id=donor_id).first()
        if not donor:
            return ResponseFactory.error(message="Donor not found", error_code="404")

        # Get messages sent to this donor by this church through user_messages table
        messages = (
            db.query(ChurchMessage, UserMessage)
            .join(UserMessage, ChurchMessage.id == UserMessage.message_id)
            .filter(
                ChurchMessage.church_id == church_id,
                UserMessage.user_id == donor_id,
                ChurchMessage.is_active == True
            )
            .order_by(ChurchMessage.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        message_list = []
        for church_message, user_message in messages:
            message_list.append(
                {
                    "id": church_message.id,
                    "title": church_message.title,
                    "content": church_message.content,
                    "type": church_message.type,
                    "date": church_message.created_at.isoformat(),
                    "is_read": user_message.is_read,
                    "read_at": user_message.read_at.isoformat() if user_message.read_at else None,
                }
            )

        # Get total count for pagination
        total_count = (
            db.query(func.count(UserMessage.id))
            .join(ChurchMessage, ChurchMessage.id == UserMessage.message_id)
            .filter(
                ChurchMessage.church_id == church_id,
                UserMessage.user_id == donor_id,
                ChurchMessage.is_active == True
            )
            .scalar()
            or 0
        )

        donor_name = f"{donor.first_name} {donor.last_name}".strip()

        return ResponseFactory.success(
            message="Donor message history retrieved successfully",
            data={
                "messages": message_list,
                "total_count": total_count,
                "donor_name": donor_name,
                "church_name": church.name,
            },
        )

    except Exception as e:
        logging.error(f"Error retrieving message history: {str(e)}")
        return ResponseFactory.error(
            message="Error retrieving message history", error_code="500"
        )


def mark_message_as_read(user_id: int, message_id: int, db: Session):
    """Mark a specific church message as read"""
    try:
        user_message = (
            db.query(UserMessage)
            .filter_by(message_id=message_id, user_id=user_id)
            .first()
        )

        if not user_message:
            return ResponseFactory.error(message="Message not found", error_code="404")

        user_message.is_read = True
        user_message.read_at = datetime.now()
        db.commit()

        return ResponseFactory.success(
            message="Message marked as read",
            data={"message_id": message_id, "is_read": True},
        )

    except Exception as e:
        logging.error(f"Error marking message as read: {str(e)}")
        return ResponseFactory.error(
            message="Error marking message as read", error_code="500"
        )


def mark_all_messages_as_read(user_id: int, db: Session):
    """Mark all unread church messages as read"""
    try:
        # Update all unread messages for this user
        updated_count = (
            db.query(UserMessage)
            .filter_by(user_id=user_id, is_read=False)
            .update({
                "is_read": True,
                "read_at": datetime.now()
            })
        )
        
        db.commit()

        return ResponseFactory.success(
            message="All messages marked as read",
            data={
                "updated_count": updated_count,
            },
        )

    except Exception as e:
        logging.error(f"Error marking messages as read: {str(e)}")
        return ResponseFactory.error(
            message="Error marking messages as read", error_code="500"
        )


def get_unread_message_count(user_id: int, db: Session):
    """Get count of unread church messages"""
    try:
        # Count unread messages for this user
        unread_count = (
            db.query(func.count(UserMessage.id))
            .filter_by(user_id=user_id, is_read=False)
            .scalar()
            or 0
        )

        return ResponseFactory.success(
            message="Unread count retrieved",
            data={
                "unread_count": unread_count,
            },
        )

    except Exception as e:
        logging.error(f"Error retrieving unread count: {str(e)}")
        return ResponseFactory.success(
            message="Error retrieving unread count", data={"unread_count": 0}
        )


def delete_mobile_message(user_id: int, message_id: int, db: Session):
    """Delete a specific church message for donor"""
    try:
        # Find the user_message record
        user_message = (
            db.query(UserMessage)
            .filter_by(message_id=message_id, user_id=user_id)
            .first()
        )

        if not user_message:
            return ResponseFactory.error(message="Message not found", error_code="404")

        # Delete the user_message record (this removes the link between user and message)
        db.delete(user_message)
        db.commit()

        return ResponseFactory.success(
            message="Message deleted successfully", data={"message_id": message_id}
        )

    except Exception as e:
        logging.error(f"Error deleting message: {str(e)}")
        return ResponseFactory.error(message="Error deleting message", error_code="500")
