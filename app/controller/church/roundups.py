from typing import Dict, Any, Optional
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from app.middleware.auth_middleware import jwt_auth
from app.utils.database import get_db
from app.services.church_roundup_service import ChurchRoundupService
from app.core.responses import ResponseFactory


def get_church_roundup_summary(
    church_id: int,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get round-up summary for a church"""
    # Verify user has access to this church
    if current_user.get("church_id") != church_id and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied to this church")
    
    result = ChurchRoundupService.get_church_roundup_summary(church_id, db)
    return ResponseFactory.success(message="Round-up summary retrieved successfully", data=result)


def get_church_transactions(
    church_id: int,
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get transactions for a church with pagination"""
    # Verify user has access to this church
    if current_user.get("church_id") != church_id and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied to this church")
    
    result = ChurchRoundupService.get_church_transactions(
        church_id=church_id,
        db=db,
        page=page,
        limit=limit,
        status=status
    )
    return ResponseFactory.success(message="Transactions retrieved successfully", data=result)


def get_church_roundups(
    church_id: int,
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get round-ups for a church with pagination"""
    # Verify user has access to this church
    if current_user.get("church_id") != church_id and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied to this church")
    
    result = ChurchRoundupService.get_church_roundups(
        church_id=church_id,
        db=db,
        page=page,
        limit=limit,
        status=status
    )
    return ResponseFactory.success(message="Round-ups retrieved successfully", data=result)


def update_church_roundup_settings(
    church_id: int,
    settings_data: Dict[str, Any],
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Update round-up settings for a church"""
    # Verify user has access to this church
    if current_user.get("church_id") != church_id and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied to this church")
    
    result = ChurchRoundupService.update_church_roundup_settings(
        church_id=church_id,
        settings_data=settings_data,
        db=db
    )
    return ResponseFactory.success(message="Settings updated successfully", data=result)


def create_church_roundup_batch(
    church_id: int,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Create a batch of round-ups for a church"""
    # Verify user has access to this church
    if current_user.get("church_id") != church_id and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied to this church")
    
    result = ChurchRoundupService.create_church_roundup_batch(church_id, db)
    return ResponseFactory.success(message="Batch created successfully", data=result)


def get_church_roundup_analytics(
    church_id: int,
    days: int = 30,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get round-up analytics for a church"""
    # Verify user has access to this church
    if current_user.get("church_id") != church_id and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied to this church")
    
    result = ChurchRoundupService.get_church_roundup_analytics(
        church_id=church_id,
        db=db,
        days=days
    )
    return ResponseFactory.success(message="Analytics retrieved successfully", data=result)
