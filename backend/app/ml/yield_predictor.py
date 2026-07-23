import numpy as np
from typing import Dict, List, Optional
import json


CROP_BASE_YIELDS = {
    "rice": 4500,
    "wheat": 3800,
    "cotton": 1800,
    "sugarcane": 70000,
    "groundnut": 2200,
    "maize": 5000,
    "sorghum": 2500,
    "soybean": 2000,
}

SOIL_MULTIPLIERS = {
    "clay": 1.1,
    "loam": 1.2,
    "sandy_loam": 1.0,
    "sandy": 0.85,
    "black_cotton": 1.15,
    "red_laterite": 0.9,
}


def predict_yield(
    crop_name: str,
    area_acres: float,
    soil_type: Optional[str],
    avg_soil_moisture: Optional[float],
    avg_soil_ph: Optional[float],
    avg_nitrogen: Optional[float],
    rainfall_mm: Optional[float],
    temperature_avg: Optional[float],
    disease_severity: str = "none",
) -> Dict:
    base = CROP_BASE_YIELDS.get(crop_name.lower(), 3000)
    soil_mult = SOIL_MULTIPLIERS.get((soil_type or "loam").lower(), 1.0)

    moisture_mult = 1.0
    if avg_soil_moisture is not None:
        if 40 <= avg_soil_moisture <= 70:
            moisture_mult = 1.1
        elif avg_soil_moisture < 20:
            moisture_mult = 0.7
        elif avg_soil_moisture > 85:
            moisture_mult = 0.85

    ph_mult = 1.0
    if avg_soil_ph is not None:
        if 6.0 <= avg_soil_ph <= 7.5:
            ph_mult = 1.05
        elif avg_soil_ph < 5.5 or avg_soil_ph > 8.5:
            ph_mult = 0.8

    disease_mult = {"none": 1.0, "low": 0.95, "medium": 0.85, "high": 0.7, "critical": 0.5}
    d_mult = disease_mult.get(disease_severity, 1.0)

    predicted_per_acre = base * soil_mult * moisture_mult * ph_mult * d_mult
    total_predicted = predicted_per_acre * area_acres

    return {
        "predicted_yield_kg": round(total_predicted, 1),
        "yield_per_acre_kg": round(predicted_per_acre, 1),
        "confidence_percent": 72.0,
        "limiting_factors": _get_limiting_factors(avg_soil_moisture, avg_soil_ph, avg_nitrogen, disease_severity),
    }


def _get_limiting_factors(moisture, ph, nitrogen, disease_severity) -> List[str]:
    factors = []
    if moisture is not None and moisture < 25:
        factors.append("Low soil moisture — irrigation recommended")
    if ph is not None and (ph < 5.5 or ph > 8.0):
        factors.append(f"Suboptimal soil pH ({ph:.1f}) — consider soil amendment")
    if nitrogen is not None and nitrogen < 50:
        factors.append("Low nitrogen — apply urea or organic compost")
    if disease_severity in ("high", "critical"):
        factors.append("High disease pressure — immediate treatment required")
    return factors
