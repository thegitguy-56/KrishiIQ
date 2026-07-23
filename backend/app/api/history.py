from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta
from app.database import get_db
from app.api.deps import require_farmer
from app.models.user import User
from app.models.farmer import Farmer
from app.models.farm import Farm
from app.models.crop import CropRecord
from app.models.sensor_reading import SensorReading
from app.models.disease_detection import DiseaseDetection
from app.schemas.crop import CropOut
from app.schemas.sensor import SensorReadingOut
from app.schemas.disease import DiseaseDetectionOut

router = APIRouter(prefix="/history", tags=["history"])


def _get_farmer_farms(db: Session, user: User):
    farmer = db.query(Farmer).filter(Farmer.user_id == user.id).first()
    if not farmer:
        return None, []
    farms = db.query(Farm).filter(Farm.farmer_id == farmer.id).all()
    return farmer, farms


@router.get("/summary")
def history_summary(db: Session = Depends(get_db), user: User = Depends(require_farmer)):
    farmer, farms = _get_farmer_farms(db, user)
    if not farmer:
        return {"error": "Farmer not found"}

    farm_ids = [f.id for f in farms]
    total_area = sum(f.area_acres for f in farms)

    crop_count = db.query(CropRecord).filter(CropRecord.farm_id.in_(farm_ids)).count() if farm_ids else 0
    sensor_count = (
        db.query(SensorReading).filter(SensorReading.farm_id.in_(farm_ids)).count() if farm_ids else 0
    )
    disease_count = (
        db.query(DiseaseDetection).filter(DiseaseDetection.farm_id.in_(farm_ids)).count() if farm_ids else 0
    )

    # Heuristic environmental metrics (production would use real telemetry)
    water_saved_liters = round(total_area * 1200, 0)
    carbon_footprint_kg = round(total_area * 85, 1)
    carbon_reduced_kg = round(total_area * 22, 1)

    return {
        "total_farms": len(farms),
        "total_area_acres": round(total_area, 1),
        "crop_records": crop_count,
        "sensor_readings": sensor_count,
        "disease_scans": disease_count,
        "water_usage": {
            "estimated_saved_liters": water_saved_liters,
            "irrigation_efficiency_percent": 72,
            "period": "last_30_days",
        },
        "carbon_footprint": {
            "estimated_kg_co2": carbon_footprint_kg,
            "reduced_kg_co2": carbon_reduced_kg,
            "trees_equivalent": round(carbon_reduced_kg / 21, 1),
            "period": "last_30_days",
        },
    }


@router.get("/crops", response_model=List[CropOut])
def crop_history(db: Session = Depends(get_db), user: User = Depends(require_farmer)):
    _, farms = _get_farmer_farms(db, user)
    farm_ids = [f.id for f in farms]
    if not farm_ids:
        return []
    return db.query(CropRecord).filter(CropRecord.farm_id.in_(farm_ids)).order_by(CropRecord.created_at.desc()).all()


@router.get("/sensors/{farm_id}", response_model=List[SensorReadingOut])
def sensor_logs(
    farm_id: str,
    hours: int = Query(168, ge=1, le=720),
    db: Session = Depends(get_db),
    user: User = Depends(require_farmer),
):
    _, farms = _get_farmer_farms(db, user)
    if not any(str(f.id) == farm_id for f in farms):
        return []
    since = datetime.utcnow() - timedelta(hours=hours)
    return (
        db.query(SensorReading)
        .filter(SensorReading.farm_id == farm_id, SensorReading.recorded_at >= since)
        .order_by(SensorReading.recorded_at.desc())
        .limit(500)
        .all()
    )


@router.get("/diseases", response_model=List[DiseaseDetectionOut])
def disease_history(
    limit: int = 30,
    db: Session = Depends(get_db),
    user: User = Depends(require_farmer),
):
    _, farms = _get_farmer_farms(db, user)
    farm_ids = [f.id for f in farms]
    if not farm_ids:
        return []
    return (
        db.query(DiseaseDetection)
        .filter(DiseaseDetection.farm_id.in_(farm_ids))
        .order_by(DiseaseDetection.created_at.desc())
        .limit(limit)
        .all()
    )
