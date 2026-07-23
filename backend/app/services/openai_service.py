import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


def _is_configured() -> bool:
    return bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip())


def _extract_json(raw: str) -> Optional[Dict[str, Any]]:
    try:
        text = raw.strip()

        if "```" in text:
            parts = text.split("```")
            text = parts[1].strip()
            if text.startswith("json"):
                text = text[4:].strip()

        return json.loads(text)
    except Exception:
        return None


async def _chat(
    messages: List[Dict[str, str]],
    *,
    max_tokens: int = 800,
    temperature: float = 0.4,
) -> Optional[str]:
    if not _is_configured():
        logger.warning("Groq API key not configured")
        return None

    payload = {
        "model": settings.GROQ_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                GROQ_CHAT_URL,
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    except httpx.HTTPStatusError as exc:
        logger.warning(
            "Groq request failed: %s - %s",
            exc.response.status_code,
            exc.response.text,
        )
        return None
    except Exception as exc:
        logger.warning("Groq request failed: %s", exc)
        return None


async def enhance_disease_treatment(
    disease_name: str,
    confidence: float,
    severity: str,
    crop_name: str = "rice",
    district: str = "Tamil Nadu",
) -> Optional[Dict[str, str]]:
    system = (
        "You are KrishiIQ, an expert Indian agricultural extension officer. "
        "Respond ONLY with valid JSON. No markdown."
    )

    user = (
        f"Disease: {disease_name}, confidence: {confidence:.0%}, severity: {severity}, "
        f"crop: {crop_name}, region: {district}, India. "
        'Return JSON exactly like this: '
        '{"treatment_en":"","treatment_hi":"","treatment_ta":"","prevention_en":""}'
    )

    raw = await _chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=500,
        temperature=0.3,
    )

    if not raw:
        return None

    parsed = _extract_json(raw)
    if parsed:
        return {
            "treatment_en": str(parsed.get("treatment_en", "")),
            "treatment_hi": str(parsed.get("treatment_hi", "")),
            "treatment_ta": str(parsed.get("treatment_ta", "")),
            "prevention_en": str(parsed.get("prevention_en", "")),
        }

    return {
        "treatment_en": raw,
        "treatment_hi": raw,
        "treatment_ta": raw,
        "prevention_en": "",
    }


async def generate_advisory_content(
    advisory_type: str,
    context: Dict[str, Any],
    language_hint: str = "en",
) -> Optional[Dict[str, str]]:
    system = (
        "You are KrishiIQ AI advisor for Indian farmers. "
        "Write practical, short advice. "
        "Respond ONLY with valid JSON. No markdown. "
        'JSON format: {"title_en":"","title_hi":"","title_ta":"","body_en":"","body_hi":"","body_ta":"","priority":"normal"}'
    )

    user = (
        f"Type: {advisory_type}. "
        f"Context: {json.dumps(context, default=str)}. "
        f"Preferred language: {language_hint}. "
        "Priority must be one of: normal, high, urgent."
    )

    raw = await _chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=700,
        temperature=0.4,
    )

    if not raw:
        return None

    parsed = _extract_json(raw)
    if not parsed:
        return None

    return {
        "title_en": str(parsed.get("title_en", "")),
        "title_hi": str(parsed.get("title_hi", "")),
        "title_ta": str(parsed.get("title_ta", "")),
        "body_en": str(parsed.get("body_en", "")),
        "body_hi": str(parsed.get("body_hi", "")),
        "body_ta": str(parsed.get("body_ta", "")),
        "priority": str(parsed.get("priority", "normal")),
    }


async def farmer_chat(
    message: str,
    farmer_context: Dict[str, Any],
    history: Optional[List[Dict[str, str]]] = None,
) -> str:
    language = farmer_context.get("language", "en")

    system = (
        "You are KrishiIQ, a helpful agricultural assistant for Indian farmers. "
        "Answer in simple language. "
        f"Preferred language: {language}. "
        "Give practical advice on crops, irrigation, pests, fertilizers, soil, and weather. "
        "Use the farmer context if available. "
        "If unsure, recommend consulting the local agriculture officer."
    )

    context_block = f"Farmer context: {json.dumps(farmer_context, default=str)}"

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": f"{system}\n{context_block}"}
    ]

    if history:
        messages.extend(history[-6:])

    messages.append({"role": "user", "content": message})

    reply = await _chat(messages, max_tokens=600, temperature=0.5)

    if reply:
        return reply

    return (
        "AI assistant is currently unavailable. Please try again later. "
        "For urgent crop disease or pest issues, contact your local agriculture officer."
    )