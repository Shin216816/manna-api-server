from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session
import logging
from app.controller.donor.profile import (
    get_profile, 
    update_profile, 
    upload_profile_picture, 
    delete_profile_picture,
    update_preferences,
    get_profile_stats,
    export_profile_data,
    deactivate_account,
    reactivate_account,
    associate_church
)
from app.schema.donor_schema import (
    DonorProfileUpdateRequest, 
    DonorPreferencesUpdateRequest
)
from app.middleware.auth_middleware import get_current_user
from app.utils.database import get_db

router = APIRouter()

@router.get("/")
def donor_get_profile(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get donor profile information"""
    return get_profile(current_user, db)

@router.get("")
def donor_get_profile_no_slash(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get donor profile information (no trailing slash)"""
    return get_profile(current_user, db)

@router.put("/")
def donor_update_profile(data: DonorProfileUpdateRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update donor profile information"""
    return update_profile(data, current_user, db)

@router.put("")
def donor_update_profile_no_slash(data: DonorProfileUpdateRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update donor profile information (no trailing slash)"""
    return update_profile(data, current_user, db)

@router.post("/picture")
async def donor_upload_profile_picture(
    current_user: dict = Depends(get_current_user), 
    db: Session = Depends(get_db),
    file: UploadFile = File(...)
):
    """Upload donor profile picture"""
    return await upload_profile_picture(current_user, db, file)

@router.delete("/picture")
def donor_delete_profile_picture(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete donor profile picture"""
    return delete_profile_picture(current_user, db)

@router.put("/preferences")
def donor_update_preferences(data: DonorPreferencesUpdateRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update donor preferences"""
    return update_preferences(data, current_user, db)

@router.get("/stats")
def donor_get_profile_stats(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get donor profile statistics and achievements"""
    return get_profile_stats(current_user, db)

@router.get("/export")
def donor_export_profile_data(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Export donor profile data"""
    return export_profile_data(current_user, db)

@router.post("/deactivate")
def donor_deactivate_account(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Deactivate donor account"""
    return deactivate_account(current_user, db)

@router.post("/reactivate")
def donor_reactivate_account(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Reactivate donor account"""
    return reactivate_account(current_user, db)
