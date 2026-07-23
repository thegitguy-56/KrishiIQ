from fastapi import APIRouter, Depends, Query
from app.database import get_redis
from app.api.deps import get_current_user
from app.models.user import User
from app.services.weather_service import get_weather_forecast

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/forecast")
async def forecast(
    lat: float = Query(...),
    lon: float = Query(...),
    user: User = Depends(get_current_user),
):
    redis = get_redis()
    return await get_weather_forecast(lat, lon, redis)
