import httpx
import json
from typing import Optional, Dict
from app.config import settings


async def get_weather_forecast(lat: float, lon: float, redis_client=None) -> Dict:
    cache_key = f"weather:{lat:.2f}:{lon:.2f}"

    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

    if not settings.OPENWEATHER_API_KEY or settings.OPENWEATHER_API_KEY.startswith("your_"):
        return _mock_weather(lat, lon)

    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat, "lon": lon,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric", "cnt": 40,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    result = _parse_forecast(data)

    if redis_client:
        redis_client.setex(cache_key, 1800, json.dumps(result))

    return result


def _parse_forecast(data: Dict) -> Dict:
    forecasts = []
    for item in data.get("list", [])[:8]:
        forecasts.append({
            "datetime": item["dt_txt"],
            "temp_celsius": item["main"]["temp"],
            "humidity_percent": item["main"]["humidity"],
            "description": item["weather"][0]["description"],
            "rainfall_mm": item.get("rain", {}).get("3h", 0),
            "wind_speed_ms": item["wind"]["speed"],
            "wind_direction_deg": item["wind"]["deg"],
        })
    city = data.get("city", {})
    return {
        "city": city.get("name", ""),
        "country": city.get("country", "IN"),
        "forecasts": forecasts,
        "current": forecasts[0] if forecasts else {},
    }


def _mock_weather(lat: float, lon: float) -> Dict:
    return {
        "city": "Mock City",
        "country": "IN",
        "current": {
            "datetime": "2026-05-21 06:00:00",
            "temp_celsius": 32.4,
            "humidity_percent": 68,
            "description": "partly cloudy",
            "rainfall_mm": 0,
            "wind_speed_ms": 3.2,
            "wind_direction_deg": 220,
        },
        "forecasts": [
            {"datetime": "2026-05-21 06:00:00", "temp_celsius": 32.4, "humidity_percent": 68, "description": "partly cloudy", "rainfall_mm": 0, "wind_speed_ms": 3.2, "wind_direction_deg": 220},
            {"datetime": "2026-05-21 09:00:00", "temp_celsius": 35.1, "humidity_percent": 55, "description": "clear sky", "rainfall_mm": 0, "wind_speed_ms": 4.1, "wind_direction_deg": 215},
            {"datetime": "2026-05-21 12:00:00", "temp_celsius": 38.0, "humidity_percent": 42, "description": "sunny", "rainfall_mm": 0, "wind_speed_ms": 5.0, "wind_direction_deg": 210},
            {"datetime": "2026-05-21 18:00:00", "temp_celsius": 33.5, "humidity_percent": 60, "description": "light rain", "rainfall_mm": 2.4, "wind_speed_ms": 6.2, "wind_direction_deg": 180},
        ],
    }
