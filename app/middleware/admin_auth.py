"""
Admin Authentication Middleware

Handles authentication for admin platform endpoints.
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.model.m_admin_user import AdminUser
from app.utils.database import get_db
from app.middleware.auth_middleware import jwt_auth
import logging


def admin_auth(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """
    Verify that the current user is a platform admin.
    
    Args:
        current_user: The authenticated user from JWT
        db: Database session
        
    Returns:
        dict: User data
        
    Raises:
        HTTPException: If user is not an admin
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        # Get admin from database
        admin = db.query(AdminUser).filter_by(id=user_id).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin not found"
            )
        
        # Check if admin is active
        if not admin.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin account is inactive"
            )
        
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        ) 
