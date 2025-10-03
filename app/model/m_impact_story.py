from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.utils.database import Base

class ImpactStory(Base):
    __tablename__ = "impact_stories"
    
    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False)
    
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    amount_used = Column(Numeric(10, 2), nullable=False)
    category = Column(String(50), nullable=False)
    status = Column(String(20), default="draft")
    
    image_url = Column(String(500))
    published_date = Column(DateTime(timezone=True))
    
    people_impacted = Column(Integer, default=0)
    events_held = Column(Integer, default=0)
    items_purchased = Column(Integer, default=0)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    church = relationship("Church")
    
    def __repr__(self):
        return f"<ImpactStory(id={self.id}, title='{self.title}', church_id={self.church_id})>"
