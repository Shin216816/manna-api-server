"""
Plaid Items Model

Stores Plaid item information for bank account connections.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.utils.database import Base


class PlaidItem(Base):
    __tablename__ = "plaid_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    item_id = Column(String(255), unique=True, nullable=False, index=True)
    access_token = Column(Text, nullable=False)  # Encrypted in production
    institution_id = Column(String(255), nullable=True)
    institution_name = Column(String(255), nullable=True)
    
    # Status tracking
    status = Column(String(20), default="active", nullable=False)  # active, inactive, error
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="plaid_items")
    # accounts relationship removed - using on-demand Plaid API fetching