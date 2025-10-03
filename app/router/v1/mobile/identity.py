from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.middleware.auth_middleware import jwt_auth
from app.controller.mobile.identity import (
    create_verification_session,
    check_verification_status,
    cancel_verification_session,
    get_verification_summary
)

mobile_identity_router = APIRouter(prefix="/identity", tags=["Mobile Identity Verification"])


@mobile_identity_router.post("/verification-session")
async def create_user_verification_session(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Create a Stripe Identity verification session for the current user"""
    try:
        result = create_verification_session(current_user["user_id"], db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@mobile_identity_router.get("/verification-status")
async def get_user_verification_status(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Check the verification status of the current user's Stripe Identity session"""
    try:
        result = check_verification_status(current_user["user_id"], db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@mobile_identity_router.post("/verification-session/cancel")
async def cancel_user_verification_session(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Cancel the current user's verification session"""
    try:
        result = cancel_verification_session(current_user["user_id"], db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@mobile_identity_router.get("/verification-summary")
async def get_user_verification_summary(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get a summary of the current user's verification status"""
    try:
        result = get_verification_summary(current_user["user_id"], db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
