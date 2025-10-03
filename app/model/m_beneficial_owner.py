"""
Beneficial Owner Model

Stores information about beneficial owners and control persons for KYC compliance.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.utils.database import Base


class BeneficialOwner(Base):
    __tablename__ = "beneficial_owners"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    
    # Basic Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    title = Column(String(100), nullable=True)
    is_primary = Column(Boolean, default=False)
    
    # Personal Information
    date_of_birth = Column(DateTime, nullable=True)
    ssn_full = Column(String(9), nullable=True)  # Full SSN for compliance
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Address Information
    address_line_1 = Column(String(255), nullable=True)
    address_line_2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Government ID Information
    gov_id_type = Column(String(50), nullable=True)  # driver_license, passport, etc.
    gov_id_number = Column(String(100), nullable=True)
    gov_id_front = Column(Text, nullable=True)  # File path
    gov_id_back = Column(Text, nullable=True)   # File path
    
    # Citizenship and Residence
    country_of_citizenship = Column(String(100), nullable=True)
    country_of_residence = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    church = relationship("Church", back_populates="beneficial_owners")