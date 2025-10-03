from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.controller.admin.auth import (
    login_admin, logout_admin, get_admin_profile, refresh_admin_token, 
    register_admin_with_invitation, validate_invitation_code
)
from app.schema.admin_schema import AdminLoginRequest, AdminInvitationRequest, InvitationValidationRequest
from app.utils.database import get_db
from app.middleware.admin_auth import admin_auth
from app.core.responses import SuccessResponse

auth_router = APIRouter(tags=["Admin Authentication"])

@auth_router.post("/register", response_model=SuccessResponse)
async def register_admin_route(
    data: AdminInvitationRequest,
    db: Session = Depends(get_db)
):
    """Register a new admin user with invitation code"""
    return register_admin_with_invitation(data, db)

@auth_router.post("/validate-invitation", response_model=SuccessResponse)
async def validate_invitation_route(
    data: InvitationValidationRequest
):
    """Validate an invitation code"""
    return validate_invitation_code(data.invitation_code)

@auth_router.post("/login", response_model=SuccessResponse)
async def login_admin_route(
    data: AdminLoginRequest,
    db: Session = Depends(get_db)
):
    """Login admin user"""
    return login_admin(data, db)

@auth_router.post("/logout", response_model=SuccessResponse)
async def logout_admin_route(
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Logout admin user"""
    return logout_admin(current_user, db)

@auth_router.get("/profile", response_model=SuccessResponse)
async def get_admin_profile_route(
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get admin profile"""
    return get_admin_profile(current_user["id"], db)

# Admin users don't use refresh tokens - they should re-login instead

@auth_router.get("/permissions", response_model=SuccessResponse)
async def get_admin_permissions_route(
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get admin permissions"""
    from app.controller.admin.auth import get_admin_permissions
    return get_admin_permissions(current_user["id"], db)
