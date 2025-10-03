from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.controller.mobile.profile import (
    get_mobile_profile, update_mobile_profile, upload_profile_image, remove_profile_image, 
    get_profile_image, verify_mobile_email, confirm_mobile_email_verification,
    verify_mobile_phone, confirm_mobile_phone_verification, set_mobile_password, sync_mobile_profile
)
from app.schema.auth_schema import (
    UserProfileUpdateRequest, SetPasswordRequest, AuthVerifyOtpRequest
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
    """Get user profile for mobile"""
    return get_mobile_profile(current_user, db)

@profile_router.put("/", response_model=SuccessResponse)
async def update_profile_route(
    data: UserProfileUpdateRequest,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Update user profile for mobile"""
    return update_mobile_profile(data, current_user, db)

@profile_router.post("/image", response_model=SuccessResponse)
async def upload_profile_image_route(
    file: UploadFile = File(...),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Upload profile image for mobile"""
    return upload_profile_image(current_user["id"], file, db)

@profile_router.delete("/image", response_model=SuccessResponse)
async def remove_profile_image_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Remove profile image for mobile"""
    return remove_profile_image(current_user["id"], db)

@profile_router.get("/image", response_model=SuccessResponse)
async def get_profile_image_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get profile image for mobile"""
    return get_profile_image(current_user, db)

@profile_router.post("/verify-email/send", response_model=SuccessResponse)
async def send_email_verification_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Send email verification for mobile"""
    return verify_mobile_email(current_user, db)

@profile_router.post("/verify-email/confirm", response_model=SuccessResponse)
async def confirm_email_verification_route(
    data: AuthVerifyOtpRequest,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Confirm email verification for mobile"""
    return confirm_mobile_email_verification(data, current_user, db)

@profile_router.post("/verify-phone/send", response_model=SuccessResponse)
async def send_phone_verification_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Send phone verification for mobile"""
    return verify_mobile_phone(current_user, db)

@profile_router.post("/verify-phone/confirm", response_model=SuccessResponse)
async def confirm_phone_verification_route(
    data: AuthVerifyOtpRequest,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Confirm phone verification for mobile"""
    return confirm_mobile_phone_verification(data, current_user, db)

@profile_router.post("/set-password", response_model=SuccessResponse)
async def set_password_route(
    data: SetPasswordRequest,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Set password for mobile"""
    return set_mobile_password(data, current_user, db)

@profile_router.get("/sync", response_model=SuccessResponse)
async def sync_profile_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Sync profile data for mobile"""
    return sync_mobile_profile(current_user["id"], db)

# Additional endpoints that tests might expect
@profile_router.put("/password", response_model=SuccessResponse)
async def change_password_route(
    data: SetPasswordRequest,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Change password for mobile (alias for set-password)"""
    return set_mobile_password(data, current_user, db)

@profile_router.delete("/", response_model=SuccessResponse)
async def delete_account_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Delete user account"""
    from app.controller.mobile.profile import delete_mobile_account
    return delete_mobile_account(current_user["id"], db)
