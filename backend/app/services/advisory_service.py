from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from uuid import UUID
from datetime import datetime, timedelta
from app.models.advisory import Advisory, AdvisoryType
from app.models.farmer import Farmer
from app.models.farm import Farm
from app.models.sensor_reading import SensorReading
from app.models.crop import CropRecord, CropStatus
from app.models.disease_detection import DiseaseDetection
from app.services import openai_service


def generate_irrigation_advisory(
    db: Session,
    farmer: Farmer,
    farm: Farm,
    latest_sensor: Optional[SensorReading],
    weather: Dict,
) -> Optional[Advisory]:
    if not latest_sensor:
        return None

    moisture = latest_sensor.soil_moisture_percent or 50
    rain_expected = sum(f.get("rainfall_mm", 0) for f in weather.get("forecasts", [])[:4]) > 5

    if moisture < 35 and not rain_expected:
        advisory = Advisory(
            farmer_id=farmer.id,
            advisory_type=AdvisoryType.IRRIGATION,
            title_en=f"Irrigation needed for {farm.name}",
            title_hi=f"{farm.name} के लिए सिंचाई आवश्यक",
            title_ta=f"{farm.name}-க்கு நீர்பாசனம் தேவை",
            body_en=f"Soil moisture is at {moisture:.0f}% (below 35% threshold). No rainfall expected in next 12 hours. Irrigate 2–3 inches within 24 hours.",
            body_hi=f"मिट्टी की नमी {moisture:.0f}% है। अगले 12 घंटों में बारिश की उम्मीद नहीं। 24 घंटों के भीतर 2–3 इंच सिंचाई करें।",
            body_ta=f"மண் ஈரப்பதம் {moisture:.0f}% உள்ளது. 12 மணி நேரத்தில் மழை எதிர்பார்க்கப்படவில்லை. 24 மணி நேரத்திற்குள் பாசனம் செய்யவும்.",
            priority="high",
        )
        db.add(advisory)
        db.commit()
        db.refresh(advisory)
        return advisory
    return None


def generate_fertilizer_advisory(
    db: Session,
    farmer: Farmer,
    farm: Farm,
    latest_sensor: Optional[SensorReading],
) -> Optional[Advisory]:
    if not latest_sensor:
        return None

    nitrogen = latest_sensor.nitrogen_ppm or 100
    phosphorus = latest_sensor.phosphorus_ppm or 50
    potassium = latest_sensor.potassium_ppm or 80

    deficiencies = []
    if nitrogen < 60:
        deficiencies.append("Nitrogen (N)")
    if phosphorus < 30:
        deficiencies.append("Phosphorus (P)")
    if potassium < 50:
        deficiencies.append("Potassium (K)")

    if not deficiencies:
        return None

    deficiency_str = ", ".join(deficiencies)
    advisory = Advisory(
        farmer_id=farmer.id,
        advisory_type=AdvisoryType.FERTILIZER,
        title_en=f"Nutrient deficiency detected: {deficiency_str}",
        title_hi=f"पोषक तत्वों की कमी: {deficiency_str}",
        title_ta=f"ஊட்டச்சத்து குறைபாடு: {deficiency_str}",
        body_en=f"Soil analysis shows deficiency in {deficiency_str}. Apply recommended fertilizers based on crop stage. Consult your agriculture officer for dosage.",
        body_hi=f"मिट्टी विश्लेषण में {deficiency_str} की कमी दिखी। फसल के चरण के अनुसार उर्वरक डालें।",
        body_ta=f"மண் பரிசோதனையில் {deficiency_str} குறைபாடு உள்ளது. பயிர் நிலைக்கு ஏற்ப உரம் இடவும்.",
        priority="normal",
    )
    db.add(advisory)
    db.commit()
    db.refresh(advisory)
    return advisory


