from fastapi import APIRouter, Depends, Body, HTTPException, Request
from sqlalchemy.orm import Session
from app.controller.church.auth import (
    login_church_admin, register_church_admin, refresh_church_token
)
from app.schema.church_schema import ChurchAdminLoginRequest, ChurchAdminRegisterRequest
from app.utils.database import get_db
from app.middleware.church_admin_auth import church_admin_auth
from app.core.responses import SuccessResponse

auth_router = APIRouter(tags=["Church Authentication"])

@auth_router.post("/register", response_model=SuccessResponse)
async def register_church_admin_route(
    data: ChurchAdminRegisterRequest,
    db: Session = Depends(get_db)
):
    """Register new church admin"""
    return register_church_admin(data.dict(), db)

@auth_router.post("/login", response_model=SuccessResponse)
async def login_church_admin_route(
    data: ChurchAdminLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Login church admin"""
    return login_church_admin(data.email, data.password, db, request)

@auth_router.post("/logout", response_model=SuccessResponse)
async def logout_church_admin_route(
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Logout church admin"""
    # This would need the refresh token from the request
    # For now, just return success
    return {"success": True, "message": "Logged out successfully"}

@auth_router.post("/refresh", response_model=SuccessResponse)
async def refresh_church_admin_token_route(
    request: Request,
    data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """Refresh church admin token"""
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="refresh_token is required")
    return refresh_church_token(refresh_token, db, request)
