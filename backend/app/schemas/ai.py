from pydantic import BaseModel, Field
from typing import List, Optional


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: Optional[List[ChatMessage]] = None


class ChatResponse(BaseModel):
    reply: str
    ai_enabled: bool


class PublicConfig(BaseModel):
    google_maps_api_key: Optional[str] = None
    ai_enabled: bool = False
