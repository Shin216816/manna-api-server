"""
Session Management Endpoints

Provides endpoints for session validation, status checking, and management.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.middleware.auth_middleware import jwt_auth
from app.utils.token_manager import token_manager
from app.services.session_service import session_manager
from app.core.responses import ResponseFactory
from typing import Dict, Any, Optional

router = APIRouter(tags=["Session Management"])

@router.get("/status")
async def check_session_status(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Check if current session is valid and get session info"""
    try:
        # If no authorization header, return unauthenticated
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="No authorization token provided")
        
        # Extract and verify token
        token = authorization.replace("Bearer ", "")
        payload = token_manager.verify_access_token(token, db)
        
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        user_id = payload.get("user_id")
        session_id = payload.get("session_id")
        
        # Handle legacy tokens without session_id
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing user_id")
        
        if not session_id:
            # Legacy token without session - return basic user info
            return ResponseFactory.success(
                message="Session is valid (legacy token)",
                data={
                    "session_id": None,
                    "user_id": user_id,
                    "user_type": payload.get("user_type", "user"),
                    "church_id": payload.get("church_id"),
                    "device_info": None,
                    "created_at": None,
                    "last_activity": None,
                    "is_active": True
                }
            )
        
        # Get session info for modern tokens
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=401, detail="Session expired or invalid")
        
        # Update session activity
        session_manager.update_session_activity(session_id)
        
        return ResponseFactory.success(
            message="Session is valid",
            data={
                "session_id": session.session_id,
                "user_id": session.user_id,
                "user_type": session.user_type,
                "church_id": session.church_id,
                "device_info": session.device_info,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "last_activity": session.last_activity.isoformat() if session.last_activity else None,
                "is_active": session.is_active
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check session status: {str(e)}")

@router.get("/user-sessions")
async def get_user_sessions(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get all active sessions for the current user"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user")
        
        sessions = session_manager.get_user_sessions(user_id)
        
        sessions_data = []
        for session in sessions:
            sessions_data.append({
                "session_id": session.session_id,
                "device_info": session.device_info,
                "ip_address": session.ip_address,
                "user_agent": session.user_agent,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "last_activity": session.last_activity.isoformat() if session.last_activity else None
            })
        
        return ResponseFactory.success(
            message="User sessions retrieved successfully",
            data={
                "user_id": user_id,
                "total_sessions": len(sessions_data),
                "sessions": sessions_data
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user sessions: {str(e)}")

@router.delete("/logout-session/{session_id}")
async def logout_session(
    session_id: str,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Logout from a specific session"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user")
        
        # Validate that the session belongs to the user
        if not session_manager.validate_session(session_id, user_id):
            raise HTTPException(status_code=403, detail="Session does not belong to user")
        
        # Deactivate the session
        session_manager.deactivate_session(session_id)
        
        return ResponseFactory.success(
            message="Session logged out successfully",
            data={"session_id": session_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to logout session: {str(e)}")

@router.delete("/logout-all")
async def logout_all_sessions(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Logout from all sessions for the current user"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user")
        
        # Logout from all sessions
        session_manager.logout_user(user_id)
        
        return ResponseFactory.success(
            message="All sessions logged out successfully",
            data={"user_id": user_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to logout all sessions: {str(e)}")

@router.get("/stats")
async def get_session_stats(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get session statistics (admin only)"""
    try:
        user_type = current_user.get("user_type")
        if user_type not in ["platform_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        stats = session_manager.get_session_stats()
        
        return ResponseFactory.success(
            message="Session statistics retrieved successfully",
            data=stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session stats: {str(e)}")
