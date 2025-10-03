from sqlalchemy.orm import Session
from app.core.responses import ResponseFactory
from app.core.exceptions import MannaException, ValidationError
from app.model import ContactMessage, ContactCategory, ContactPriority
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import re


class ContactMessageRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    subject: str = Field(..., min_length=1, max_length=500)
    message: str = Field(..., min_length=10)
    category: Optional[str] = Field(default="general")
    priority: Optional[str] = Field(default="medium")


def submit_contact_message(db: Session, contact_data: ContactMessageRequest):
    """Submit a contact message from a visitor (public endpoint, no auth required)"""
    try:
        # Validate and normalize category
        category = ContactCategory.GENERAL
        if contact_data.category:
            try:
                category = ContactCategory(contact_data.category.lower())
            except ValueError:
                category = ContactCategory.GENERAL
        
        # Validate and normalize priority
        priority = ContactPriority.MEDIUM
        if contact_data.priority:
            try:
                priority = ContactPriority(contact_data.priority.lower())
            except ValueError:
                priority = ContactPriority.MEDIUM
        
        # Sanitize input data
        name = contact_data.name.strip()
        subject = contact_data.subject.strip()
        message = contact_data.message.strip()
        
        # Additional validation
        if len(name) == 0:
            raise ValidationError("Name cannot be empty")
        
        if len(subject) == 0:
            raise ValidationError("Subject cannot be empty")
        
        if len(message) < 10:
            raise ValidationError("Message must be at least 10 characters long")
        
        # Check for potential spam patterns (basic validation)
        spam_patterns = [
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            r'www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
        ]
        
        for pattern in spam_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                # Log potential spam but don't reject - just flag for review
                priority = ContactPriority.LOW
        
        # Create contact message record
        contact_message = ContactMessage(
            name=name,
            email=contact_data.email,
            subject=subject,
            message=message,
            category=category,
            priority=priority
        )
        
        db.add(contact_message)
        db.commit()
        db.refresh(contact_message)
        
        return ResponseFactory.success(
            message="Contact message submitted successfully",
            data={
                "id": contact_message.id,
                "submitted_at": contact_message.created_at.isoformat() if contact_message.created_at else None
            }
        )
        
    except ValidationError:
        raise
    except MannaException:
        raise
    except Exception as e:
        db.rollback()
        raise ValidationError(f"Failed to submit contact message: {str(e)}")


def get_contact_categories():
    """Get available contact categories for the frontend form"""
    try:
        categories = [
            {"value": category.value, "label": category.value.replace("_", " ").title()}
            for category in ContactCategory
        ]
        
        return ResponseFactory.success(
            message="Contact categories retrieved successfully",
            data={"categories": categories}
        )
        
    except Exception as e:
        raise ValidationError(f"Failed to get contact categories: {str(e)}")


def get_contact_priorities():
    """Get available contact priorities for the frontend form"""
    try:
        priorities = [
            {"value": priority.value, "label": priority.value.title()}
            for priority in ContactPriority
        ]
        
        return ResponseFactory.success(
            message="Contact priorities retrieved successfully",
            data={"priorities": priorities}
        )
        
    except Exception as e:
        raise ValidationError(f"Failed to get contact priorities: {str(e)}")
