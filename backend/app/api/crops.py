from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.api.deps import require_farmer
from app.models.user import User
from app.models.farmer import Farmer
from app.models.farm import Farm
from app.models.crop import CropRecord
from app.schemas.crop import CropCreate, CropUpdate, CropOut

router = APIRouter(prefix="/crops", tags=["crops"])


def _get_farmer(db: Session, user: User) -> Farmer:
    farmer = db.query(Farmer).filter(Farmer.user_id == user.id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    return farmer


def _verify_farm(db: Session, farmer: Farmer, farm_id: str) -> Farm:
    farm = (
        db.query(Farm)
        .filter(
            Farm.id == str(farm_id),
            Farm.farmer_id == farmer.id,
        )
        .first()
    )

    if not farm:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Farm not found",
                "selected_farm_id": str(farm_id),
                "logged_in_farmer_id": str(farmer.id),
            },
        )

    return farm


@router.get("", response_model=List[CropOut])
@router.get("/", response_model=List[CropOut])
def list_crops(
    db: Session = Depends(get_db),
    user: User = Depends(require_farmer),
):
    farmer = _get_farmer(db, user)

    farms = db.query(Farm).filter(Farm.farmer_id == farmer.id).all()
    farm_ids = [f.id for f in farms]

    if not farm_ids:
        return []

    return (
        db.query(CropRecord)
        .filter(CropRecord.farm_id.in_(farm_ids))
        .order_by(CropRecord.created_at.desc())
        .all()
    )


@router.post("", response_model=CropOut, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=CropOut, status_code=status.HTTP_201_CREATED)
def create_crop(
    body: CropCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_farmer),
):
    farmer = _get_farmer(db, user)

    farm = _verify_farm(db, farmer, str(body.farm_id))

    data = body.model_dump()
    data["farm_id"] = farm.id

    crop = CropRecord(**data)

    db.add(crop)
    db.commit()
    db.refresh(crop)

    return crop


@router.patch("/{crop_id}", response_model=CropOut)
def update_crop(
    crop_id: str,
    body: CropUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_farmer),
):
    farmer = _get_farmer(db, user)

    crop = db.query(CropRecord).filter(CropRecord.id == str(crop_id)).first()

    if not crop:
        raise HTTPException(status_code=404, detail="Crop record not found")

    _verify_farm(db, farmer, str(crop.farm_id))

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(crop, field, value)

    db.commit()
    db.refresh(crop)

    return crop