from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.controller.public.churches import get_public_churches, get_public_church_by_id
from app.core.responses import SuccessResponse

router = APIRouter()

@router.get("/list", response_model=SuccessResponse)
def list_public_churches(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of churches to return"),
    search: str = Query(default=None, description="Search churches by name, city, or state"),
    db: Session = Depends(get_db)
):
    """Get public list of active churches for donor selection"""
    return get_public_churches(db, limit, search)

@router.get("/{church_id}", response_model=SuccessResponse)
def get_church_by_id(
    church_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific church by ID for public access"""
    return get_public_church_by_id(db, church_id)
