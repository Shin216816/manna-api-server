"""
Email Verification Router

Handles email verification and password reset functionality.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.middleware.auth_middleware import jwt_auth
from app.services.email_service import EmailService
from app.core.responses import ResponseFactory
from app.core.exceptions import ValidationError
from app.utils.error_handler import handle_controller_errors

router = APIRouter()

@router.post("/send-verification")
async def send_verification_email(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Send email verification to the current user"""
    try:
        email_service = EmailService(db)
        result = email_service.send_verification_email(current_user["user_id"])
        
        if result['success']:
            return ResponseFactory.success(
                message=result['message']
            )
        else:
            return ResponseFactory.error(result['message'], "400")
    except Exception as e:
        return ResponseFactory.error(f"Error sending verification email: {str(e)}", "500")

@router.post("/verify-email")
async def verify_email(
    token: str = Query(..., description="Email verification token"),
    db: Session = Depends(get_db)
):
    """Verify user's email with token"""
    try:
        email_service = EmailService(db)
        result = email_service.verify_email(token)
        
        if result['success']:
            return ResponseFactory.success(
                message=result['message']
            )
        else:
            return ResponseFactory.error(result['message'], "400")
    except Exception as e:
        return ResponseFactory.error(f"Error verifying email: {str(e)}", "500")

@router.post("/send-password-reset")
async def send_password_reset_email(
    email: str = Query(..., description="User's email address"),
    db: Session = Depends(get_db)
):
    """Send password reset email"""
    try:
        email_service = EmailService(db)
        result = email_service.send_password_reset_email(email)
        
        return ResponseFactory.success(
            message=result['message']
        )
    except Exception as e:
        return ResponseFactory.error(f"Error sending password reset email: {str(e)}", "500")

@router.post("/reset-password")
async def reset_password(
    token: str = Query(..., description="Password reset token"),
    new_password: str = Query(..., description="New password"),
    db: Session = Depends(get_db)
):
    """Reset user's password with token"""
    try:
        from app.model.m_email_verification import EmailVerification
        from app.model.m_user import User
        from app.utils.security import hash_password
        from datetime import datetime, timezone
        
        # Find verification record
        verification = db.query(EmailVerification).filter(
            EmailVerification.token == token,
            EmailVerification.type == 'password_reset',
            EmailVerification.status == 'pending'
        ).first()
        
        if not verification:
            return ResponseFactory.error("Invalid or expired reset token", "400")
        
        # Check if token is expired
        if verification.is_expired():
            verification.mark_expired(db)
            return ResponseFactory.error("Reset token has expired", "400")
        
        # Get user
        user = db.query(User).filter(User.id == verification.user_id).first()
        if not user:
            return ResponseFactory.error("User not found", "404")
        
        # Update password
        user.set_password(new_password)
        verification.status = 'used'
        verification.verified_at = datetime.now(timezone.utc)
        
        db.commit()
        
        return ResponseFactory.success(
            message="Password reset successfully"
        )
    except Exception as e:
        db.rollback()
        return ResponseFactory.error(f"Error resetting password: {str(e)}", "500")

@router.get("/verification-status")
async def get_verification_status(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get current user's email verification status"""
    try:
        from app.model.m_user import User
        
        user = db.query(User).filter(User.id == current_user["user_id"]).first()
        if not user:
            return ResponseFactory.error("User not found", "404")
        
        return ResponseFactory.success(
            message="Verification status retrieved successfully",
            data={
                'is_email_verified': user.is_email_verified,
                'email': user.email
            }
        )
    except Exception as e:
        return ResponseFactory.error(f"Error retrieving verification status: {str(e)}", "500")
