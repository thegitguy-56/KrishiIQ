from sqlalchemy import Column, Float, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    farm_id = Column(String(36), ForeignKey("farms.id"), nullable=False, index=True)
    device_id = Column(String(100), nullable=False, index=True)
    soil_moisture_percent = Column(Float, nullable=True)
    soil_temperature_celsius = Column(Float, nullable=True)
    soil_ph = Column(Float, nullable=True)
    nitrogen_ppm = Column(Float, nullable=True)
    phosphorus_ppm = Column(Float, nullable=True)
    potassium_ppm = Column(Float, nullable=True)
    air_temperature_celsius = Column(Float, nullable=True)
    air_humidity_percent = Column(Float, nullable=True)
    light_lux = Column(Float, nullable=True)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    farm = relationship("Farm", back_populates="sensor_readings")
