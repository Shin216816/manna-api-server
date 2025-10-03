from app.model.m_audit_log import AuditLog
from sqlalchemy.orm import Session
from typing import Optional

def create_audit_log(db: Session, actor_type: str, actor_id: int, action: str, metadata: Optional[dict] = None):
    log = AuditLog(
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        additional_data=metadata or {}
    )
    db.add(log)
    db.commit()

def log_audit_event(db: Session, actor_type: str, actor_id: int, action: str, metadata: Optional[dict] = None):
    """Log an audit event to the database"""
    try:
        log = AuditLog(
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            additional_data=metadata or {}
        )
        db.add(log)
        # Don't commit here - let the calling function handle the transaction
    except Exception as e:
        # Log error but don't fail the main operation
        print(f"Failed to log audit event: {e}")
