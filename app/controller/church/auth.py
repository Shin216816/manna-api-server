from fastapi import HTTPException
import logging
import traceback
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from app.model.m_church import Church
from app.model.m_church_admin import ChurchAdmin
from app.model.m_user import User
from app.model.m_refresh_token import RefreshToken
from app.utils.security import hash_password, verify_password
from app.utils.jwt_handler import create_access_token, create_refresh_token
from app.core.messages import get_auth_message
from app.core.responses import ResponseFactory, SuccessResponse
from app.utils.token_manager import token_manager


def register_church_admin(admin_data: dict, db: Session) -> SuccessResponse:
    """Register a new church admin with proper MVP validation"""
    try:
        # Check if user already exists with this email
        existing_user = db.query(User).filter(User.email == admin_data["email"]).first()

        if existing_user:
            # Check if this user is already a church admin
            existing_admin = (
                db.query(ChurchAdmin)
                .filter(ChurchAdmin.user_id == existing_user.id)
                .first()
            )

            if existing_admin:
                raise HTTPException(
                    status_code=409, detail="Church admin already exists for this email"
                )
            else:
                # User exists but is not a church admin - email already in use
                raise HTTPException(
                    status_code=409,
                    detail="Email address is already registered with a different account type",
                )

        # Validate required fields for MVP
        required_fields = ["first_name", "last_name", "email", "password"]
        for field in required_fields:
            if not admin_data.get(field):
                raise HTTPException(
                    status_code=400, detail=f"{field.replace('_', ' ').title()} is required"
                )

        # Create user first with proper validation
        user = User(
            first_name=admin_data["first_name"],
            last_name=admin_data["last_name"],
            email=admin_data["email"],
            password_hash=hash_password(admin_data["password"]),
            role="church_admin",
            is_active=True,
            is_email_verified=True,  # Church admins are verified by default
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # Create a basic church record for this admin (MVP requirement)
        church = Church(
            name=f"Church for {user.first_name} {user.last_name}",
            legal_name=f"Church for {user.first_name} {user.last_name}",
            email=user.email,
            phone="",
            address="",
            address_line_1="",
            address_line_2="",
            city="",
            state="",
            zip_code="",
            country="US",
            is_active=False,  # Will be activated after KYC approval
            status="pending_kyc",
            kyc_status="not_submitted",
            kyc_state="not_submitted",
            charges_enabled=False,
            payouts_enabled=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        db.add(church)
        db.commit()
        db.refresh(church)

        # Create church admin linked to the church with proper permissions
        admin = ChurchAdmin(
            user_id=user.id,
            church_id=church.id,
            role=admin_data.get("role", "admin"),
            is_active=True,
            is_primary_admin=True,  # First admin is primary
            can_manage_finances=True,
            can_manage_members=True,
            can_manage_settings=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        return ResponseFactory.success(
            message="Church admin registered successfully",
            data={
                "id": admin.id,
                "user_id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": admin.role,
                "church_id": church.id,
                "church_name": church.name,
                "kyc_status": church.kyc_status,
                "next_step": "complete_church_kyc",
                "message": "Please complete KYC verification to activate your church account"
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        # Check if it's a unique constraint violation
        if "duplicate key value violates unique constraint" in str(
            e
        ) and "email" in str(e):
            raise HTTPException(
                status_code=409, detail="Email address is already registered"
            )

        raise HTTPException(status_code=500, detail="Failed to register church admin")


def login_church_admin(
    email: str, password: str, db: Session, request: Optional[Any] = None
) -> SuccessResponse:
    """Login church admin with proper MVP validation"""
    try:
        # Validate required fields
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password are required")

        # First find the user by email
        user = db.query(User).filter(User.email == email).first()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Verify this is a church admin user
        if user.role != "church_admin":
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Then find the church admin record for this user
        admin = db.query(ChurchAdmin).filter(ChurchAdmin.user_id == user.id).first()

        if not admin:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Verify password
        if not user.verify_password(password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Check if account is active
        if not admin.is_active or not user.is_active:
            raise HTTPException(status_code=401, detail="Account is inactive")

        # Get church info
        church = db.query(Church).filter(Church.id == admin.church_id).first()

        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Create tokens using token manager with session creation
        access_token, jti, session_id = token_manager.create_access_token(
            data={
                "user_id": user.id,  # Primary identifier for all user types
                "id": user.id,  # Keep for backward compatibility
                "role": "church_admin",  # Include role
                "church_id": admin.church_id,  # Include church_id for session
            },
            request=request,
        )

        # Create refresh token record
        refresh_token_record = token_manager.create_refresh_token_record(
            user_id=user.id,  # Use user.id instead of admin.id
            db=db,
            device_info=None,
            ip_address=None,
            user_agent=None,
        )
        new_refresh_token = refresh_token_record.token

        # Update session with refresh token
        if session_id:
            from app.services.session_service import session_manager

            session = session_manager.get_session(session_id)
            if session:
                session.refresh_token = str(new_refresh_token)

        return ResponseFactory.success(
            message="Login successful",
            data={
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": 3600,
                "session_id": session_id,
                "admin": {
                    "id": admin.id,
                    "church_id": admin.church_id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": admin.role,
                    "is_primary_admin": admin.is_primary_admin,
                    "permissions": {
                        "can_manage_finances": admin.can_manage_finances,
                        "can_manage_members": admin.can_manage_members,
                        "can_manage_settings": admin.can_manage_settings
                    }
                },
                "church": {
                    "id": church.id,
                    "name": church.name,
                    "legal_name": church.legal_name,
                    "status": church.status,
                    "kyc_status": church.kyc_status,
                    "is_active": church.is_active,
                    "charges_enabled": church.charges_enabled,
                    "payouts_enabled": church.payouts_enabled,
                    "next_step": "complete_kyc" if church.kyc_status == "not_submitted" else "dashboard"
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in church admin login: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to login")


def refresh_church_token(
    refresh_token: str, db: Session, request: Optional[Any] = None
) -> SuccessResponse:
    """Refresh church admin access token"""
    try:
        # Verify refresh token using the database method
        refresh_token_record = token_manager.verify_refresh_token(refresh_token, db)
        if not refresh_token_record:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # Get admin from user_id
        admin = (
            db.query(ChurchAdmin)
            .filter(ChurchAdmin.user_id == refresh_token_record.user_id)
            .first()
        )
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")

        admin_id = admin.id

        # Get user information
        user = db.query(User).filter(User.id == admin.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not admin.is_active or not user.is_active:
            raise HTTPException(status_code=401, detail="Account is inactive")

        # Create new tokens using token manager with session creation
        access_token, jti, session_id = token_manager.create_access_token(
            data={
                "user_id": user.id,
                "id": user.id,
                "role": "church_admin",
                "church_id": admin.church_id,
            },
            request=request,
        )

        # Rotate refresh token
        new_refresh_token_record = token_manager.rotate_refresh_token(
            old_token=refresh_token,
            db=db,
            device_info=None,
            ip_address=None,
            user_agent=None,
        )
        new_refresh_token = (
            new_refresh_token_record.token
            if new_refresh_token_record
            else refresh_token
        )

        # Update session with new refresh token
        if session_id:
            from app.services.session_service import session_manager

            session = session_manager.get_session(session_id)
            if session:
                session.refresh_token = str(new_refresh_token)

        # Get church info
        church = db.query(Church).filter(Church.id == admin.church_id).first()

        return ResponseFactory.success(
            message="Token refreshed successfully",
            data={
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": 3600,
                "session_id": session_id,
                "admin": {
                    "id": admin.id,
                    "church_id": admin.church_id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": admin.role,
                },
                "church": {
                    "id": church.id if church else None,
                    "name": church.name if church else None,
                    "status": church.status if church else None,
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to refresh token")


def logout_church(admin_id: int, refresh_token: str, db: Session) -> SuccessResponse:
    """Logout church admin"""
    try:
        token_record = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.token == refresh_token, RefreshToken.user_id == admin_id
            )
            .first()
        )

        if token_record:
            db.delete(token_record)
            db.commit()

        return ResponseFactory.success(message="Logged out successfully")

    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to logout")
