from sqlalchemy import Column, Float, ForeignKey, DateTime, String, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class DiseaseDetection(Base):
    __tablename__ = "disease_detections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    farm_id = Column(String(36), ForeignKey("farms.id"), nullable=False, index=True)
    image_url = Column(String(500), nullable=False)
    detected_disease = Column(String(200), nullable=True)
    confidence_score = Column(Float, nullable=True)
    severity = Column(String(20), nullable=True)  # low, medium, high, critical
    affected_area_percent = Column(Float, nullable=True)
    treatment_recommendation = Column(Text, nullable=True)
    raw_predictions = Column(JSON, default={})
    is_pest_anomaly = Column(String(10), default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    farm = relationship("Farm", back_populates="disease_detections")
