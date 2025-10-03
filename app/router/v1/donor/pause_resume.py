from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.model.m_user import User
from app.model.m_donor_settings import DonorSettings
from app.schema.donor_settings_schema import PauseResumeRequest, PauseResumeResponse
from datetime import datetime

router = APIRouter()

@router.post("/pause-giving", response_model=PauseResumeResponse)
async def pause_giving(
    request: PauseResumeRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pause donor's round-up giving"""
    try:
        user_id = current_user.get("user_id")
        
        # Get or create donor settings
        settings = db.query(DonorSettings).filter(
            DonorSettings.user_id == user_id
        ).first()
        
        if not settings:
            settings = DonorSettings(
                user_id=user_id,
                pause=True,
                pause_reason=request.reason,
                pause_date=datetime.utcnow()
            )
            db.add(settings)
        else:
            settings.pause = True
            settings.pause_reason = request.reason
            settings.pause_date = datetime.utcnow()
            settings.resume_date = None
        
        db.commit()
        db.refresh(settings)
        
        return PauseResumeResponse(
            success=True,
            message="Giving paused successfully",
            data={
                "pause": settings.pause,
                "pause_date": settings.pause_date,
                "pause_reason": settings.pause_reason
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause giving: {str(e)}"
        )

@router.post("/resume-giving", response_model=PauseResumeResponse)
async def resume_giving(
    request: PauseResumeRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resume donor's round-up giving"""
    try:
        user_id = current_user.get("user_id")
        
        # Get donor settings
        settings = db.query(DonorSettings).filter(
            DonorSettings.user_id == user_id
        ).first()
        
        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Donor settings not found"
            )
        
        settings.pause = False
        settings.resume_date = datetime.utcnow()
        settings.pause_reason = None
        
        db.commit()
        db.refresh(settings)
        
        return PauseResumeResponse(
            success=True,
            message="Giving resumed successfully",
            data={
                "pause": settings.pause,
                "resume_date": settings.resume_date,
                "pause_reason": settings.pause_reason
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume giving: {str(e)}"
        )

@router.get("/pause-status")
async def get_pause_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current pause/resume status"""
    try:
        user_id = current_user.get("user_id")
        
        settings = db.query(DonorSettings).filter(
            DonorSettings.user_id == user_id
        ).first()
        
        if not settings:
            return {
                "success": True,
                "data": {
                    "pause": False,
                    "pause_date": None,
                    "resume_date": None,
                    "pause_reason": None
                }
            }
        
        return {
            "success": True,
            "data": {
                "pause": settings.pause,
                "pause_date": settings.pause_date,
                "resume_date": settings.resume_date,
                "pause_reason": settings.pause_reason
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pause status: {str(e)}"
        )
