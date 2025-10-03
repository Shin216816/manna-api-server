"""
Admin Audit Log Model

Tracks all administrative actions for security and compliance purposes.
This model provides a complete audit trail of admin activities including:
- Authentication events
- Data modifications
- System configuration changes
- User management actions
- Financial operations
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.utils.database import Base
from app.model.m_admin_user import AdminUser
import uuid


class AdminAuditLog(Base):
    """Model for tracking admin actions and system events"""

    __tablename__ = "admin_audit_logs"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Unique identifier for correlation
    correlation_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False, index=True)

    # Admin user who performed the action
    admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=False, index=True)

    # Action details
    action = Column(String(100), nullable=False, index=True)  # e.g., "login", "update_church", "approve_kyc"
    resource_type = Column(String(50), nullable=False, index=True)  # e.g., "church", "user", "system"
    resource_id = Column(Integer, nullable=True, index=True)  # ID of the affected resource

    # Request details
    method = Column(String(10), nullable=True)  # HTTP method (GET, POST, PUT, DELETE)
    endpoint = Column(String(255), nullable=True)  # API endpoint

    # Additional context
    details = Column(JSON, nullable=True)  # Flexible JSON field for action-specific data
    old_values = Column(JSON, nullable=True)  # Previous values before change
    new_values = Column(JSON, nullable=True)  # New values after change

    # Request metadata
    ip_address = Column(String(45), nullable=True, index=True)  # IPv4/IPv6 address
    user_agent = Column(Text, nullable=True)  # Browser/client information
    session_id = Column(String(255), nullable=True, index=True)  # Session identifier

    # Result
    success = Column(Boolean, default=True, nullable=False, index=True)
    error_message = Column(Text, nullable=True)  # Error details if action failed

    # Timing
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    duration_ms = Column(Integer, nullable=True)  # Action duration in milliseconds

    # Security flags
    is_suspicious = Column(Boolean, default=False, nullable=False, index=True)
    risk_score = Column(Integer, default=0, nullable=False)  # 0-100 risk assessment

    # Compliance and retention
    retention_category = Column(String(50), default="standard", nullable=False)  # "standard", "sensitive", "permanent"
    is_exported = Column(Boolean, default=False, nullable=False)  # For compliance exports
    export_date = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    admin_user = relationship("AdminUser", back_populates="audit_logs")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.correlation_id:
            self.correlation_id = uuid.uuid4()

    @classmethod
    def log_action(cls, db, admin_id: int, action: str, resource_type: str,
                   resource_id: int = None, **kwargs):
        """
        Convenience method to create audit log entry

        Args:
            db: Database session
            admin_id: ID of admin user performing action
            action: Action being performed
            resource_type: Type of resource being acted upon
            resource_id: ID of specific resource (optional)
            **kwargs: Additional fields (details, ip_address, etc.)
        """
        log_entry = cls(
            admin_id=admin_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            **kwargs
        )
        db.add(log_entry)
        return log_entry

    @classmethod
    def get_admin_actions(cls, db, admin_id: int, limit: int = 100, offset: int = 0):
        """Get recent actions by a specific admin"""
        return (db.query(cls)
                .filter(cls.admin_id == admin_id)
                .order_by(cls.timestamp.desc())
                .limit(limit)
                .offset(offset)
                .all())

    @classmethod
    def get_resource_history(cls, db, resource_type: str, resource_id: int,
                           limit: int = 100, offset: int = 0):
        """Get audit history for a specific resource"""
        return (db.query(cls)
                .filter(cls.resource_type == resource_type,
                       cls.resource_id == resource_id)
                .order_by(cls.timestamp.desc())
                .limit(limit)
                .offset(offset)
                .all())

    @classmethod
    def get_failed_actions(cls, db, hours: int = 24, limit: int = 100):
        """Get failed actions within the last N hours"""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        return (db.query(cls)
                .filter(cls.success == False, cls.timestamp >= since)
                .order_by(cls.timestamp.desc())
                .limit(limit)
                .all())

    @classmethod
    def get_suspicious_activity(cls, db, hours: int = 24, limit: int = 100):
        """Get suspicious activity within the last N hours"""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        return (db.query(cls)
                .filter(cls.is_suspicious == True, cls.timestamp >= since)
                .order_by(cls.risk_score.desc(), cls.timestamp.desc())
                .limit(limit)
                .all())

    @classmethod
    def get_ip_activity(cls, db, ip_address: str, hours: int = 24):
        """Get all activity from a specific IP within the last N hours"""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        return (db.query(cls)
                .filter(cls.ip_address == ip_address, cls.timestamp >= since)
                .order_by(cls.timestamp.desc())
                .all())

    @classmethod
    def get_action_statistics(cls, db, hours: int = 24):
        """Get action statistics for the last N hours"""
        from sqlalchemy import func
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        stats = db.query(
            cls.action,
            func.count(cls.id).label('count'),
            func.sum(func.cast(cls.success == False, Integer)).label('failures')
        ).filter(
            cls.timestamp >= since
        ).group_by(
            cls.action
        ).all()

        return [
            {
                'action': stat.action,
                'total_count': stat.count,
                'failure_count': stat.failures or 0,
                'success_rate': ((stat.count - (stat.failures or 0)) / stat.count * 100) if stat.count > 0 else 0
            }
            for stat in stats
        ]

    def to_dict(self, include_sensitive: bool = False):
        """Convert to dictionary for API responses"""
        data = {
            'id': self.id,
            'correlation_id': str(self.correlation_id),
            'admin_id': self.admin_id,
            'admin_email': self.admin_user.email if self.admin_user else None,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'method': self.method,
            'endpoint': self.endpoint,
            'success': self.success,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'duration_ms': self.duration_ms,
            'is_suspicious': self.is_suspicious,
            'risk_score': self.risk_score
        }

        if include_sensitive:
            data.update({
                'details': self.details,
                'old_values': self.old_values,
                'new_values': self.new_values,
                'ip_address': self.ip_address,
                'user_agent': self.user_agent,
                'session_id': self.session_id,
                'error_message': self.error_message
            })

        return data

    def __repr__(self):
        return f"<AdminAuditLog(id={self.id}, admin_id={self.admin_id}, action='{self.action}', timestamp='{self.timestamp}')>"


# Add relationship to AdminUser model (this would be added to the AdminUser model file)
"""
In app/model/m_admin_user.py, add this relationship:

audit_logs = relationship("AdminAuditLog", back_populates="admin_user", cascade="all, delete-orphan")
"""
