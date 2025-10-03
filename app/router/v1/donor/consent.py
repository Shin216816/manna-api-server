from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.controller.donor.consent import (
    accept_consent, 
    get_consent_status, 
    get_consent_history
)

router = APIRouter()

@router.post("/accept")
def accept_consent_route(
    data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept consent and authorizations"""
    return accept_consent(current_user, data, db)

@router.get("/status")
def get_consent_status_route(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get consent status"""
    return get_consent_status(current_user, db)

@router.get("/history")
def get_consent_history_route(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get consent history"""
    return get_consent_history(current_user, db)
