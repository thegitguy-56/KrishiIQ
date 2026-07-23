from pydantic import BaseModel
from typing import Optional, Any
from uuid import UUID


class FarmerOut(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    district: str
    state: str
    soil_health_card_id: Optional[str] = None
    agristack_id: Optional[str] = None
    total_land_acres: float
    profile_data: dict = {}
    phone: Optional[str] = None
    preferred_language: Optional[str] = None

    class Config:
        from_attributes = True


class FarmerUpdate(BaseModel):
    name: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    soil_health_card_id: Optional[str] = None
    agristack_id: Optional[str] = None
    total_land_acres: Optional[float] = None
    profile_data: Optional[Any] = None
    preferred_language: Optional[str] = None
