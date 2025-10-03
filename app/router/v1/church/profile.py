from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.controller.church.profile import (
    get_church_profile, update_church_profile, upload_church_logo,
    remove_church_logo, get_church_logo, get_church_contact,
    update_church_contact, get_church_branding, update_church_branding
)
from app.schema.church_schema import ChurchProfileUpdateRequest
from app.utils.database import get_db
from app.middleware.church_admin_auth import church_admin_auth
from app.core.responses import SuccessResponse

profile_router = APIRouter(tags=["Church Profile"])


@profile_router.get("", response_model=SuccessResponse)
async def get_church_profile_route_no_slash(
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get church profile (no trailing slash)"""
    return get_church_profile(current_user["church_id"], db)


@profile_router.put("", response_model=SuccessResponse)
async def update_church_profile_route_no_slash(
    data: ChurchProfileUpdateRequest,
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Update church profile (no trailing slash)"""
    return update_church_profile(current_user["church_id"], data.dict(), db)


@profile_router.post("/logo", response_model=SuccessResponse)
async def upload_church_logo_route(
    file: UploadFile = File(...),
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Upload church logo"""
    return upload_church_logo(current_user["church_id"], file, db)


@profile_router.delete("/logo", response_model=SuccessResponse)
async def remove_church_logo_route(
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Remove church logo"""
    return remove_church_logo(current_user["church_id"], db)


@profile_router.get("/logo", response_model=SuccessResponse)
async def get_church_logo_route(
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get church logo"""
    return get_church_logo(current_user["church_id"], db)


@profile_router.get("/contact", response_model=SuccessResponse)
async def get_church_contact_route(
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get church contact information"""
    return get_church_contact(current_user["church_id"], db)


@profile_router.put("/contact", response_model=SuccessResponse)
async def update_church_contact_route(
    contact_data: dict,
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Update church contact information"""
    return update_church_contact(current_user["church_id"], contact_data, db)


@profile_router.get("/branding", response_model=SuccessResponse)
async def get_church_branding_route(
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get church branding settings"""
    return get_church_branding(current_user["church_id"], db)


@profile_router.put("/branding", response_model=SuccessResponse)
async def update_church_branding_route(
    branding_data: dict,
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Update church branding settings"""
    return update_church_branding(current_user["church_id"], branding_data, db)


@profile_router.get("/", response_model=SuccessResponse)
async def get_church_profile_route(
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get church profile (with trailing slash)"""
    return get_church_profile(current_user["church_id"], db)


@profile_router.put("/", response_model=SuccessResponse)
async def update_church_profile_route(
    data: ChurchProfileUpdateRequest,
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    """Update church profile (with trailing slash)"""
    return update_church_profile(current_user["church_id"], data.dict(), db)
