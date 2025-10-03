"""
Google OAuth Controller for Church Admin Authentication

This controller handles Google OAuth authentication endpoints for church admins.
"""

from typing import Dict, Any
from fastapi import HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.services.oauth_service import google_oauth_service
from app.core.exceptions import AuthenticationError, ValidationError
from app.core.responses import SuccessResponse
from app.config import config
import secrets
import urllib.parse

def initiate_google_oauth(request: Request, db: Session) -> RedirectResponse:
    """
    Initiate Google OAuth flow by redirecting to Google OAuth
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        RedirectResponse to Google OAuth
    """
    try:
        # Generate state parameter for security
        state = secrets.token_urlsafe(32)
        
        # Build Google OAuth URL with the configured redirect URI from backend .env
        google_oauth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": config.GOOGLE_CLIENT_ID,
            "redirect_uri": config.GOOGLE_REDIRECT_URI,  # Use the configured redirect URI
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }
        
        # Create the full OAuth URL
        oauth_url = f"{google_oauth_url}?{urllib.parse.urlencode(params)}"
        
        return RedirectResponse(url=oauth_url)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to initiate OAuth flow")

def google_oauth_login(
    id_token: str,
    request: Request,
    db: Session = Depends(get_db)
) -> SuccessResponse:
    """
    Authenticate church admin using Google OAuth
    
    Args:
        id_token: Google ID token from client
        request: FastAPI request object
        db: Database session
        
    Returns:
        Authentication response with tokens and user info
    """
    try:
        result = google_oauth_service.authenticate_church_admin(
            id_token_string=id_token,
            db=db,
            request=request
        )
        return result
        
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Authentication failed")

def link_google_account(
    user_id: int,
    id_token: str,
    db: Session = Depends(get_db)
) -> SuccessResponse:
    """
    Link existing church admin account to Google OAuth
    
    Args:
        user_id: User ID to link
        id_token: Google ID token from client
        db: Database session
        
    Returns:
        Success response confirming account linking
    """
    try:
        result = google_oauth_service.link_google_account(
            user_id=user_id,
            id_token_string=id_token,
            db=db
        )
        return result
        
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to link Google account")
