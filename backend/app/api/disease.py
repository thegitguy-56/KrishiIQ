import os
import uuid as uuid_lib
from pathlib import Path
from typing import List

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import require_farmer, get_current_user
from app.models.user import User
from app.models.farmer import Farmer
from app.models.disease_detection import DiseaseDetection
from app.models.farm import Farm
from app.models.crop import CropRecord, CropStatus
from app.schemas.disease import DiseaseDetectionOut, DiseaseDetectionResult
from app.ml.disease_detector import get_detector
from app.config import settings
from app.services import openai_service

router = APIRouter(prefix="/disease", tags=["disease"])

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"


async def _save_image(farm_id: str, filename: str, image_bytes: bytes) -> str:
    farm_dir = UPLOAD_DIR / str(farm_id)
    farm_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid_lib.uuid4().hex}_{os.path.basename(filename or 'crop.jpg')}"
    file_path = farm_dir / safe_name

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(image_bytes)

    return f"uploads/{farm_id}/{safe_name}"


@router.post("/detect", response_model=DiseaseDetectionResult)
async def detect_disease(
    farm_id: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_farmer),
):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    farmer = db.query(Farmer).filter(Farmer.user_id == user.id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found")

    farm = (
        db.query(Farm)
        .filter(
            Farm.id == farm_id,
            Farm.farmer_id == farmer.id,
        )
        .first()
    )

    if not farm:
        any_farm = db.query(Farm).filter(Farm.id == farm_id).first()

        raise HTTPException(
            status_code=404,
            detail={
                "message": "Farm not found for logged-in farmer",
                "selected_farm_id": str(farm_id),
                "logged_in_user_id": str(user.id),
                "logged_in_farmer_id": str(farmer.id),
                "farm_exists": any_farm is not None,
                "actual_farm_farmer_id": str(any_farm.farmer_id) if any_farm else None,
                "db_url": str(engine.url),
                "farm_count": db.query(Farm).count(),
            },
        )

    image_bytes = await image.read()
    image_url = await _save_image(str(farm.id), image.filename or "crop.jpg", image_bytes)

    detector = get_detector(settings.DISEASE_MODEL_PATH)
    result = detector.predict(image_bytes)

    crop = (
        db.query(CropRecord)
        .filter(
            CropRecord.farm_id == farm.id,
            CropRecord.status.in_([CropStatus.GROWING, CropStatus.SOWING]),
        )
        .first()
    )

    crop_name = crop.crop_name if crop else "rice"

    ai_treatment = await openai_service.enhance_disease_treatment(
        result["disease_name"],
        result["confidence"],
        result["severity"],
        crop_name=crop_name,
        district=farm.district,
    )

    if ai_treatment:
        result["treatment_en"] = ai_treatment.get("treatment_en") or result["treatment_en"]
        result["treatment_hi"] = ai_treatment.get("treatment_hi") or result.get("treatment_hi")
        result["treatment_ta"] = ai_treatment.get("treatment_ta") or result.get("treatment_ta")

        if ai_treatment.get("prevention_en"):
            result["treatment_en"] = (
                f"{result['treatment_en']}\n\nPrevention: {ai_treatment['prevention_en']}"
            )

    detection = DiseaseDetection(
        farm_id=farm.id,
        image_url=image_url,
        detected_disease=result["disease_name"],
        confidence_score=result["confidence"],
        severity=result["severity"],
        affected_area_percent=result["affected_area_percent"],
        treatment_recommendation=result["treatment_en"],
        raw_predictions=result["top_predictions"],
        is_pest_anomaly=str(result["is_pest_anomaly"]).lower(),
    )

    db.add(detection)
    db.commit()
    db.refresh(detection)

    return DiseaseDetectionResult(**result)


@router.get("/farm/{farm_id}/history", response_model=List[DiseaseDetectionOut])
def get_disease_history(
    farm_id: str,
    limit: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(require_farmer),
):
    farmer = db.query(Farmer).filter(Farmer.user_id == user.id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found")

    farm = (
        db.query(Farm)
        .filter(
            Farm.id == farm_id,
            Farm.farmer_id == farmer.id,
        )
        .first()
    )

    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    return (
        db.query(DiseaseDetection)
        .filter(DiseaseDetection.farm_id == farm.id)
        .order_by(DiseaseDetection.created_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/alerts/district/{district}", response_model=List[DiseaseDetectionOut])
def get_district_alerts(
    district: str,
    severity: str = "high",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    farms = db.query(Farm).filter(Farm.district == district).all()
    farm_ids = [f.id for f in farms]

    severities = (
        ["high", "critical"]
        if severity == "high"
        else ["medium", "high", "critical"]
    )

    return (
        db.query(DiseaseDetection)
        .filter(
            DiseaseDetection.farm_id.in_(farm_ids),
            DiseaseDetection.severity.in_(severities),
        )
        .order_by(DiseaseDetection.created_at.desc())
        .limit(50)
        .all()
    )