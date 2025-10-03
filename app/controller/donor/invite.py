from sqlalchemy.orm import Session
from app.core.responses import ResponseFactory
from app.core.exceptions import MannaException, ValidationError
from app.utils.jwt_handler import create_access_token
from datetime import datetime, timezone, timedelta


def create_invite_token(db: Session, church_id: int, expires_in_minutes: int = 10):
    """Create a JWT token for church invite - no database storage needed"""
    try:
        # Use raw SQL to avoid SQLAlchemy relationship issues
        from app.utils.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, name, city, state FROM churches WHERE id = :church_id AND is_active = true"),
                {"church_id": church_id}
            ).fetchone()
            
            if not result:
                raise ValidationError("Church not found or inactive")
            
            church_id, church_name, city, state = result
        
        payload = {
            "church_id": church_id,
            "type": "church_invite",
            "expires_in_minutes": expires_in_minutes
        }
        
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
        token = create_access_token(payload)
        
        return ResponseFactory.success(
            message="Invite token created successfully",
            data={
                "token": token,
                "expires_at": expires_at.isoformat(),
                "church_id": church_id,
                "church": {
                    "id": church_id,
                    "name": church_name,
                    "city": city,
                    "state": state
                }
            }
        )
    except MannaException:
        raise
    except Exception as e:
        raise ValidationError(f"Failed to create invite token: {str(e)}")


def validate_invite_token(token: str):
    """Validate an invite token without database access"""
    try:
        from app.utils.jwt_handler import verify_access_token
        
        payload = verify_access_token(token)
        if not payload:
            raise ValidationError("Invalid or expired invite token")
        
        if payload.get("type") != "church_invite":
            raise ValidationError("Invalid invite token type")
        
        church_id = payload.get("church_id")
        if not church_id:
            raise ValidationError("Invalid invite token: missing church_id")
        
        return {
            "church_id": church_id,
            "type": payload.get("type")
        }
    except MannaException:
        raise
    except Exception as e:
        raise ValidationError(f"Failed to validate invite token: {str(e)}")
