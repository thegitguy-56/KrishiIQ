from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserRole


class LoginRequest(BaseModel):
    phone: str
    password: str


class RegisterRequest(BaseModel):
    phone: str
    password: str
    name: str
    email: EmailStr
    district: str
    state: str = "Tamil Nadu"
    preferred_language: str = "en"
    role: UserRole = UserRole.FARMER
    total_land_acres: Optional[float] = None
    soil_health_card_id: Optional[str] = None
    agristack_id: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    preferred_language: str


class UserOut(BaseModel):
    id: str
    phone: str
    role: UserRole
    preferred_language: str
    is_active: bool

    class Config:
        from_attributes = True
