from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User, UserRole
from app.models.farmer import Farmer
from app.schemas.auth import RegisterRequest


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({**data, "exp": expire}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode({**data, "exp": expire, "type": "refresh"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


def get_user_by_phone(db: Session, phone: str) -> Optional[User]:
    return db.query(User).filter(User.phone == phone).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def register_user(db: Session, req: RegisterRequest) -> User:
    user = User(
        phone=req.phone,
        email=req.email,
        hashed_password=hash_password(req.password),
        role=req.role,
        preferred_language=req.preferred_language,
    )
    db.add(user)
    db.flush()

    if req.role == UserRole.FARMER:
        farmer = Farmer(
            user_id=user.id,
            name=req.name,
            district=req.district,
            state=req.state,
            total_land_acres=getattr(req, "total_land_acres", None) or 0.0,
            soil_health_card_id=getattr(req, "soil_health_card_id", None),
            agristack_id=getattr(req, "agristack_id", None),
            profile_data={},
        )
        db.add(farmer)

    db.commit()
    db.refresh(user)
    return user
