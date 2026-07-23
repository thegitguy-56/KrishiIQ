from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db, get_redis
from app.api.deps import get_current_user, require_farmer
from app.models.user import User
from app.models.farmer import Farmer
from app.models.farm import Farm
from app.models.sensor_reading import SensorReading
from app.models.disease_detection import DiseaseDetection
from app.models.advisory import Advisory
from app.schemas.advisory import PersonalizedAdvisory
from app.services import advisory_service
from app.services.weather_service import get_weather_forecast

router = APIRouter(prefix="/advisory", tags=["advisory"])


def normalize_weather_summary(weather):
    if not isinstance(weather, dict):
        return {}

    current = weather.get("current", weather)

    temperature = (
        current.get("temperature")
        or current.get("temp")
        or current.get("temp_c")
    )

    humidity = current.get("humidity")

    rain = (
        current.get("rain")
        or current.get("rain_mm")
        or current.get("precipitation")
        or current.get("precipitation_mm")
        or 0
    )

    condition = (
        current.get("condition")
        or current.get("weather")
        or current.get("description")
        or "Clear"
    )

    return {
        "temperature": temperature,
        "humidity": humidity,
        "rain": rain,
        "condition": condition,
    }


@router.get("/personalized", response_model=PersonalizedAdvisory)
async def get_personalized_advisory(
    db: Session = Depends(get_db),
    user: User = Depends(require_farmer),
):
    farmer = db.query(Farmer).filter(Farmer.user_id == user.id).first()

    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found")

    farms = db.query(Farm).filter(Farm.farmer_id == farmer.id).all()

    weather = {}

    if farms and farms[0].latitude is not None and farms[0].longitude is not None:
        try:
            redis = get_redis()
            weather = await get_weather_forecast(
                farms[0].latitude,
                farms[0].longitude,
                redis,
            )
        except Exception as e:
            print("WEATHER ERROR:", e)
            weather = {}

    for farm in farms:
        latest_sensor = (
            db.query(SensorReading)
            .filter(SensorReading.farm_id == farm.id)
            .order_by(SensorReading.recorded_at.desc())
            .first()
        )

        try:
            advisory_service.generate_irrigation_advisory(
                db, farmer, farm, latest_sensor, weather
            )

            advisory_service.generate_fertilizer_advisory(
                db, farmer, farm, latest_sensor
            )

            await advisory_service.generate_ai_weather_advisory(
                db, farmer, farm, weather
            )

        except Exception as e:
            print("ADVISORY GENERATION ERROR:", e)

        recent_detection = (
            db.query(DiseaseDetection)
            .filter(DiseaseDetection.farm_id == farm.id)
            .order_by(DiseaseDetection.created_at.desc())
            .first()
        )

        if recent_detection and recent_detection.detected_disease != "Healthy":
            try:
                await advisory_service.generate_ai_pest_advisory(
                    db, farmer, farm, recent_detection
                )
            except Exception as e:
                print("PEST ADVISORY ERROR:", e)

    db.commit()

    advisories = advisory_service.get_farmer_advisories(db, farmer.id)

    if len(advisories) == 0:
        test_advisory = Advisory(
            farmer_id=farmer.id,
            title_en="General Farm Advisory",
            title_hi="सामान्य कृषि सलाह",
            title_ta="பொது விவசாய ஆலோசனை",
            body_en="No sensor-based advisory is available yet. Add sensor readings or crop data to get personalized recommendations.",
            body_hi="अभी सेंसर आधारित सलाह उपलब्ध नहीं है। व्यक्तिगत सलाह के लिए सेंसर रीडिंग या फसल डेटा जोड़ें।",
            body_ta="இப்போது சென்சார் அடிப்படையிலான ஆலோசனை இல்லை. தனிப்பட்ட பரிந்துரைகளுக்கு சென்சார் அல்லது பயிர் தரவை சேர்க்கவும்.",
            advisory_type="general",
            priority="normal",
            is_read="false",
        )

        db.add(test_advisory)
        db.commit()
        db.refresh(test_advisory)

        advisories = [test_advisory]

    latest_sensor = None

    if farms:
        latest_sensor = (
            db.query(SensorReading)
            .filter(SensorReading.farm_id == farms[0].id)
            .order_by(SensorReading.recorded_at.desc())
            .first()
        )

    soil_summary = {}

    if latest_sensor:
        soil_summary = {
            "moisture": latest_sensor.soil_moisture_percent,
            "ph": latest_sensor.soil_ph,
            "nitrogen": latest_sensor.nitrogen_ppm,
            "phosphorus": latest_sensor.phosphorus_ppm,
            "potassium": latest_sensor.potassium_ppm,
        }

    weather_summary = normalize_weather_summary(weather)

    return PersonalizedAdvisory(
        farmer_name=farmer.name,
        advisories=advisories,
        weather_summary=weather_summary,
        soil_summary=soil_summary,
        crop_stage_summary=advisory_service.get_crop_stage_summary(db, farmer.id),
    )


@router.patch("/{advisory_id}/read")
def mark_read(
    advisory_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    advisory = db.query(Advisory).filter(Advisory.id == advisory_id).first()

    if not advisory:
        raise HTTPException(status_code=404, detail="Advisory not found")

    advisory.is_read = "true"
    db.commit()

    return {"status": "ok"}