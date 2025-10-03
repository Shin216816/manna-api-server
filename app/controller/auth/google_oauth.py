"""
Google OAuth Authentication Controller

Handles Google OAuth login functionality for the mobile app.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging
import time

from google.oauth2 import id_token  # type: ignore
from google.auth.transport import requests as google_requests  # type: ignore
from google.auth.exceptions import GoogleAuthError  # type: ignore

from app.model.m_user import User
from app.utils.jwt_handler import create_access_token, create_refresh_token
from app.model.m_refresh_token import RefreshToken
from app.core.responses import ResponseFactory
from app.config import config
from app.schema.auth_schema import GoogleOAuthRequest


def google_oauth_login(data: GoogleOAuthRequest, db: Session):
    """Google OAuth login implementation"""
    try:
        # Validate ID token is not empty
        if not data.id_token or data.id_token.strip() == "":
            raise HTTPException(status_code=400, detail="Google ID token is required")

        # Verify the Google ID token
        max_retries = 3
        base_delay = 1  # Start with 1 second delay

        for attempt in range(max_retries):
            try:
                idinfo = id_token.verify_oauth2_token(
                    data.id_token, google_requests.Request(), config.GOOGLE_CLIENT_ID
                )

                # If we get here, token verification succeeded
                break

            except ValueError as e:
                error_msg = str(e)

                # Check if this is a clock skew issue
                if "Token used too early" in error_msg and attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)  # Exponential backoff: 1s, 2s, 4s

                    time.sleep(delay)
                    continue
                elif "Token expired" in error_msg:
                    raise HTTPException(
                        status_code=401,
                        detail="Google token has expired. Please sign in again.",
                    )
                else:
                    # Re-raise the error if it's not a clock skew issue or we've exhausted retries
                    raise HTTPException(
                        status_code=401, detail="Invalid Google ID token"
                    )
            except Exception as e:

                raise HTTPException(status_code=401, detail="Invalid Google ID token")
        else:
            # If we've exhausted all retries
            raise HTTPException(
                status_code=401,
                detail="Token validation failed due to persistent clock synchronization issues. Please try again.",
            )

        # Extract user information
        google_user_id = idinfo.get("sub")
        email = idinfo.get("email")
        first_name = idinfo.get("given_name", "")
        last_name = idinfo.get("family_name", "")
        email_verified = idinfo.get("email_verified", False)

        if not google_user_id or not email:
            raise HTTPException(status_code=400, detail="Invalid Google user data")

        # Check if user exists
        user = User.get_by_email(db, email)
        if not user:
            user = User.get_by_google_id(db, google_user_id)

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
                google_id=google_user_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update existing user
            user.google_id = google_user_id
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
            message="Google OAuth login successful",
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

    except GoogleAuthError:
        raise HTTPException(status_code=401, detail="Invalid Google ID token")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Google OAuth login failed")
