from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.utils.database import Base
from datetime import datetime, timezone


class AccessCode(Base):
    __tablename__ = "access_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    access_code = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)  # Aware datetime
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))  # Aware

    # Cleanup logic: delete codes past expiration
    @staticmethod
    def delete_expired(db):
        now = datetime.now(timezone.utc)
        db.query(AccessCode).filter(AccessCode.expires_at < now).delete()
        db.commit()
