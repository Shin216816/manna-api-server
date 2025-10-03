"""
Apple OAuth Router for Donor Authentication

This router defines the API endpoints for Apple OAuth authentication for donors.
"""

from fastapi import APIRouter, Depends, Body, Request, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.controller.donor.apple_oauth import (
    apple_oauth_login, initiate_apple_oauth, apple_oauth_callback
)
from app.utils.database import get_db
from app.core.responses import SuccessResponse

router = APIRouter(tags=["Donor Apple OAuth"])


class DonorAppleOAuthLoginRequest(BaseModel):
    """Request model for donor Apple OAuth login"""
    identity_token: str = Body(..., description="Apple identity token from client")
    invite_token: str = Body(None, description="Optional invite token for church association")


class DonorAppleOAuthCallbackRequest(BaseModel):
    """Request model for Apple OAuth callback"""
    code: str = Body(..., description="Authorization code from Apple")
    state: str = Body(..., description="State parameter for security")


@router.get("/initiate", response_model=SuccessResponse)
async def initiate_oauth_flow(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Initiate Apple OAuth flow
    
    This endpoint generates an Apple OAuth URL for donor authentication.
    """
    return await initiate_apple_oauth(request, db)


@router.post("/login", response_model=SuccessResponse)
async def login_with_apple(
    request_data: DonorAppleOAuthLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate or create donor using Apple OAuth
    
    This endpoint allows donors to sign up or log in using their Apple account.
    The client must provide a valid Apple identity token.
    """
    return await apple_oauth_login(
        identity_token=request_data.identity_token,
        invite_token=request_data.invite_token,
        request=request,
        db=db
    )


@router.post("/callback", response_model=SuccessResponse)
async def handle_oauth_callback(
    request_data: DonorAppleOAuthCallbackRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Apple OAuth callback
    
    This endpoint processes the authorization code from Apple OAuth.
    """
    return await apple_oauth_callback(
        code=request_data.code,
        state=request_data.state,
        request=request,
        db=db
    )