import random
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

from app.config import settings
from app.database import get_redis

logger = logging.getLogger(__name__)

_memory_store: Dict[str, Dict] = {}
OTP_TTL_SECONDS = 300


def _generate_otp() -> str:
    if settings.ENVIRONMENT == "development" and settings.DEV_OTP_CODE:
        return settings.DEV_OTP_CODE
    return str(random.randint(100000, 999999))


def send_otp(phone: str) -> dict:
    otp = _generate_otp()
    payload = {"otp": otp, "expires": (datetime.utcnow() + timedelta(seconds=OTP_TTL_SECONDS)).isoformat()}

    redis = get_redis()
    key = f"otp:{phone}"
    if redis:
        redis.setex(key, OTP_TTL_SECONDS, otp)
    else:
        _memory_store[key] = payload

    logger.info("OTP for %s (dev only log): %s", phone, otp if settings.ENVIRONMENT == "development" else "****")

    result = {"message": "OTP sent successfully", "expires_in_seconds": OTP_TTL_SECONDS}
    if settings.ENVIRONMENT == "development":
        result["dev_otp"] = otp
    return result


def verify_otp(phone: str, otp: str) -> bool:
    redis = get_redis()
    key = f"otp:{phone}"
    if redis:
        stored = redis.get(key)
        if stored and stored == otp:
            redis.delete(key)
            return True
        return False

    entry = _memory_store.get(key)
    if not entry:
        return False
    if entry["otp"] == otp:
        del _memory_store[key]
        return True
    return False