async def generate_ai_weather_advisory(
    db: Session,
    farmer: Farmer,
    farm: Farm,
    weather: Dict,
) -> Optional[Advisory]:
    forecasts = weather.get("forecasts", [])
    heavy_rain = sum(f.get("rainfall_mm", 0) for f in forecasts[:6]) > 25
    if not heavy_rain:
        return None

    recent = (
        db.query(Advisory)
        .filter(
            Advisory.farmer_id == farmer.id,
            Advisory.advisory_type == AdvisoryType.WEATHER_ALERT,
            Advisory.created_at >= datetime.utcnow() - timedelta(hours=12),
        )
        .first()
    )
    if recent:
        return None

    content = await openai_service.generate_advisory_content(
        "weather_alert",
        {"farm": farm.name, "district": farm.district, "heavy_rain_mm": sum(f.get("rainfall_mm", 0) for f in forecasts[:6])},
    )
    if not content:
        advisory = Advisory(
            farmer_id=farmer.id,
            advisory_type=AdvisoryType.WEATHER_ALERT,
            title_en=f"Heavy rain expected near {farm.name}",
            title_hi=f"{farm.name} के पास भारी बारिश की संभावना",
            title_ta=f"{farm.name} அருகில் கனமழை எதிர்பார்க்கப்படுகிறது",
            body_en="Heavy rainfall forecast in next 48 hours. Delay fertilizer application and ensure drainage.",
            body_hi="अगले 48 घंटों में भारी बारिश की संभावना। उर्वरक प्रयोग स्थगित करें।",
            body_ta="அடுத்த 48 மணி நேரத்தில் கனமழை. உரம் இடுவதை தாமதப்படுத்தவும்.",
            priority="high",
        )
    else:
        advisory = Advisory(
            farmer_id=farmer.id,
            advisory_type=AdvisoryType.WEATHER_ALERT,
            title_en=content.get("title_en", "Weather alert"),
            title_hi=content.get("title_hi"),
            title_ta=content.get("title_ta"),
            body_en=content.get("body_en", ""),
            body_hi=content.get("body_hi"),
            body_ta=content.get("body_ta"),
            priority=content.get("priority", "high"),
        )
    db.add(advisory)
    db.commit()
    db.refresh(advisory)
    return advisory


async def generate_ai_pest_advisory(
    db: Session,
    farmer: Farmer,
    farm: Farm,
    detection: DiseaseDetection,
) -> Optional[Advisory]:
    recent = (
        db.query(Advisory)
        .filter(
            Advisory.farmer_id == farmer.id,
            Advisory.advisory_type == AdvisoryType.PEST_CONTROL,
            Advisory.created_at >= datetime.utcnow() - timedelta(hours=24),
        )
        .first()
    )
    if recent:
        return None

    content = await openai_service.generate_advisory_content(
        "pest_control",
        {
            "farm": farm.name,
            "disease": detection.detected_disease,
            "severity": detection.severity,
            "confidence": detection.confidence_score,
        },
    )
    if not content:
        return None

    advisory = Advisory(
        farmer_id=farmer.id,
        advisory_type=AdvisoryType.PEST_CONTROL,
        title_en=content.get("title_en", f"Pest alert: {detection.detected_disease}"),
        title_hi=content.get("title_hi"),
        title_ta=content.get("title_ta"),
        body_en=content.get("body_en", detection.treatment_recommendation or ""),
        body_hi=content.get("body_hi"),
        body_ta=content.get("body_ta"),
        priority=content.get("priority", "high"),
        extra_data={"detection_id": str(detection.id), "farm_id": str(farm.id)},
    )
    db.add(advisory)
    db.commit()
    db.refresh(advisory)
    return advisory


def get_crop_stage_summary(db: Session, farmer_id: UUID) -> List[dict]:
    crops = (
        db.query(CropRecord)
        .join(Farm)
        .filter(Farm.farmer_id == farmer_id)
        .order_by(CropRecord.created_at.desc())
        .limit(10)
        .all()
    )
    return [
        {
            "crop_name": c.crop_name,
            "status": c.status.value if hasattr(c.status, "value") else str(c.status),
            "farm_id": str(c.farm_id),
            "area_acres": c.area_acres,
            "sowing_date": c.sowing_date.isoformat() if c.sowing_date else None,
        }
        for c in crops
    ]


def get_farmer_advisories(db: Session, farmer_id: UUID, limit: int = 20) -> List[Advisory]:
    return (
        db.query(Advisory)
        .filter(Advisory.farmer_id == farmer_id)
        .order_by(Advisory.created_at.desc())
        .limit(limit)
        .all()
    )
