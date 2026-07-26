import os
from typing import Dict, List, Optional

try:
    import joblib
    import numpy as np
    _ML_AVAILABLE = True
except ImportError:
    _ML_AVAILABLE = False


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

# Trained model's known categories (from crop_encoder.classes_ / soil_encoder.classes_,
# lowercased for matching). Any crop or soil type outside these sets falls back to the
# heuristic formula below — the trained model genuinely has no signal for them, so
# forcing a prediction would be worse than being upfront that it isn't covered.
ML_KNOWN_CROPS = {"barley", "cotton", "maize", "rice", "soybean", "wheat"}
ML_KNOWN_SOILS = {"chalky", "clay", "loam", "peaty", "sandy", "silt"}

# R2 on held-out test data (GradientBoostingRegressor, trained on
# crop + soil_type + rainfall_mm + temperature_celsius -> yield_tons_per_hectare).
# Used to report an honest confidence figure rather than a made-up constant.
ML_MODEL_R2 = 0.59

TONS_HECTARE_TO_KG_ACRE = 1000 / 2.471


class YieldPredictor:
    def __init__(self, weights_dir: str):
        self.model = None
        self.crop_encoder = None
        self.soil_encoder = None
        self.feature_columns = None

        if not _ML_AVAILABLE:
            print("joblib/numpy not available. Using heuristic-only yield predictor.")
            return

        model_path = os.path.join(weights_dir, "yield_predictor_model.pkl")
        crop_enc_path = os.path.join(weights_dir, "crop_encoder.pkl")
        soil_enc_path = os.path.join(weights_dir, "soil_encoder.pkl")
        feature_cols_path = os.path.join(weights_dir, "feature_columns.pkl")

        if not all(os.path.exists(p) for p in [model_path, crop_enc_path, soil_enc_path, feature_cols_path]):
            print(f"Trained yield model files not found in {weights_dir}. Using heuristic-only yield predictor.")
            return

        try:
            self.model = joblib.load(model_path)
            self.crop_encoder = joblib.load(crop_enc_path)
            self.soil_encoder = joblib.load(soil_enc_path)
            self.feature_columns = joblib.load(feature_cols_path)
            print("Yield model loaded successfully from", weights_dir)
        except Exception as exc:
            print(f"Failed to load yield model artifacts: {exc}. Using heuristic-only yield predictor.")
            self.model = None

    def _ml_available_for(self, crop_name: str, soil_type: Optional[str],
                           rainfall_mm: Optional[float], temperature_avg: Optional[float]) -> bool:
        if self.model is None:
            return False
        if rainfall_mm is None or temperature_avg is None:
            return False
        if crop_name.lower() not in ML_KNOWN_CROPS:
            return False
        if soil_type is None or soil_type.lower() not in ML_KNOWN_SOILS:
            return False
        return True

    def _predict_ml(self, crop_name: str, soil_type: str, rainfall_mm: float,
                     temperature_avg: float) -> float:
        """Returns predicted yield in kg/acre using the trained model."""
        crop_encoded = self.crop_encoder.transform([crop_name.capitalize()])[0]
        soil_encoded = self.soil_encoder.transform([soil_type.capitalize()])[0]

        features = np.array([[crop_encoded, soil_encoded, rainfall_mm, temperature_avg]])
        yield_tons_per_hectare = self.model.predict(features)[0]
        yield_kg_per_acre = yield_tons_per_hectare * TONS_HECTARE_TO_KG_ACRE
        return float(yield_kg_per_acre)

    def predict(
        self,
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
        use_ml = self._ml_available_for(crop_name, soil_type, rainfall_mm, temperature_avg)

        if use_ml:
            try:
                predicted_per_acre = self._predict_ml(crop_name, soil_type, rainfall_mm, temperature_avg)
                prediction_method = "ml_model"
                confidence = round(ML_MODEL_R2 * 100, 1)
            except Exception as exc:
                print(f"ML prediction failed ({exc}), falling back to heuristic.")
                use_ml = False

        if not use_ml:
            predicted_per_acre, confidence = _heuristic_predict(
                crop_name, soil_type, avg_soil_moisture, avg_soil_ph, disease_severity
            )
            prediction_method = "heuristic_fallback"

        # Apply disease severity as a post-hoc adjustment either way — the trained
        # model has no disease signal at all, and the heuristic already factors it in
        # via its own multiplier inside _heuristic_predict, so only adjust here for ML path.
        if use_ml:
            disease_mult = {"none": 1.0, "low": 0.95, "medium": 0.85, "high": 0.7, "critical": 0.5}
            predicted_per_acre *= disease_mult.get(disease_severity, 1.0)

        total_predicted = predicted_per_acre * area_acres

        return {
            "predicted_yield_kg": round(total_predicted, 1),
            "yield_per_acre_kg": round(predicted_per_acre, 1),
            "confidence_percent": confidence,
            "prediction_method": prediction_method,
            "limiting_factors": _get_limiting_factors(
                avg_soil_moisture, avg_soil_ph, avg_nitrogen, disease_severity
            ),
        }


def _heuristic_predict(crop_name, soil_type, avg_soil_moisture, avg_soil_ph, disease_severity):
    """Original rule-based formula — used when the trained model doesn't cover this
    crop/soil combination (e.g. sugarcane, groundnut, sorghum, sandy_loam, black_cotton,
    red_laterite — none of which are present in the public dataset the model was trained on)."""
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
    return predicted_per_acre, 72.0  # confidence unchanged from original heuristic


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


_predictor_instance = None


def get_yield_predictor(weights_dir: str) -> YieldPredictor:
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = YieldPredictor(weights_dir)
    return _predictor_instance


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
    weights_dir: str = "./ml/weights",
) -> Dict:
    """Backward-compatible module-level function — same signature as the original,
    so no call sites elsewhere in the backend need to change."""
    predictor = get_yield_predictor(weights_dir)
    return predictor.predict(
        crop_name, area_acres, soil_type, avg_soil_moisture, avg_soil_ph,
        avg_nitrogen, rainfall_mm, temperature_avg, disease_severity,
    )