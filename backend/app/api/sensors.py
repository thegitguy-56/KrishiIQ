from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime, timedelta
from app.database import get_db, get_redis
from app.api.deps import get_current_user, require_farmer
from app.models.user import User
from app.models.sensor_reading import SensorReading
from app.models.farm import Farm
from app.models.farmer import Farmer
from app.schemas.sensor import SensorReadingCreate, SensorReadingOut, LatestSensorData
import json

router = APIRouter(prefix="/sensors", tags=["sensors"])


@router.post("/ingest", response_model=SensorReadingOut)
def ingest_sensor_data(body: SensorReadingCreate, db: Session = Depends(get_db)):
    """IoT device endpoint — no auth required (device API key in production)"""
    farm = db.query(Farm).filter(Farm.id == body.farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    reading = SensorReading(**body.model_dump())
    db.add(reading)
    db.commit()
    db.refresh(reading)

    redis = get_redis()
    if redis:
        redis.setex(f"sensor:latest:{body.farm_id}", 300, json.dumps({
        "soil_moisture_percent": body.soil_moisture_percent,
        "soil_ph": body.soil_ph,
        "nitrogen_ppm": body.nitrogen_ppm,
        "phosphorus_ppm": body.phosphorus_ppm,
        "potassium_ppm": body.potassium_ppm,
        "air_temperature_celsius": body.air_temperature_celsius,
        "recorded_at": reading.recorded_at.isoformat(),
        }))

    return reading


@router.post("/farm/{farm_id}/register-device")
def register_device(
    farm_id: str,
    device_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_farmer),
):
    farmer = db.query(Farmer).filter(Farmer.user_id == user.id).first()

    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found")

    farm = db.query(Farm).filter(
        Farm.id == farm_id,
        Farm.farmer_id == farmer.id,
    ).first()

    if not farm:
        any_farm = db.query(Farm).filter(Farm.id == farm_id).first()
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Farm not found",
                "selected_farm_id": str(farm_id),
                "logged_in_user_id": str(user.id),
                "logged_in_farmer_id": str(farmer.id),
                "farm_exists": any_farm is not None,
                "actual_farm_farmer_id": str(any_farm.farmer_id) if any_farm else None,
            },
        )

    farm.sensor_device_id = device_id
    farm.has_iot_sensor = True

    db.commit()
    db.refresh(farm)

    return {
        "status": "ok",
        "message": "Sensor paired successfully",
        "farm_id": str(farm.id),
        "device_id": device_id,
    }


@router.get("/farm/{farm_id}/latest", response_model=LatestSensorData)
def get_latest_sensor(farm_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    reading = (
        db.query(SensorReading)
        .filter(SensorReading.farm_id == farm_id)
        .order_by(SensorReading.recorded_at.desc())
        .first()
    )

    irrigation_needed = False
    npk_alert = None

    if reading:
        irrigation_needed = (reading.soil_moisture_percent or 50) < 35
        deficiencies = []
        if (reading.nitrogen_ppm or 100) < 60:
            deficiencies.append("N")
        if (reading.phosphorus_ppm or 50) < 30:
            deficiencies.append("P")
        if (reading.potassium_ppm or 80) < 50:
            deficiencies.append("K")
        npk_alert = f"Low {', '.join(deficiencies)}" if deficiencies else None

        moisture = reading.soil_moisture_percent or 50
        ph = reading.soil_ph or 7
        if moisture < 25 or ph < 5.5 or ph > 8:
            soil_status = "poor"
        elif moisture < 40 or ph < 6:
            soil_status = "moderate"
        else:
            soil_status = "good"
    else:
        soil_status = "unknown"

    return LatestSensorData(
        farm_id=farm_id,
        latest_reading=reading,
        soil_health_status=soil_status,
        irrigation_needed=irrigation_needed,
        npk_alert=npk_alert,
    )


@router.get("/farm/{farm_id}/history", response_model=List[SensorReadingOut])
def get_sensor_history(
    farm_id: UUID,
    hours: int = 24,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    since = datetime.utcnow() - timedelta(hours=hours)
    return (
        db.query(SensorReading)
        .filter(SensorReading.farm_id == farm_id, SensorReading.recorded_at >= since)
        .order_by(SensorReading.recorded_at.asc())
        .all()
    )
