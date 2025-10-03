from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.middleware.auth_middleware import jwt_auth
from app.controller.donor.dashboard import (
    get_dashboard_overview, get_impact_analytics, get_summary_stats, get_recent_activity, get_church_impact_stories
)

router = APIRouter()

@router.get("/overview")
def donor_get_dashboard_overview(current_user: dict = Depends(jwt_auth), db: Session = Depends(get_db)):
    """Get donor dashboard overview"""
    return get_dashboard_overview(current_user, db)

@router.get("/impact")
def donor_get_impact_analytics(current_user: dict = Depends(jwt_auth), db: Session = Depends(get_db)):
    """Get donor impact analytics"""
    return get_impact_analytics(current_user, db)

@router.get("/summary")
def donor_get_summary_stats(current_user: dict = Depends(jwt_auth), db: Session = Depends(get_db)):
    """Get donor summary statistics"""
    return get_summary_stats(current_user, db)

@router.get("/activity")
def donor_get_recent_activity(current_user: dict = Depends(jwt_auth), db: Session = Depends(get_db)):
    """Get donor recent activity"""
    return get_recent_activity(current_user, db)

@router.get("/impact-stories")
def donor_get_church_impact_stories(current_user: dict = Depends(jwt_auth), db: Session = Depends(get_db)):
    """Get impact stories from donor's church"""
    return get_church_impact_stories(current_user, db)
