"""
Church Admin Authentication Middleware

Handles authentication for church admin endpoints.
"""

from fastapi import Depends
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.middleware.auth_middleware import jwt_church_admin_auth


async def church_admin_auth(
    current_user: dict = Depends(jwt_church_admin_auth),
    db: Session = Depends(get_db)
):
    """
    Verify that the current user is a church admin.
    
    Args:
        current_user: The authenticated user from jwt_church_admin_auth
        db: Database session
        
    Returns:
        dict: User data with church_id and admin_id
        
    Raises:
        HTTPException: If user is not a church admin
    """
    # jwt_church_admin_auth already handles all the authentication logic
    # Just return the authenticated user data
    return current_user
