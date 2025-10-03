"""
Google OAuth Controller for Donor Authentication

This controller handles comprehensive Google OAuth authentication for donors with proper token verification
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
from app.utils.security import create_access_token, create_refresh_token

def generate_jwt_tokens(user_id: int, role: str, church_id: int = None) -> dict:
    """Generate JWT access and refresh tokens"""
    token_data = {"user_id": user_id, "role": role}
    if church_id:
        token_data["church_id"] = church_id
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }
from app.utils.audit import log_audit_event


@handle_controller_errors
async def google_oauth_login(
    id_token: str,
    invite_token: Optional[str] = None,
    request: Request = None,
    db: Session = None
) -> ResponseFactory:
    """
    Authenticate or create donor using Google OAuth
    
    Args:
        id_token: Google ID token from client
        invite_token: Optional invite token for church association
        request: FastAPI request object
        db: Database session
        
    Returns:
        ResponseFactory with authentication result
    """
    try:
        # Initialize OAuth service
        oauth_service = OAuthService()
        
        # Verify Google ID token
        user_info = await oauth_service.authenticate_google_user(id_token)
        
        if not user_info.get('email'):
            raise ValidationError("Email is required for authentication")
        
        # Check if user already exists
        user = db.query(User).filter(
            User.email == user_info['email'],
            User.role == "donor"
        ).first()
        
        if user:
            # Update last login
            user.last_login = datetime.now(timezone.utc)
            user.updated_at = datetime.now(timezone.utc)
            
            # Update Google ID if not already set
            if user_info.get('google_id') and not user.google_id:
                user.google_id = user_info['google_id']
            
            # Update profile information if available
            if user_info.get('name') and not user.first_name:
                name_parts = user_info['name'].split(' ', 1)
                user.first_name = name_parts[0]
                if len(name_parts) > 1:
                    user.last_name = name_parts[1]
            
            if user_info.get('picture') and not user.profile_picture_url:
                user.profile_picture_url = user_info['picture']
            
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
                action="GOOGLE_OAUTH_LOGIN",
                metadata={
                    "resource_type": "user",
                    "resource_id": user.id,
                    "oauth_provider": "google",
                    "email": user_info['email']
                }
            )
            
            return ResponseFactory.success(
                message="Successfully logged in with Google",
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
                # This is a simplified implementation - in production, you'd verify the token
                try:
                    church_id = int(invite_token.split('_')[-1])  # Simplified token parsing
                    # Verify church exists
                    church = db.query(Church).filter(Church.id == church_id).first()
                    if not church:
                        church_id = None
                except (ValueError, IndexError):
                    church_id = None
            
            # Create user
            name_parts = user_info.get('name', '').split(' ', 1)
            first_name = name_parts[0] if name_parts else user_info.get('given_name', '')
            last_name = name_parts[1] if len(name_parts) > 1 else user_info.get('family_name', '')
            
            user = User(
                email=user_info['email'],
                first_name=first_name,
                last_name=last_name,
                role="donor",
                church_id=church_id,
                is_email_verified=user_info.get('email_verified', False),
                profile_picture_url=user_info.get('picture'),
                google_id=user_info.get('google_id'),  # Store Google ID for OAuth users
                password_hash=None,  # OAuth users don't need passwords
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
                action="GOOGLE_OAUTH_REGISTER",
                metadata={
                    "resource_type": "user",
                    "resource_id": user.id,
                    "oauth_provider": "google",
                    "email": user_info['email'],
                    "church_id": church_id
                }
            )
            
            return ResponseFactory.success(
                message="Successfully registered with Google",
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
        logging.error(f"Google OAuth login error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to authenticate with Google")


@handle_controller_errors
async def initiate_google_oauth(
    request: Request,
    db: Session = None
):
    """
    Initiate Google OAuth flow by redirecting to Google
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        Redirect response to Google OAuth URL
    """
    try:
        from fastapi.responses import RedirectResponse
        from app.config import config
        
        # Extract invite token from query parameters
        invite_token = request.query_params.get('invite')
        
        oauth_service = OAuthService()
        
        # Generate state parameter for security with flow type
        import secrets
        import urllib.parse
        
        # Create state with flow type information
        state_data = {
            'oauth_type': 'donor',
            'nonce': secrets.token_urlsafe(32)
        }
        
        # Include invite token in state if provided
        if invite_token:
            state_data['invite_token'] = invite_token
            
        state = urllib.parse.urlencode(state_data)
        
        # Get the proper redirect URI from config based on environment
        # Always use the configured redirect URI if available
        if config.GOOGLE_REDIRECT_URI:
            redirect_uri = config.GOOGLE_REDIRECT_URI
        else:
            # Fallback based on environment if not configured
            if config.ENVIRONMENT == "production":
                redirect_uri = "https://manna-api-server.onrender.com/api/v1/donor/google-oauth/callback"
            else:
                redirect_uri = "http://localhost:8000/api/v1/donor/google-oauth/callback"
        
        # Get Google OAuth URL with proper redirect URI
        oauth_url = await oauth_service.get_google_oauth_url(state, redirect_uri)
        
        # Store state in session or cache for later verification
        # For now, we'll rely on Google's state parameter validation
        
        # Redirect to Google OAuth
        return RedirectResponse(url=oauth_url)
    
    except Exception as e:
        logging.error(f"Error initiating Google OAuth: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate Google OAuth")


@handle_controller_errors
async def google_oauth_callback(
    code: str,
    state: str,
    request: Request = None,
    db: Session = None
) -> ResponseFactory:
    """
    Handle Google OAuth callback
    
    Args:
        code: Authorization code from Google
        state: State parameter for security
        request: FastAPI request object
        db: Database session
        
    Returns:
        ResponseFactory with authentication result
    """
    try:
        from app.config import config
        
        # Validate database session
        if not db:
            raise ValidationError("Database session is not available")
        
        # Parse invite token from state parameter
        invite_token = None
        if state:
            try:
                # Parse state data (format: oauth_type=donor&invite_token=XXX&nonce=YYY)
                from urllib.parse import parse_qs
                state_params = parse_qs(state)
                # parse_qs returns lists, so get the first value
                invite_token = state_params.get('invite_token', [None])[0]
            except Exception as e:
                logging.warning(f"Failed to parse state parameter: {str(e)}")
                invite_token = None
            
        oauth_service = OAuthService()
        
        # Exchange code for user info - must use same redirect URI as initial request
        # Always use the configured redirect URI if available
        if config.GOOGLE_REDIRECT_URI:
            redirect_uri = config.GOOGLE_REDIRECT_URI
        else:
            # Fallback based on environment if not configured
            if config.ENVIRONMENT == "production":
                redirect_uri = "https://manna-api-server.onrender.com/api/v1/donor/google-oauth/callback"
            else:
                redirect_uri = "http://localhost:8000/api/v1/donor/google-oauth/callback"
            
        user_info = await oauth_service.exchange_google_code_for_user_info(code, redirect_uri)
        
        if not user_info.get('email'):
            raise ValidationError("Email is required for authentication")
        
        # Check if user already exists
        user = db.query(User).filter(
            User.email == user_info['email'],
            User.role == "donor"
        ).first()
        
        if user:
            # Update last login
            user.last_login = datetime.now(timezone.utc)
            user.updated_at = datetime.now(timezone.utc)
            
            # Update Google ID if not already set
            if user_info.get('google_id') and not user.google_id:
                user.google_id = user_info['google_id']
            
            db.commit()
            
            # Generate JWT tokens
            tokens = generate_jwt_tokens(user.id, user.role, user.church_id)
            
            # Log audit event
            log_audit_event(
                db=db,
                actor_type="user",
                actor_id=user.id,
                action="GOOGLE_OAUTH_CALLBACK_LOGIN",
                metadata={
                    "resource_type": "user",
                    "resource_id": user.id,
                    "oauth_provider": "google",
                    "email": user_info['email']
                }
            )
            
            # For popup-based OAuth, send message to parent window
            from fastapi.responses import HTMLResponse
            if request and request.headers.get("user-agent") and "Mozilla" in request.headers.get("user-agent", ""):
                # This is a browser request, send HTML response with postMessage
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Google OAuth Success</title>
                </head>
                <body>
                    <script>
                        window.opener.postMessage({{
                            type: 'OAUTH_SUCCESS',
                            user: {{
                                id: {user.id},
                                email: '{user.email}',
                                first_name: '{user.first_name or ''}',
                                last_name: '{user.last_name or ''}',
                                role: '{user.role}',
                                church_id: {user.church_id or 'null'},
                                is_email_verified: {str(user.is_email_verified).lower()},
                                profile_picture_url: '{user.profile_picture_url or ''}'
                            }},
                            tokens: {{
                                access_token: '{tokens["access_token"]}',
                                refresh_token: '{tokens["refresh_token"]}'
                            }},
                            userData: {{
                                id: {user.id},
                                email: '{user.email}',
                                first_name: '{user.first_name or ''}',
                                last_name: '{user.last_name or ''}',
                                role: '{user.role}',
                                church_id: {user.church_id or 'null'},
                                is_email_verified: {str(user.is_email_verified).lower()},
                                profile_picture_url: '{user.profile_picture_url or ''}',
                                access_token: '{tokens["access_token"]}',
                                refresh_token: '{tokens["refresh_token"]}',
                                user_id: {user.id},
                                is_new_user: False
                            }}
                        }}, '*');
                        window.close();
                    </script>
                    <p>Authentication successful! This window will close automatically.</p>
                </body>
                </html>
                """
                return HTMLResponse(content=html_content)
            else:
                # API request, return JSON response
                return ResponseFactory.success(
                    message="Successfully authenticated with Google",
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
            # Handle church association from invite token
            church_id = None
            if invite_token:
                try:
                    # Validate and decode invite token to get church ID
                    from app.controller.donor.invite import validate_invite_token
                    invite_data = validate_invite_token(invite_token)
                    church_id = invite_data.get('church_id')
                    
                    # Verify church exists
                    from app.model.m_church import Church
                    if church_id:
                        church = db.query(Church).filter(Church.id == church_id).first()
                        if not church:
                            church_id = None
                except Exception as e:
                    logging.warning(f"Failed to process invite token for church association: {str(e)}")
                    church_id = None
            
            name_parts = user_info.get('name', '').split(' ', 1)
            first_name = name_parts[0] if name_parts else user_info.get('given_name', '')
            last_name = name_parts[1] if len(name_parts) > 1 else user_info.get('family_name', '')
            
            user = User(
                email=user_info['email'],
                first_name=first_name,
                last_name=last_name,
                role="donor",
                church_id=church_id,  # Associate with church if invite token provided
                is_email_verified=user_info.get('email_verified', False),
                profile_picture_url=user_info.get('picture'),
                google_id=user_info.get('google_id'),  # Store Google ID for OAuth users
                password_hash=None,  # OAuth users don't need passwords
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
                action="GOOGLE_OAUTH_CALLBACK_REGISTER",
                metadata={
                    "resource_type": "user",
                    "resource_id": user.id,
                    "oauth_provider": "google",
                    "email": user_info['email']
                }
            )
            
            # For popup-based OAuth, send message to parent window
            from fastapi.responses import HTMLResponse
            if request and request.headers.get("user-agent") and "Mozilla" in request.headers.get("user-agent", ""):
                # This is a browser request, send HTML response with postMessage
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Google OAuth Success</title>
                </head>
                <body>
                    <script>
                        window.opener.postMessage({{
                            type: 'OAUTH_SUCCESS',
                            user: {{
                                id: {user.id},
                                email: '{user.email}',
                                first_name: '{user.first_name or ''}',
                                last_name: '{user.last_name or ''}',
                                role: '{user.role}',
                                church_id: {user.church_id or 'null'},
                                is_email_verified: {str(user.is_email_verified).lower()},
                                profile_picture_url: '{user.profile_picture_url or ''}'
                            }},
                            tokens: {{
                                access_token: '{tokens["access_token"]}',
                                refresh_token: '{tokens["refresh_token"]}'
                            }},
                            userData: {{
                                id: {user.id},
                                email: '{user.email}',
                                first_name: '{user.first_name or ''}',
                                last_name: '{user.last_name or ''}',
                                role: '{user.role}',
                                church_id: {user.church_id or 'null'},
                                is_email_verified: {str(user.is_email_verified).lower()},
                                profile_picture_url: '{user.profile_picture_url or ''}',
                                access_token: '{tokens["access_token"]}',
                                refresh_token: '{tokens["refresh_token"]}',
                                user_id: {user.id},
                                is_new_user: True
                            }}
                        }}, '*');
                        window.close();
                    </script>
                    <p>Registration successful! This window will close automatically.</p>
                </body>
                </html>
                """
                return HTMLResponse(content=html_content)
            else:
                # API request, return JSON response
                return ResponseFactory.success(
                    message="Successfully registered with Google",
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
        logging.error(f"OAuth validation/auth error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Google OAuth callback error: {str(e)}", exc_info=True)
        if db:
            db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process Google OAuth callback: {str(e)}")