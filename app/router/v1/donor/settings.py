"""
Donor Settings Router

Handles donor settings endpoints for roundup configuration and preferences.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.controller.donor.settings import (
    get_donor_settings,
    update_donor_settings,
    pause_giving,
    resume_giving,
    get_roundup_preview
)
from app.core.responses import ResponseFactory
from app.middleware.auth_middleware import get_current_user
from app.utils.database import get_db

# Important: Do not set a prefix here because the aggregator already mounts this router
router = APIRouter(tags=["Donor"])


@router.get("/", response_model=None)
async def get_settings(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get donor settings
    
    Retrieves all donor settings including roundup preferences,
    notification settings, and donation preferences.
    """
    user_id = current_user["id"]
    return get_donor_settings(user_id, db)


@router.put("/", response_model=None)
async def update_settings(
    settings_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update donor settings
    
    Updates donor preferences and settings. Common settings include:
    - frequency: donation collection frequency
    - multiplier: roundup multiplier amount
    - monthly_cap: maximum monthly donation limit
    - pause_giving: temporarily pause donations
    - notifications: email and SMS preferences
    """
    user_id = current_user["id"]
    return update_donor_settings(user_id, settings_data, db)


@router.post("/pause", response_model=None)
async def pause_roundup_giving(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Pause roundup giving
    
    Temporarily pauses all roundup donations for the donor.
    Donations can be resumed later using the resume endpoint.
    """
    user_id = current_user["id"]
    return pause_giving(user_id, db)


@router.post("/resume", response_model=None)
async def resume_roundup_giving(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Resume roundup giving
    
    Resumes roundup donations that were previously paused.
    Donations will resume based on the configured frequency.
    """
    user_id = current_user["id"]
    return resume_giving(user_id, db)


@router.get("/preview", response_model=None)
async def get_roundup_preview(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get roundup preview
    
    Shows a preview of current roundup settings and estimated
    donation impact based on recent transaction history.
    """
    user_id = current_user["id"]
    return get_roundup_preview(user_id, db)