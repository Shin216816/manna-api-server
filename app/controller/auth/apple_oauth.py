"""
Apple OAuth Authentication Controller

Handles Apple OAuth login functionality for the mobile app.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging
import urllib.request
import json
from jose import jwt, JWTError

from app.model.m_user import User
from app.utils.jwt_handler import create_access_token, create_refresh_token
from app.model.m_refresh_token import RefreshToken
from app.core.responses import ResponseFactory
from app.config import config
from app.schema.auth_schema import AppleOAuthRequest


def apple_oauth_login(data: AppleOAuthRequest, db: Session):
    """Apple OAuth login implementation"""
    try:
        # Verify the Apple ID token (simplified for python-jose)
        # For production, implement proper Apple token verification
        try:
            # Decode without verification for now
            payload = jwt.decode(
                data.auth_code, key=None, options={"verify_signature": False}
            )
        except JWTError:
            raise HTTPException(status_code=400, detail="Invalid Apple token format")

        # Extract user information
        apple_user_id = payload.get("sub")
        email = payload.get("email")
        first_name = payload.get("given_name", "")
        last_name = payload.get("family_name", "")
        email_verified = True  # Apple tokens are pre-verified

        if not apple_user_id or not email:
            raise HTTPException(status_code=400, detail="Invalid Apple user data")

        # Check if user exists
        user = User.get_by_email(db, email)
        if not user:
            user = User.get_by_apple_id(db, apple_user_id)

        if not user:
            # Create new user
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=None,
                password=None,
                church_id=None,
                is_email_verified=email_verified,
                is_phone_verified=False,
                is_active=True,
                apple_id=apple_user_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update existing user
            user.apple_id = apple_user_id
            user.is_email_verified = email_verified or user.is_email_verified
            user.updated_at = datetime.now(timezone.utc)
            db.commit()

        # Generate tokens
        access_token = create_access_token(
            {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        )

        refresh_token_obj = RefreshToken.create_token(user.id, db, create_refresh_token)  # type: ignore

        return ResponseFactory.success(
            message="Apple OAuth login successful",
            data={
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token_obj.token,
                    "token_type": "bearer",
                    "expires_in": 3600,
                },
                "user": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "middle_name": user.middle_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "phone": user.phone,
                    "is_email_verified": user.is_email_verified,
                    "is_phone_verified": user.is_phone_verified,
                    "is_active": user.is_active,
                    "church_id": None,  # User not associated with church during OAuth
                    "stripe_customer_id": user.stripe_customer_id,
                    "created_at": (
                        user.created_at.isoformat() if user.created_at else None
                    ),
                    "updated_at": (
                        user.updated_at.isoformat() if user.updated_at else None
                    ),
                    "last_login": (
                        user.last_login.isoformat() if user.last_login else None
                    ),
                },
            },
        )

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid Apple identity token")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Apple OAuth login failed")
