from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.controller.donor.invite import create_invite_token
from app.schema.donor_schema import InviteCreateRequest

router = APIRouter()

@router.post("/create")
def create_invite(data: InviteCreateRequest, db: Session = Depends(get_db)):
    """Create a church invite token"""
    return create_invite_token(db, data.church_id, data.expires_in_minutes)
