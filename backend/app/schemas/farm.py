from pydantic import BaseModel
from typing import Optional, Any
from uuid import UUID


class FarmCreate(BaseModel):
    name: str
    area_acres: float
    latitude: float
    longitude: float
    soil_type: Optional[str] = None
    irrigation_source: Optional[str] = None
    district: str
    village: Optional[str] = None
    geojson: Optional[Any] = None


class FarmUpdate(BaseModel):
    name: Optional[str] = None
    area_acres: Optional[float] = None
    soil_type: Optional[str] = None
    irrigation_source: Optional[str] = None
    has_iot_sensor: Optional[bool] = None
    sensor_device_id: Optional[str] = None


class FarmOut(BaseModel):
    id: UUID
    farmer_id: UUID
    name: str
    area_acres: float
    latitude: float
    longitude: float
    soil_type: Optional[str]
    irrigation_source: Optional[str]
    has_iot_sensor: bool
    district: str
    village: Optional[str]

    class Config:
        from_attributes = True
