from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.models.advisory import AdvisoryType


class AdvisoryOut(BaseModel):
    id: UUID
    farmer_id: UUID
    advisory_type: AdvisoryType
    title_en: str
    title_hi: Optional[str]
    title_ta: Optional[str]
    body_en: str
    body_hi: Optional[str]
    body_ta: Optional[str]
    voice_url_en: Optional[str]
    voice_url_hi: Optional[str]
    voice_url_ta: Optional[str]
    priority: str
    is_read: str
    created_at: datetime

    class Config:
        from_attributes = True


class PersonalizedAdvisory(BaseModel):
    farmer_name: str
    advisories: List[AdvisoryOut]
    weather_summary: dict
    soil_summary: dict
    crop_stage_summary: List[dict]
