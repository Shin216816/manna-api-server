from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.model.m_church import Church
from app.core.responses import ResponseFactory
from app.config import config
import logging


def toggle_church_status(church_id: int, current_user, db: Session):
    """Toggle church active status"""
    try:
        # Get the church
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")
        
        # Store previous status
        previous_status = church.is_active
        
        # Toggle status
        church.is_active = not church.is_active
        db.commit()
        
        return ResponseFactory.success(
            message="Church status updated successfully",
            data={
                "church_id": church_id,
                "previous_status": config.STATUS_ACTIVE if previous_status else config.STATUS_INACTIVE,
                "new_status": config.STATUS_ACTIVE if church.is_active else config.STATUS_INACTIVE,
                "is_active": church.is_active
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to toggle church status")
