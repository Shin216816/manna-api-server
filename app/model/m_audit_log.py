"""
Audit Log Model

Tracks all compliance and security-related events for audit purposes.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from datetime import datetime, timezone
from app.utils.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Actor Information
    actor_type = Column(String(50), nullable=False)  # user, church_admin, system
    actor_id = Column(Integer, nullable=True)  # ID of the actor
    
    # Action Information
    action = Column(String(100), nullable=False)  # KYC_SUBMITTED, DOCUMENT_UPLOADED, etc.
    resource_type = Column(String(50), nullable=True)  # church, user, donation, etc.
    resource_id = Column(Integer, nullable=True)  # ID of the resource
    
    # Additional Data
    additional_data = Column(JSON, nullable=True)  # Additional context data
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Indexes for common queries
    __table_args__ = (
        {"mysql_engine": "InnoDB"},
    )