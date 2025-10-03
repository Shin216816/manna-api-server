from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.controller.public.contact import (
    submit_contact_message, 
    get_contact_categories, 
    get_contact_priorities,
    ContactMessageRequest
)
from app.core.responses import SuccessResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.post("/submit", response_model=SuccessResponse)
@limiter.limit("5/minute")  # Rate limit to prevent spam
def submit_contact_form(
    request: Request,
    contact_data: ContactMessageRequest,
    db: Session = Depends(get_db)
):
    """
    Submit a contact message from a visitor
    
    Public endpoint that allows visitors to submit contact messages without authentication.
    Rate limited to prevent spam and abuse.
    
    **Request Body:**
    - **name**: Full name of the person contacting (required, 1-255 characters)
    - **email**: Valid email address for response (required)
    - **subject**: Subject line for the message (required, 1-500 characters)
    - **message**: Message content (required, minimum 10 characters)
    - **category**: Message category (optional, defaults to "general")
    - **priority**: Message priority (optional, defaults to "medium")
    
    **Available Categories:**
    - general: General inquiries
    - support: Technical support requests
    - partnership: Partnership opportunities
    - technical: Technical issues or bugs
    - feedback: User feedback and suggestions
    
    **Available Priorities:**
    - low: Non-urgent inquiries
    - medium: Standard priority (default)
    - high: Important matters requiring attention
    - urgent: Critical issues requiring immediate attention
    
    **Response:**
    Returns success confirmation with message ID and submission timestamp.
    
    **Rate Limiting:**
    Limited to 5 submissions per minute per IP address to prevent spam.
    """
    return submit_contact_message(db, contact_data)

@router.get("/categories", response_model=SuccessResponse)
def get_available_categories():
    """
    Get available contact message categories
    
    Returns a list of all available categories for contact form submissions.
    Useful for populating dropdown menus in the frontend.
    
    **Response:**
    Returns array of category objects with value and label fields.
    """
    return get_contact_categories()

@router.get("/priorities", response_model=SuccessResponse)
def get_available_priorities():
    """
    Get available contact message priorities
    
    Returns a list of all available priorities for contact form submissions.
    Useful for populating dropdown menus in the frontend.
    
    **Response:**
    Returns array of priority objects with value and label fields.
    """
    return get_contact_priorities()
