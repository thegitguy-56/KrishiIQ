from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date, datetime
from app.models.crop import CropStatus, Season


class CropCreate(BaseModel):
    farm_id: UUID
    crop_name: str
    crop_variety: Optional[str] = None
    season: Season
    area_acres: float
    sowing_date: Optional[date] = None
    expected_harvest_date: Optional[date] = None


class CropUpdate(BaseModel):
    crop_name: Optional[str] = None
    crop_variety: Optional[str] = None
    status: Optional[CropStatus] = None
    area_acres: Optional[float] = None
    sowing_date: Optional[date] = None
    expected_harvest_date: Optional[date] = None
    actual_harvest_date: Optional[date] = None
    actual_yield_kg: Optional[float] = None


class CropOut(BaseModel):
    id: UUID
    farm_id: UUID
    crop_name: str
    crop_variety: Optional[str]
    season: Season
    status: CropStatus
    area_acres: float
    sowing_date: Optional[date]
    expected_harvest_date: Optional[date]
    actual_yield_kg: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True
