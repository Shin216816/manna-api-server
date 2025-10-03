"""
Mobile Identity Controller
Handles identity verification for church admins via mobile app
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.middleware.auth_middleware import get_current_user
from app.utils.database import get_db
from app.services.stripe_identity_service import StripeIdentityService
from app.model.m_church_admin import ChurchAdmin

router = APIRouter()

@router.get("/status")
async def get_identity_status(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get identity verification status for the current user (if they're a church admin)"""
    try:
        user_id = current_user["id"]
        
        # Check if user is a church admin
        church_admin = db.query(ChurchAdmin).filter_by(user_id=user_id).first()
        if not church_admin:
            return {
                "status": "not_applicable",
                "message": "Identity verification is only required for church admins"
            }
        
        # Check if there's an existing verification session
        if church_admin.stripe_identity_session_id and church_admin.identity_verification_status == "pending":
            # Check current status from Stripe
            status_info = StripeIdentityService.check_verification_status(church_admin.id, db)
            return {
                "status": status_info["status"],
                "session_id": status_info["session_id"],
                "verification_date": status_info.get("verification_date")
            }
        
        # Return current status
        return {
            "status": church_admin.identity_verification_status,
            "session_id": church_admin.stripe_identity_session_id,
            "verification_date": church_admin.identity_verification_date.isoformat() if church_admin.identity_verification_date else None
        }
        
    except Exception as e:
        error(f"Error getting identity status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get identity status")

@router.post("/start")
async def start_identity_verification(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Start identity verification process for church admin"""
    try:
        user_id = current_user["id"]
        
        # Check if user is a church admin
        church_admin = db.query(ChurchAdmin).filter_by(user_id=user_id).first()
        if not church_admin:
            raise HTTPException(
                status_code=403, 
                detail="Identity verification is only available for church admins"
            )
        
        # Check if already verified
        if church_admin.identity_verification_status == "verified":
            return {
                "status": "already_verified",
                "message": "Identity verification already completed"
            }
        
        # Check if there's an existing pending session
        if church_admin.stripe_identity_session_id and church_admin.identity_verification_status == "pending":
            return {
                "status": "pending",
                "session_id": church_admin.stripe_identity_session_id,
                "message": "Verification session already in progress"
            }
        
        # Create new verification session
        session_info = StripeIdentityService.create_verification_session(church_admin.id, db)
        
        return {
            "status": "started",
            "session_id": session_info["session_id"],
            "client_secret": session_info["client_secret"],
            "url": session_info["url"]
        }
        
    except Exception as e:
        error(f"Error starting identity verification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start identity verification")

@router.post("/cancel")
async def cancel_identity_verification(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Cancel identity verification process for church admin"""
    try:
        user_id = current_user["id"]
        
        # Check if user is a church admin
        church_admin = db.query(ChurchAdmin).filter_by(user_id=user_id).first()
        if not church_admin:
            raise HTTPException(
                status_code=403, 
                detail="Identity verification is only available for church admins"
            )
        
        # Cancel verification session
        result = StripeIdentityService.cancel_verification_session(church_admin.id, db)
        
        return {
            "status": "cancelled",
            "message": "Identity verification cancelled successfully"
        }
        
    except Exception as e:
        error(f"Error cancelling identity verification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel identity verification")

@router.get("/info")
async def get_identity_info(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed identity verification information for church admin"""
    try:
        user_id = current_user["id"]
        
        # Get verification info by user ID
        verification_info = StripeIdentityService.get_verification_info_by_user_id(user_id, db)
        
        if not verification_info:
            return {
                "status": "not_applicable",
                "message": "Identity verification is only required for church admins"
            }
        
        return verification_info
        
    except Exception as e:
        error(f"Error getting identity info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get identity information")
