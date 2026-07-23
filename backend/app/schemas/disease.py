from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class DiseaseDetectionOut(BaseModel):
    id: UUID
    farm_id: UUID
    image_url: str
    detected_disease: Optional[str]
    confidence_score: Optional[float]
    severity: Optional[str]
    affected_area_percent: Optional[float]
    treatment_recommendation: Optional[str]
    is_pest_anomaly: str
    created_at: datetime

    class Config:
        from_attributes = True


class DiseaseDetectionResult(BaseModel):
    disease_name: str
    confidence: float
    severity: str
    affected_area_percent: float
    treatment_en: str
    treatment_hi: str
    treatment_ta: str
    is_pest_anomaly: bool
    top_predictions: Dict[str, float]
