from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.utils.token_manager import token_manager
from app.utils.database import get_db
from app.model.m_user import User
from app.model.m_church_admin import ChurchAdmin
from app.model.m_church import Church
import logging

security = HTTPBearer(auto_error=True)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user for donor endpoints"""
    token = credentials.credentials

    # Validate JWT using token manager (includes blacklist checking)
    payload = token_manager.verify_access_token(token, db)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

    # Check if token is expired
    if payload.get("expired") and payload.get("error") == "token_expired":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="AUTH.TOKEN.EXPIRED"
        )

    # Check if payload has required user_id field
    if "user_id" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

    # Get user from database
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Ensure this is a donor/congregant user (not a church admin)
    if user.role not in ["donor", "congregant"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Donor access required"
        )

    # Get church_id from user's direct church association
    church_id = user.church_id

    return {
        "user_id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "church_id": church_id,
        "role": user.role  # Use actual user role from database
    }

def jwt_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """JWT authentication with blacklist checking - based on old backend implementation"""
    token = credentials.credentials

    # Validate JWT using token manager (includes blacklist checking)
    payload = token_manager.verify_access_token(token, db)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="AUTH.TOKEN.INVALID"
        )

    # Check if token is expired
    if payload.get("expired") and payload.get("error") == "token_expired":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="AUTH.TOKEN.EXPIRED"
        )

    return payload

def jwt_church_admin_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Church admin authentication with unified user_id approach"""
    token = credentials.credentials

    try:
        # Validate JWT using token manager (includes blacklist checking)
        payload = token_manager.verify_access_token(token, db)
        if not payload:
            raise HTTPException(
                status_code=401, 
                detail="AUTH.ADMIN.TOKEN.INVALID"
            )

        # Check if token is expired
        if payload.get("expired") and payload.get("error") == "token_expired":
            raise HTTPException(
                status_code=401, 
                detail="AUTH.TOKEN.EXPIRED",
                headers={"X-Token-Expired": "true"}
            )

        # Check if payload has required user_id field
        if "user_id" not in payload:
            raise HTTPException(
                status_code=401, 
                detail="AUTH.ADMIN.TOKEN.INVALID"
            )

        # Get user directly using user_id
        user = db.query(User).filter_by(id=payload["user_id"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="AUTH.USER.NOT_FOUND")

        # Check if user has church_admin role
        if user.role != "church_admin":
            logging.error(f"Church admin auth failed - User {user.id} has role '{user.role}', expected 'church_admin'")
            raise HTTPException(
                status_code=403, 
                detail="AUTH.ROLE.FORBIDDEN"
            )

        # Get the church admin record for this user
        admin = db.query(ChurchAdmin).filter_by(user_id=user.id).first()
        if not admin:
            logging.error(f"Church admin record not found for user {user.id}")
            raise HTTPException(status_code=404, detail="AUTH.ADMIN.NOT_FOUND")

        # Get church information
        church = db.query(Church).filter_by(id=admin.church_id).first()
        if not church:
            logging.error(f"Church {admin.church_id} not found for admin {admin.id}")
            raise HTTPException(status_code=404, detail="Church not found")
        
        # Allow access during onboarding even if church is not fully active
        # Check if church is in onboarding state
        if not church.is_active and church.status not in ["pending_kyc", "active"]:
            logging.error(f"Church {church.id} is disabled with status: {church.status}")
            raise HTTPException(status_code=403, detail="Church is disabled.")

        return {
            "user_id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "church_id": admin.church_id,
            "role": "church_admin",
            "admin_id": admin.id  # Keep for backward compatibility
        }
    except HTTPException:
        raise
    except Exception as e:
        error(f"Church admin auth error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="AUTH.ADMIN.TOKEN.INVALID"
        )

def jwt_platform_admin_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Platform admin authentication - based on old backend implementation"""
    token = credentials.credentials

    # Validate JWT using token manager (includes blacklist checking)
    payload = token_manager.verify_access_token(token, db)
    if not payload:
        raise HTTPException(status_code=403, detail="AUTH.ROLE.FORBIDDEN")

    # Check if token is expired
    if payload.get("expired") and payload.get("error") == "token_expired":
        raise HTTPException(
            status_code=401,
            detail="AUTH.TOKEN.EXPIRED"
        )

    # Check if user has platform admin role
    if payload.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="AUTH.ROLE.FORBIDDEN")

    return {
        "admin_id": payload.get("admin_id"),
        "role": "platform_admin"
    }
