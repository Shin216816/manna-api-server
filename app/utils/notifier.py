from app.model.m_audit_log import AuditLog
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional

def notify_church(church_id: int, message: str, type: str = "info", db: Optional[Session] = None):
    if not church_id or not message or not db:
        return

    note = AuditLog(
        actor_type="system",
        action="NOTIFICATION",
        resource_type="church",
        resource_id=church_id,
        additional_data={
            "message": message,
            "type": type
        },
        created_at=datetime.now(timezone.utc)
    )
    db.add(note)
    db.commit()
