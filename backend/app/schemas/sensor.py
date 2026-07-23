from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class SensorReadingCreate(BaseModel):
    farm_id: UUID
    device_id: str
    soil_moisture_percent: Optional[float] = None
    soil_temperature_celsius: Optional[float] = None
    soil_ph: Optional[float] = None
    nitrogen_ppm: Optional[float] = None
    phosphorus_ppm: Optional[float] = None
    potassium_ppm: Optional[float] = None
    air_temperature_celsius: Optional[float] = None
    air_humidity_percent: Optional[float] = None
    light_lux: Optional[float] = None


class SensorReadingOut(SensorReadingCreate):
    id: UUID
    recorded_at: datetime

    class Config:
        from_attributes = True


class LatestSensorData(BaseModel):
    farm_id: UUID
    latest_reading: Optional[SensorReadingOut]
    soil_health_status: str
    irrigation_needed: bool
    npk_alert: Optional[str]
