from pydantic import BaseModel
from typing import List
from uuid import UUID


class YieldPredictionOut(BaseModel):
    crop_id: UUID
    farm_id: UUID
    crop_name: str
    area_acres: float
    predicted_yield_kg: float
    yield_per_acre_kg: float
    confidence_percent: float
    prediction_method: str  # "ml_model" or "heuristic_fallback"
    limiting_factors: List[str]

    class Config:
        from_attributes = True