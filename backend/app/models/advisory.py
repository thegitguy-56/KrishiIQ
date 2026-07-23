from sqlalchemy import Column, ForeignKey, DateTime, String, Text, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class AdvisoryType(str, enum.Enum):
    IRRIGATION = "irrigation"
    FERTILIZER = "fertilizer"
    PEST_CONTROL = "pest_control"
    SOWING = "sowing"
    HARVESTING = "harvesting"
    WEATHER_ALERT = "weather_alert"
    GENERAL = "general"


class Advisory(Base):
    __tablename__ = "advisories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    crop_record_id = Column(String(36), ForeignKey("crop_records.id"), nullable=True)
    farmer_id = Column(String(36), ForeignKey("farmers.id"), nullable=False, index=True)
    advisory_type = Column(Enum(AdvisoryType), nullable=False)
    title_en = Column(String(300), nullable=False)
    title_hi = Column(String(300), nullable=True)
    title_ta = Column(String(300), nullable=True)
    body_en = Column(Text, nullable=False)
    body_hi = Column(Text, nullable=True)
    body_ta = Column(Text, nullable=True)
    voice_url_en = Column(String(500), nullable=True)
    voice_url_hi = Column(String(500), nullable=True)
    voice_url_ta = Column(String(500), nullable=True)
    priority = Column(String(10), default="normal")  # low, normal, high, urgent
    extra_data = Column(JSON, default={})
    is_read = Column(String(5), default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    crop_record = relationship("CropRecord", back_populates="advisories")
