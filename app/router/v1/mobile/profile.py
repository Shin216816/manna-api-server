from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session
from app.controller.mobile.profile import (
    get_mobile_profile, update_mobile_profile, upload_mobile_profile_image,
    remove_mobile_profile_image, send_email_verification, confirm_email_verification,
    send_phone_verification, confirm_phone_verification
)
from app.utils.database import get_db
from app.middleware.auth_middleware import jwt_auth
from app.core.responses import SuccessResponse

profile_router = APIRouter(tags=["Mobile Profile"])

@profile_router.get("/", response_model=SuccessResponse)
async def get_profile_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get user profile"""
    return get_mobile_profile(current_user["id"], db)

@profile_router.put("/", response_model=SuccessResponse)
async def update_profile_route(
    profile_data: dict,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    return update_mobile_profile(current_user["id"], profile_data, db)

@profile_router.post("/image", response_model=SuccessResponse)
async def upload_profile_image_route(
    image_file: UploadFile,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Upload profile image"""
    return await upload_mobile_profile_image(current_user["id"], image_file, db)

@profile_router.delete("/image", response_model=SuccessResponse)
async def remove_profile_image_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Remove profile image"""
    return await remove_mobile_profile_image(current_user["id"], db)

@profile_router.post("/verify-email/send", response_model=SuccessResponse)
async def send_email_verification_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Send email verification"""
    return send_email_verification(current_user["id"], db)

@profile_router.post("/verify-email/confirm", response_model=SuccessResponse)
async def confirm_email_verification_route(
    verification_data: dict,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Confirm email verification"""
    return confirm_email_verification(
        current_user["id"], 
        verification_data.get("access_code"), 
        verification_data.get("email"), 
        db
    )

@profile_router.post("/verify-phone/send", response_model=SuccessResponse)
async def send_phone_verification_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Send phone verification"""
    return send_phone_verification(current_user["id"], db)

@profile_router.post("/verify-phone/confirm", response_model=SuccessResponse)
async def confirm_phone_verification_route(
    verification_data: dict,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Confirm phone verification"""
    return confirm_phone_verification(
        current_user["id"], 
        verification_data.get("access_code"), 
        verification_data.get("phone"), 
        db
    )