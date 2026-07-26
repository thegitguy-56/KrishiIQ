import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import require_farmer
from app.models.user import User
from app.models.farmer import Farmer
from app.models.farm import Farm
from app.models.crop import CropRecord
from app.models.sensor_reading import SensorReading
from app.models.disease_detection import DiseaseDetection
from app.schemas.yield_prediction import YieldPredictionOut
from app.ml.yield_predictor import predict_yield
from app.services import weather_service
from app.config import settings

router = APIRouter(prefix="/crops", tags=["crops"])


def _get_farmer(db: Session, user: User) -> Farmer:
    farmer = db.query(Farmer).filter(Farmer.user_id == user.id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    return farmer


@router.get("/{crop_id}/predict-yield", response_model=YieldPredictionOut)
async def predict_crop_yield(
    crop_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_farmer),
):
    """
    Predicts expected yield for a crop record. Pulls soil type from the farm,
    latest sensor readings (moisture/pH/nitrogen) if available, current weather
    (rainfall/temperature) via the weather service, and the most recent disease
    detection severity for that farm — then calls the yield predictor.

    Uses a trained ML model when the crop/soil combination is one it was trained
    on (see prediction_method in the response); otherwise falls back to the
    rule-based estimate. Both paths are clearly labeled in the response so the
    frontend can display an appropriate confidence indicator.
    """
    farmer = _get_farmer(db, user)

    crop = db.query(CropRecord).filter(CropRecord.id == str(crop_id)).first()
    if not crop:
        raise HTTPException(status_code=404, detail="Crop record not found")

    farm = db.query(Farm).filter(Farm.id == crop.farm_id, Farm.farmer_id == farmer.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found or not owned by this farmer")

    # Latest sensor reading for this farm, if any (soil moisture / pH / nitrogen)
    latest_sensor = (
        db.query(SensorReading)
        .filter(SensorReading.farm_id == farm.id)
        .order_by(SensorReading.recorded_at.desc())
        .first()
    )
    avg_soil_moisture = latest_sensor.soil_moisture_percent if latest_sensor else None
    avg_soil_ph = latest_sensor.soil_ph if latest_sensor else None
    avg_nitrogen = latest_sensor.nitrogen_ppm if latest_sensor else None

    # Weather: current temperature + rainfall summed over the returned forecast window
    rainfall_mm = None
    temperature_avg = None
    try:
        forecast = await weather_service.get_weather_forecast(farm.latitude, farm.longitude)
        current = forecast.get("current", {})
        temperature_avg = current.get("temp_celsius")
        rainfall_mm = sum(f.get("rainfall_mm", 0) for f in forecast.get("forecasts", []))
    except Exception as exc:
        print(f"Weather fetch failed for yield prediction: {exc}")

    # Most recent disease detection for this farm, if any
    latest_detection = (
        db.query(DiseaseDetection)
        .filter(DiseaseDetection.farm_id == farm.id)
        .order_by(DiseaseDetection.created_at.desc())
        .first()
    )
    disease_severity = latest_detection.severity if latest_detection and latest_detection.severity else "none"

    weights_dir = os.path.dirname(settings.YIELD_MODEL_PATH) or "./ml/weights"

    result = predict_yield(
        crop_name=crop.crop_name,
        area_acres=crop.area_acres,
        soil_type=farm.soil_type,
        avg_soil_moisture=avg_soil_moisture,
        avg_soil_ph=avg_soil_ph,
        avg_nitrogen=avg_nitrogen,
        rainfall_mm=rainfall_mm,
        temperature_avg=temperature_avg,
        disease_severity=disease_severity,
        weights_dir=weights_dir,
    )

    return {
        "crop_id": crop.id,
        "farm_id": farm.id,
        "crop_name": crop.crop_name,
        "area_acres": crop.area_acres,
        **result,
    }