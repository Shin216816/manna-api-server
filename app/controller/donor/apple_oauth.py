"""
Apple OAuth Controller for Donor Authentication

This controller handles comprehensive Apple OAuth authentication for donors with proper token verification
"""

import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app.model.m_user import User
from app.model.m_church import Church
from app.services.oauth_service import OAuthService
from app.core.exceptions import AuthenticationError, ValidationError, UserNotFoundError
from app.core.responses import ResponseFactory
from app.utils.error_handler import handle_controller_errors
from app.utils.security import hash_password, create_access_token, create_refresh_token
from app.utils.audit import log_audit_event


@handle_controller_errors
async def apple_oauth_login(
    identity_token: str,
    invite_token: Optional[str] = None,
    request: Request = None,
    db: Session = None
) -> ResponseFactory:
    """
    Authenticate or create donor using Apple OAuth
    
    Args:
        identity_token: Apple identity token from client
        invite_token: Optional invite token for church association
        request: FastAPI request object
        db: Database session
        
    Returns:
        ResponseFactory with authentication result
    """
    try:
        # Initialize OAuth service
        oauth_service = OAuthService()
        
        # Verify Apple identity token
        user_info = await oauth_service.authenticate_apple_user(identity_token)
        
        if not user_info.get('apple_id'):
            raise ValidationError("Apple ID is required for authentication")
        
        # Check if user already exists by Apple ID or email
        user = None
        if user_info.get('email'):
            user = db.query(User).filter(
                User.email == user_info['email'],
                User.role == "donor"
            ).first()
        
        if user:
            # Update last login
            user.last_login = datetime.now(timezone.utc)
            user.updated_at = datetime.now(timezone.utc)
            
            # Store Apple ID if not already stored
            if not hasattr(user, 'apple_id'):
                # Add apple_id field to user model if not exists
                pass  # This would require a database migration
            
            db.commit()
            
            # Generate JWT tokens
            access_token = create_access_token({"user_id": user.id, "role": user.role, "church_id": user.church_id})
            refresh_token = create_refresh_token({"user_id": user.id, "role": user.role, "church_id": user.church_id})
            tokens = {"access_token": access_token, "refresh_token": refresh_token}
            
            # Log audit event
            log_audit_event(
                db=db,
                actor_type="user",
                actor_id=user.id,
                action="APPLE_OAUTH_LOGIN",
                metadata={
                    "resource_type": "user",
                    "resource_id": user.id,
                    "oauth_provider": "apple",
                    "apple_id": user_info['apple_id'],
                    "email": user_info.get('email')
                }
            )
            
            return ResponseFactory.success(
                message="Successfully logged in with Apple",
                data={
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "role": user.role,
                        "church_id": user.church_id,
                        "is_email_verified": user.is_email_verified,
                        "profile_picture_url": user.profile_picture_url
                    },
                    "tokens": tokens,
                    "is_new_user": False
                }
            )
        
        else:
            # Create new user
            # Handle church association
            church_id = None
            if invite_token:
                # Decode invite token to get church ID
                try:
                    church_id = int(invite_token.split('_')[-1])  # Simplified token parsing
                    # Verify church exists
                    church = db.query(Church).filter(Church.id == church_id).first()
                    if not church:
                        church_id = None
                except (ValueError, IndexError):
                    church_id = None
            
            # Create user
            # Apple doesn't provide name in identity token, so we'll use email prefix
            email = user_info.get('email', '')
            email_prefix = email.split('@')[0] if email else 'User'
            
            user = User(
                email=email or f"{user_info['apple_id']}@privaterelay.appleid.com",
                first_name=email_prefix,
                last_name="",
                role="donor",
                church_id=church_id,
                is_email_verified=user_info.get('email_verified', False),
                password=hash_password("oauth_user"),  # Dummy password for OAuth users
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                last_login=datetime.now(timezone.utc)
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Generate JWT tokens
            tokens = generate_jwt_tokens(user.id, user.role, user.church_id)
            
            # Log audit event
            log_audit_event(
                db=db,
                actor_type="user",
                actor_id=user.id,
                action="APPLE_OAUTH_REGISTER",
                metadata={
                    "resource_type": "user",
                    "resource_id": user.id,
                    "oauth_provider": "apple",
                    "apple_id": user_info['apple_id'],
                    "email": user_info.get('email'),
                    "church_id": church_id
                }
            )
            
            return ResponseFactory.success(
                message="Successfully registered with Apple",
                data={
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "role": user.role,
                        "church_id": user.church_id,
                        "is_email_verified": user.is_email_verified,
                        "profile_picture_url": user.profile_picture_url
                    },
                    "tokens": tokens,
                    "is_new_user": True
                }
            )
    
    except (ValidationError, AuthenticationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Apple OAuth login error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to authenticate with Apple")


@handle_controller_errors
async def initiate_apple_oauth(
    request: Request,
    db: Session = None
) -> ResponseFactory:
    """
    Initiate Apple OAuth flow
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        ResponseFactory with OAuth URL and state
    """
    try:
        oauth_service = OAuthService()
        
        # Generate state parameter for security
        import secrets
        state = secrets.token_urlsafe(32)
        
        # Get Apple OAuth URL
        oauth_url = await oauth_service.get_apple_oauth_url(state)
        
        return ResponseFactory.success(
            message="Apple OAuth URL generated successfully",
            data={
                "oauth_url": oauth_url,
                "state": state,
                "client_id": oauth_service.apple.client_id,
                "scope": "name email"
            }
        )
    
    except Exception as e:
        logging.error(f"Error initiating Apple OAuth: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate Apple OAuth")


@handle_controller_errors
async def apple_oauth_callback(
    code: str,
    state: str,
    request: Request,
    db: Session = None
) -> ResponseFactory:
    """
    Handle Apple OAuth callback
    
    Args:
        code: Authorization code from Apple
        state: State parameter for security
        request: FastAPI request object
        db: Database session
        
    Returns:
        ResponseFactory with authentication result
    """
    try:
        oauth_service = OAuthService()
        
        # Exchange code for user info
        user_info = await oauth_service.apple.verify_authorization_code(code)
        
        if not user_info.get('apple_id'):
            raise ValidationError("Apple ID is required for authentication")
        
        # Check if user already exists
        user = None
        if user_info.get('email'):
            user = db.query(User).filter(
                User.email == user_info['email'],
                User.role == "donor"
            ).first()
        
        if user:
            # Update last login
            user.last_login = datetime.now(timezone.utc)
            user.updated_at = datetime.now(timezone.utc)
            db.commit()
            
            # Generate JWT tokens
            tokens = generate_jwt_tokens(user.id, user.role, user.church_id)
            
            return ResponseFactory.success(
                message="Successfully authenticated with Apple",
                data={
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "role": user.role,
                        "church_id": user.church_id,
                        "is_email_verified": user.is_email_verified,
                        "profile_picture_url": user.profile_picture_url
                    },
                    "tokens": tokens,
                    "is_new_user": False
                }
            )
        else:
            # Create new user
            email = user_info.get('email', '')
            email_prefix = email.split('@')[0] if email else 'User'
            
            user = User(
                email=email or f"{user_info['apple_id']}@privaterelay.appleid.com",
                first_name=email_prefix,
                last_name="",
                role="donor",
                is_email_verified=user_info.get('email_verified', False),
                password=hash_password("oauth_user"),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                last_login=datetime.now(timezone.utc)
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Generate JWT tokens
            tokens = generate_jwt_tokens(user.id, user.role, user.church_id)
            
            return ResponseFactory.success(
                message="Successfully registered with Apple",
                data={
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "role": user.role,
                        "church_id": user.church_id,
                        "is_email_verified": user.is_email_verified,
                        "profile_picture_url": user.profile_picture_url
                    },
                    "tokens": tokens,
                    "is_new_user": True
                }
            )
    
    except (ValidationError, AuthenticationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Apple OAuth callback error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to process Apple OAuth callback")
