from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    district = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False, default="Tamil Nadu")
    soil_health_card_id = Column(String(50), nullable=True)
    agristack_id = Column(String(50), nullable=True)
    total_land_acres = Column(Float, default=0.0)
    profile_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="farmer")
    farms = relationship("Farm", back_populates="farmer", cascade="all, delete-orphan")
