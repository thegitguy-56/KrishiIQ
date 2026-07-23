from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.api.deps import get_current_user, require_farmer
from app.models.user import User, UserRole
from app.models.farm import Farm
from app.models.farmer import Farmer
from app.schemas.farm import FarmCreate, FarmUpdate, FarmOut

router = APIRouter(prefix="/farms", tags=["farms"])


def _get_farmer(db: Session, user: User) -> Farmer:
    farmer = db.query(Farmer).filter(Farmer.user_id == user.id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    return farmer


@router.get("/", response_model=List[FarmOut])
def list_farms(db: Session = Depends(get_db), user: User = Depends(require_farmer)):
    farmer = _get_farmer(db, user)

    farms = db.query(Farm).filter(Farm.farmer_id == farmer.id).all()

    return farms


@router.post("/", response_model=FarmOut, status_code=status.HTTP_201_CREATED)
def create_farm(body: FarmCreate, db: Session = Depends(get_db), user: User = Depends(require_farmer)):
    farmer = _get_farmer(db, user)
    farm = Farm(**body.model_dump(), farmer_id=farmer.id)
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@router.get("/{farm_id}", response_model=FarmOut)
def get_farm(farm_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    farmer = _get_farmer(db, user)
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == farmer.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


@router.patch("/{farm_id}", response_model=FarmOut)
def update_farm(farm_id: UUID, body: FarmUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    farmer = _get_farmer(db, user)
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == farmer.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(farm, field, value)
    db.commit()
    db.refresh(farm)
    return farm


@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farm(farm_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    farmer = _get_farmer(db, user)
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == farmer.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    db.delete(farm)
    db.commit()
