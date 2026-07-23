from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Enum, Date, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class CropStatus(str, enum.Enum):
    PLANNED = "planned"
    SOWING = "sowing"
    GROWING = "growing"
    HARVESTING = "harvesting"
    COMPLETED = "completed"


class Season(str, enum.Enum):
    KHARIF = "kharif"
    RABI = "rabi"
    ZAID = "zaid"


class CropRecord(Base):
    __tablename__ = "crop_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    farm_id = Column(String(36), ForeignKey("farms.id"), nullable=False, index=True)
    crop_name = Column(String(100), nullable=False)
    crop_variety = Column(String(100), nullable=True)
    season = Column(Enum(Season), nullable=False)
    status = Column(Enum(CropStatus), default=CropStatus.PLANNED)
    sowing_date = Column(Date, nullable=True)
    expected_harvest_date = Column(Date, nullable=True)
    actual_harvest_date = Column(Date, nullable=True)
    area_acres = Column(Float, nullable=False)
    expected_yield_kg = Column(Float, nullable=True)
    actual_yield_kg = Column(Float, nullable=True)
    irrigation_schedule = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    farm = relationship("Farm", back_populates="crop_records")
    advisories = relationship("Advisory", back_populates="crop_record")
