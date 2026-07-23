from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_response(user) -> TokenResponse:
    role = user.role.value if hasattr(user.role, "value") else user.role

    token_data = {
        "sub": str(user.id),
        "role": role,
    }

    return TokenResponse(
        access_token=auth_service.create_access_token(token_data),
        refresh_token=auth_service.create_refresh_token(token_data),
        user_id=str(user.id),
        role=role,
        preferred_language=user.preferred_language,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if len(req.phone) < 10:
        raise HTTPException(status_code=400, detail="Invalid phone number")

    if auth_service.get_user_by_phone(db, req.phone):
        raise HTTPException(status_code=400, detail="Phone number already registered")

    if req.email and auth_service.get_user_by_email(db, req.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = auth_service.register_user(db, req)

    return _token_response(user)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.get_user_by_phone(db, req.phone)

    if not user or not auth_service.verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid phone or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    return _token_response(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    payload = auth_service.decode_token(refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = auth_service.get_user_by_id(db, payload["sub"])

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return _token_response(user)