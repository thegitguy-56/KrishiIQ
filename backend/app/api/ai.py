from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import require_farmer
from app.models.user import User
from app.models.farmer import Farmer
from app.models.farm import Farm
from app.models.sensor_reading import SensorReading
from app.models.crop import CropRecord, CropStatus
from app.schemas.ai import ChatRequest, ChatResponse, PublicConfig
from app.services import openai_service
from app.config import settings

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/config/public", response_model=PublicConfig)
def get_public_config():
    return PublicConfig(
        google_maps_api_key=getattr(settings, "GOOGLE_MAPS_API_KEY", None),
        ai_enabled=openai_service._is_configured(),
    )


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_farmer),
):
    farmer = db.query(Farmer).filter(Farmer.user_id == user.id).first()

    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found")

    farms = db.query(Farm).filter(Farm.farmer_id == farmer.id).all()

    latest_sensor = None
    if farms:
        latest_sensor = (
            db.query(SensorReading)
            .filter(SensorReading.farm_id == farms[0].id)
            .order_by(SensorReading.recorded_at.desc())
            .first()
        )

    crops = (
        db.query(CropRecord)
        .join(Farm)
        .filter(
            Farm.farmer_id == farmer.id,
            CropRecord.status.in_([CropStatus.GROWING, CropStatus.SOWING]),
        )
        .all()
    )

    context = {
        "farmer_name": farmer.name,
        "district": farmer.district,
        "state": farmer.state,
        "farms": [
            {
                "name": f.name,
                "area_acres": f.area_acres,
                "district": f.district,
                "soil_type": f.soil_type,
                "irrigation_source": f.irrigation_source,
            }
            for f in farms
        ],
        "soil": {
            "moisture": latest_sensor.soil_moisture_percent if latest_sensor else None,
            "ph": latest_sensor.soil_ph if latest_sensor else None,
            "nitrogen": latest_sensor.nitrogen_ppm if latest_sensor else None,
            "phosphorus": latest_sensor.phosphorus_ppm if latest_sensor else None,
            "potassium": latest_sensor.potassium_ppm if latest_sensor else None,
        },
        "crops": [
            {
                "name": c.crop_name,
                "status": c.status.value if hasattr(c.status, "value") else str(c.status),
            }
            for c in crops
        ],
        "language": getattr(user, "preferred_language", None) or "en",
    }

    history = []
    if body.history:
        history = [{"role": m.role, "content": m.content} for m in body.history]

    reply = await openai_service.farmer_chat(
        body.message,
        context,
        history,
    )

    return ChatResponse(
        reply=reply,
        ai_enabled=openai_service._is_configured(),
    )