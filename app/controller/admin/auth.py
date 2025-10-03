from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
import logging

from app.model.m_admin_user import AdminUser
from app.schema.admin_schema import AdminLoginRequest, AdminInvitationRequest
from app.core.responses import ResponseFactory, SuccessResponse
from app.utils.security import (
    verify_password,
    hash_password,
    validate_password_strength,
)
from app.utils.token_manager import token_manager
from app.utils.invitation_validator import (
    validate_admin_invitation,
    mark_admin_invitation_used,
    get_admin_invitation_info,
)
from app.config import config


def login_admin(data: AdminLoginRequest, db: Session):
    """Admin login"""
    try:
        admin = AdminUser.get_by_email(db, data.email)
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")

        if not verify_password(data.password, admin.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not admin.is_active:
            raise HTTPException(status_code=401, detail="Account is inactive")

        # Update last login
        admin.last_login = datetime.now(timezone.utc)
        db.commit()

        # Generate a long-lived access token for admin sessions (persist until explicit logout)
        # Admin portal requires persistent sessions; we issue a long expiry token
        from datetime import timedelta
        access_token, jti, session_id = token_manager.create_access_token(
            {
                "id": admin.id,
                "email": admin.email,
                "role": admin.role,
                "permissions": admin.permissions,
            },
            expires_delta=timedelta(days=365)
        )

        return ResponseFactory.success(
            message="Admin login successful", data={"access_token": access_token}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Login failed")


def logout_admin(current_user: dict, db: Session):
    """Admin logout"""
    try:
        # For admin users, just return success since we don't use refresh tokens
        return ResponseFactory.success(
            message="Admin logout successful", data={"logged_out": True}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail="Logout failed")


def get_admin_profile(admin_id: int, db: Session):
    """Get admin profile"""
    try:
        admin = AdminUser.get_by_id(db, admin_id)
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")

        return ResponseFactory.success(
            message="Admin profile retrieved successfully",
            data={
                "id": admin.id,
                "email": admin.email,
                "role": admin.role,
                "permissions": admin.permissions,
                "is_active": admin.is_active,
                "created_at": (
                    admin.created_at.isoformat() if admin.created_at else None
                ),
                "last_login": (
                    admin.last_login.isoformat() if admin.last_login else None
                ),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve admin profile")


def refresh_admin_token(refresh_token: str, db: Session):
    """Refresh admin token - simplified for admin users"""
    try:
        # For admin users, we don't use refresh tokens
        # They should simply re-login if their token expires
        raise HTTPException(
            status_code=400,
            detail="Admin users should re-login instead of using refresh tokens",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Token refresh failed")


def get_admin_permissions(admin_id: int, db: Session):
    """Get admin permissions"""
    try:
        admin = AdminUser.get_by_id(db, admin_id)
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")

        return ResponseFactory.success(
            message="Admin permissions retrieved successfully",
            data={
                "role": admin.role,
                "permissions": admin.permissions,
                "is_active": admin.is_active,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to retrieve admin permissions"
        )


def register_admin_with_invitation(data: AdminInvitationRequest, db: Session):
    """Admin registration with invitation code validation"""
    try:
        # Validate invitation code
        validation_result = validate_admin_invitation(data.invitation_code)

        if not validation_result["valid"]:
            raise HTTPException(status_code=400, detail=validation_result["error"])

        invitation = validation_result["invitation"]

        # Verify email matches invitation
        if invitation["email"] != data.email:
            raise HTTPException(
                status_code=400, detail="Email address does not match invitation"
            )

        # Check if admin already exists
        existing_admin = AdminUser.get_by_email(db, data.email)
        if existing_admin:
            raise HTTPException(
                status_code=409, detail="Admin with this email already exists"
            )

        # Validate password strength
        password_validation = validate_password_strength(data.password)
        if not password_validation["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Password validation failed: {', '.join(password_validation['errors'])}",
            )

        # Confirm password match
        if data.password != data.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")

        # Create admin user
        admin = AdminUser(
            email=data.email,
            password=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            role="admin",
            permissions="admin",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        # Mark invitation as used
        mark_admin_invitation_used(data.invitation_code, data.email)

        # Log successful registration

        return ResponseFactory.success(
            message="Admin registered successfully",
            data={
                "id": admin.id,
                "email": admin.email,
                "first_name": admin.first_name,
                "last_name": admin.last_name,
                "role": admin.role,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Registration failed")


def validate_invitation_code(invitation_code: str):
    """Validate invitation code and return invitation info"""
    try:
        validation_result = validate_admin_invitation(invitation_code)

        if not validation_result["valid"]:
            raise HTTPException(status_code=400, detail=validation_result["error"])

        invitation = validation_result["invitation"]

        return ResponseFactory.success(
            message="Invitation code is valid",
            data={
                "email": invitation["email"],
                "name": invitation["name"],
                "expires_at": invitation["expires_at"],
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Invitation validation failed")
