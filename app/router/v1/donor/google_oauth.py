"""
Google OAuth Router for Donor Authentication

This router defines the API endpoints for Google OAuth authentication for donors.
"""

from fastapi import APIRouter, Depends, Body, Request, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.controller.donor.google_oauth import (
    google_oauth_login, initiate_google_oauth, google_oauth_callback
)
from app.utils.database import get_db
from app.core.responses import SuccessResponse

router = APIRouter(tags=["Donor Google OAuth"])


class DonorGoogleOAuthLoginRequest(BaseModel):
    """Request model for donor Google OAuth login"""
    id_token: str = Body(..., description="Google ID token from client")
    invite_token: str = Body(None, description="Optional invite token for church association")


class DonorGoogleOAuthCallbackRequest(BaseModel):
    """Request model for Google OAuth callback"""
    code: str = Body(..., description="Authorization code from Google")
    state: str = Body(..., description="State parameter for security")


@router.get("/initiate")
async def initiate_oauth_flow(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Initiate Google OAuth flow by redirecting to Google
    
    This endpoint redirects the user to Google's OAuth page for authentication.
    The popup will be redirected to Google and then back to our callback endpoint.
    """
    return await initiate_google_oauth(request, db)


@router.post("/login", response_model=SuccessResponse)
async def login_with_google(
    request_data: DonorGoogleOAuthLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate or create donor using Google OAuth
    
    This endpoint allows donors to sign up or log in using their Google account.
    The client must provide a valid Google ID token.
    """
    return await google_oauth_login(
        id_token=request_data.id_token,
        invite_token=request_data.invite_token,
        request=request,
        db=db
    )


@router.post("/callback", response_model=SuccessResponse)
async def handle_oauth_callback(
    request_data: DonorGoogleOAuthCallbackRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback
    
    This endpoint processes the authorization code from Google OAuth.
    """
    return await google_oauth_callback(
        code=request_data.code,
        state=request_data.state,
        request=request,
        db=db
    )