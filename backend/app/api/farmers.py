from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.deps import get_current_user, require_farmer
from app.models.user import User
from app.models.farmer import Farmer
from app.schemas.farmer import FarmerOut, FarmerUpdate

router = APIRouter(prefix="/farmers", tags=["farmers"])


def _farmer_out(farmer: Farmer, user: User) -> FarmerOut:
    return FarmerOut(
        id=farmer.id,
        user_id=farmer.user_id,
        name=farmer.name,
        district=farmer.district,
        state=farmer.state,
        soil_health_card_id=farmer.soil_health_card_id,
        agristack_id=farmer.agristack_id,
        total_land_acres=farmer.total_land_acres or 0,
        profile_data=farmer.profile_data or {},
        phone=user.phone,
        preferred_language=user.preferred_language,
    )


@router.get("/me", response_model=FarmerOut)
def get_my_profile(db: Session = Depends(get_db), user: User = Depends(require_farmer)):
    farmer = db.query(Farmer).filter(Farmer.user_id == user.id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    return _farmer_out(farmer, user)


@router.patch("/me", response_model=FarmerOut)
def update_my_profile(
    body: FarmerUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_farmer),
):
    farmer = db.query(Farmer).filter(Farmer.user_id == user.id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        if field == "preferred_language" and value:
            user.preferred_language = value
        elif hasattr(farmer, field):
            setattr(farmer, field, value)

    db.commit()
    db.refresh(farmer)
    db.refresh(user)
    return _farmer_out(farmer, user)
