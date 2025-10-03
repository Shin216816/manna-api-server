from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.utils.database import Base
from datetime import datetime, timezone

class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    role = Column(String, default="admin")
    permissions = Column(String, default="admin")  # JSON string of permissions or role-based
    last_login = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superadmin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    @classmethod
    def get_by_email(cls, db, email: str):
        """Get admin user by email"""
        return db.query(cls).filter(cls.email == email).first()
    
    @classmethod
    def get_by_id(cls, db, admin_id: int):
        """Get admin user by ID"""
        return db.query(cls).filter(cls.id == admin_id).first()
    
    @classmethod
    def create(cls, db, **kwargs):
        """Create new admin user"""
        admin = cls(**kwargs)
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin
