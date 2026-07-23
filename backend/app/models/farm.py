from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Farm(Base):
    __tablename__ = "farms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    farmer_id = Column(String(36), ForeignKey("farmers.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    area_acres = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geojson = Column(JSON, nullable=True)
    soil_type = Column(String(50), nullable=True)
    irrigation_source = Column(String(100), nullable=True)
    has_iot_sensor = Column(Boolean, default=False)
    sensor_device_id = Column(String(100), nullable=True)
    district = Column(String(100), nullable=False)
    village = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    farmer = relationship("Farmer", back_populates="farms")
    crop_records = relationship("CropRecord", back_populates="farm", cascade="all, delete-orphan")
    sensor_readings = relationship("SensorReading", back_populates="farm", cascade="all, delete-orphan")
    disease_detections = relationship("DiseaseDetection", back_populates="farm", cascade="all, delete-orphan")
