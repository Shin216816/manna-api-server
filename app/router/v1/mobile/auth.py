from fastapi import APIRouter, Depends, status, Query, Request
from sqlalchemy.orm import Session
from app.controller.mobile.auth import (
    register, register_code_confirm, register_code_resend,
    login, logout, forgot_password, verify_otp, reset_password,
    google_oauth_login, apple_oauth_login, refresh_token, biometric_login
)
from app.schema.auth_schema import (
    AuthRegisterRequest, AuthRegisterConfirmRequest, AuthRegisterCodeResendRequest,
    AuthLoginRequest, AuthLogoutRequest, AuthForgotPasswordRequest, 
    AuthVerifyOtpRequest, AuthResetPasswordRequest, GoogleOAuthRequest, 
    AppleOAuthRequest, RefreshTokenRequest
)
from app.utils.database import get_db
from app.core.responses import SuccessResponse

auth_router = APIRouter(tags=["Mobile Authentication"])

@auth_router.post("/register", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
async def register_route(
    data: AuthRegisterRequest,
    db: Session = Depends(get_db)
):
    """User registration for mobile app"""
    return register(data, db)

@auth_router.post("/register/confirm", response_model=SuccessResponse)
async def register_confirm_route(
    data: AuthRegisterConfirmRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Confirm registration with access code"""
    return register_code_confirm(data, db, request)

@auth_router.post("/register/resend-code", response_model=SuccessResponse)
async def register_code_resend_route(
    data: AuthRegisterCodeResendRequest,
    db: Session = Depends(get_db)
):
    """Resend registration access code"""
    return register_code_resend(data, db)

@auth_router.post("/login", response_model=SuccessResponse)
async def login_route(
    data: AuthLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """User login for mobile"""
    return login(data, db, request)

@auth_router.post("/logout", response_model=SuccessResponse)
async def logout_route(
    data: AuthLogoutRequest,
    db: Session = Depends(get_db)
):
    """Logout user"""
    return logout(data, db)

@auth_router.post("/forgot-password", response_model=SuccessResponse)
async def forgot_password_route(
    data: AuthForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """Forgot password for mobile"""
    return forgot_password(data, db)

@auth_router.post("/verify-otp", response_model=SuccessResponse)
async def verify_otp_route(
    data: AuthVerifyOtpRequest,
    db: Session = Depends(get_db)
):
    """Verify OTP for mobile"""
    return verify_otp(data, db)

@auth_router.post("/reset-password", response_model=SuccessResponse)
async def reset_password_route(
    data: AuthResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Reset password for mobile"""
    return reset_password(data, db)

@auth_router.post("/google", response_model=SuccessResponse)
async def google_oauth_route(
    data: GoogleOAuthRequest,
    db: Session = Depends(get_db)
):
    """Google OAuth for mobile"""
    return google_oauth_login(data, db)

@auth_router.post("/apple", response_model=SuccessResponse)
async def apple_oauth_route(
    data: AppleOAuthRequest,
    db: Session = Depends(get_db)
):
    """Apple OAuth for mobile"""
    return apple_oauth_login(data, db)

@auth_router.post("/refresh", response_model=SuccessResponse)
async def refresh_token_route(
    data: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Refresh access token"""
    return refresh_token(data, db, request)

@auth_router.post("/biometric-login", response_model=SuccessResponse)
async def biometric_login_route(
    request: Request,
    biometric_token: str = Query(..., description="Biometric authentication token"),
    db: Session = Depends(get_db)
):
    """Biometric login for mobile"""
    return biometric_login(biometric_token, db, request)
