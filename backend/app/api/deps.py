from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import auth_service
from app.models.user import User, UserRole

bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    payload = auth_service.decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = auth_service.get_user_by_id(db, payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def _role_value(role) -> str:
    return role.value if hasattr(role, "value") else str(role)


def require_officer(user: User = Depends(get_current_user)) -> User:
    if _role_value(user.role) not in (UserRole.OFFICER.value, UserRole.ADMIN.value):
        raise HTTPException(status_code=403, detail="Officer or admin access required")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if _role_value(user.role) != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def require_farmer(user: User = Depends(get_current_user)) -> User:
    if _role_value(user.role) != UserRole.FARMER.value:
        raise HTTPException(
            status_code=403,
            detail="This endpoint is for farmers only. Officers should use the web dashboard.",
        )
    return user
