from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict
from app.database import get_db
from app.api.deps import require_officer
from app.models.user import User
from app.models.farm import Farm
from app.models.farmer import Farmer
from app.models.disease_detection import DiseaseDetection
from app.models.sensor_reading import SensorReading
from app.models.crop import CropRecord, CropStatus
from app.ml.gnn_model import build_risk_graph

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
def get_overview(
    district: str = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_officer),
):
    farmer_query = db.query(Farmer)
    farm_query = db.query(Farm)

    if district:
        farmer_query = farmer_query.filter(Farmer.district == district)
        farm_query = farm_query.filter(Farm.district == district)

    total_farmers = farmer_query.count()
    total_farms = farm_query.count()
    total_area = db.query(func.sum(Farm.area_acres)).scalar() or 0

    active_crops = db.query(CropRecord).filter(
        CropRecord.status.in_([CropStatus.GROWING, CropStatus.SOWING])
    ).count()

    recent_alerts = db.query(DiseaseDetection).filter(
        DiseaseDetection.severity.in_(["high", "critical"])
    ).order_by(desc(DiseaseDetection.created_at)).limit(5).all()

    return {
        "total_farmers": total_farmers,
        "total_farms": total_farms,
        "total_area_acres": round(float(total_area), 1),
        "active_crops": active_crops,
        "recent_disease_alerts": [
            {
                "farm_id": str(a.farm_id),
                "disease": a.detected_disease,
                "severity": a.severity,
                "date": a.created_at.isoformat(),
            }
            for a in recent_alerts
        ],
    }


@router.get("/district-heatmap")
def get_district_heatmap(db: Session = Depends(get_db), user: User = Depends(require_officer)):
    results = (
        db.query(Farm.district, func.count(Farm.id).label("farm_count"), func.sum(Farm.area_acres).label("total_acres"))
        .group_by(Farm.district)
        .all()
    )
    return [
        {"district": r.district, "farm_count": r.farm_count, "total_acres": round(float(r.total_acres or 0), 1)}
        for r in results
    ]


@router.get("/pest-spread-risk")
def get_pest_spread_risk(
    district: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_officer),
):
    farms = db.query(Farm).filter(Farm.district == district).all()

    infected_detections = (
        db.query(DiseaseDetection.farm_id)
        .filter(DiseaseDetection.severity.in_(["high", "critical"]))
        .distinct()
        .all()
    )
    infected_ids = [str(d.farm_id) for d in infected_detections]

    farm_dicts = [
        {"id": str(f.id), "latitude": f.latitude, "longitude": f.longitude, "crop": None}
        for f in farms
    ]

    risk_graph = build_risk_graph(farm_dicts, infected_ids)
    return {"district": district, "risk_assessments": risk_graph}


@router.get("/farmers")
def list_farmers(
    district: str = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_officer),
):
    query = db.query(Farmer)

    if district:
        query = query.filter(Farmer.district == district)

    farmers = query.all()
    results = []
    
    for farmer in farmers:
        farms = db.query(Farm).filter(Farm.farmer_id == farmer.id).all()
        farm_ids = [f.id for f in farms]

        total_area = sum(float(f.area_acres or 0) for f in farms)
    
        crops = []
        if farm_ids:
            crops = (
                db.query(CropRecord.crop_name)
                .filter(CropRecord.farm_id.in_(farm_ids))
                .filter(CropRecord.crop_name.isnot(None))
                .distinct()
                .all()
            )

        has_alert = False
        if farm_ids:
            has_alert = (
                db.query(DiseaseDetection)
                .filter(
                    DiseaseDetection.farm_id.in_(farm_ids),
                    DiseaseDetection.severity.in_(["high", "critical"]),
                    DiseaseDetection.detected_disease != "Healthy",
                )
                .first()
                is not None
            )

        results.append({
            "id": str(farmer.id),
            "name": farmer.name or "Unnamed Farmer",
            "district": farmer.district or "N/A",
            "state": farmer.state or "N/A",
            "farms": len(farms),
            "area": round(total_area, 1),
            "crop": ", ".join([c[0] for c in crops if c[0]]) if crops else "—",
            "status": "alert" if has_alert else "good",
            
        })

    return results


@router.get("/farms-map")
def get_farms_map(
    district: str = Query("Coimbatore"),
    db: Session = Depends(get_db),
    user: User = Depends(require_officer),
):
    farms = db.query(Farm).filter(Farm.district == district).all()
    markers = []

    for farm in farms:
        latest_disease = (
            db.query(DiseaseDetection)
            .filter(DiseaseDetection.farm_id == farm.id)
            .order_by(desc(DiseaseDetection.created_at))
            .first()
        )
        crop = (
            db.query(CropRecord)
            .filter(CropRecord.farm_id == farm.id)
            .order_by(desc(CropRecord.created_at))
            .first()
        )

        healthy = not latest_disease or latest_disease.detected_disease == "Healthy"
        markers.append({
            "id": str(farm.id),
            "lat": farm.latitude,
            "lon": farm.longitude,
            "name": farm.name,
            "district": farm.district,
            "crop": crop.crop_name if crop else "Unknown",
            "healthy": healthy,
            "disease": None if healthy else latest_disease.detected_disease,
            "severity": latest_disease.severity if latest_disease else None,
            "farmer_id": str(farm.farmer_id),
        })

    return {"district": district, "farms": markers}


@router.get("/crop-distribution")
def get_crop_distribution(db: Session = Depends(get_db), user: User = Depends(require_officer)):
    rows = (
        db.query(CropRecord.crop_name, func.count(CropRecord.id).label("count"))
        .group_by(CropRecord.crop_name)
        .all()
    )
    total = sum(r.count for r in rows) or 1
    return [{"name": r.crop_name, "value": round(r.count / total * 100, 1)} for r in rows]


@router.get("/yield-trends")
def get_yield_trends(db: Session = Depends(get_db), user: User = Depends(require_officer)):
    """Monthly yield trends by crop from crop records (dynamic dashboard chart)."""
    crops = db.query(CropRecord).filter(CropRecord.actual_yield_kg.isnot(None)).all()
    if not crops:
        crops = db.query(CropRecord).all()

    by_crop: Dict[str, list] = {}
    for c in crops:
        try:
            month = c.sowing_date.strftime("%b") if c.sowing_date else "Current"
            area = float(c.area_acres or 1)
            yield_kg = float(c.actual_yield_kg or c.expected_yield_kg or area * 2000)
            yield_per_acre = yield_kg / max(area, 0.1)
            by_crop.setdefault(c.crop_name or "Crop", []).append({"month": month, "yield": round(yield_per_acre, 0)})
        except (TypeError, ValueError):
            continue

    crop_names = list(by_crop.keys())[:3]
    if not crop_names:
        return []

    months = sorted({p["month"] for pts in by_crop.values() for p in pts})
    result = []
    for m in months:
        row = {"month": m}
        for name in crop_names:
            pts = by_crop.get(name, [])
            match = next((p for p in pts if p["month"] == m), None)
            row[name.lower().replace(" ", "_")] = match["yield"] if match else 0
        result.append(row)
    return result[:12]


@router.get("/districts")
def list_districts(db: Session = Depends(get_db), user: User = Depends(require_officer)):
    farm_rows = db.query(Farm.district).distinct().all()
    farmer_rows = db.query(Farmer.district).distinct().all()

    districts = set()

    for r in farm_rows:
        if r[0]:
            districts.add(r[0])

    for r in farmer_rows:
        if r[0]:
            districts.add(r[0])

    return sorted(list(districts))


@router.get("/water-usage")
def get_water_usage(db: Session = Depends(get_db), user: User = Depends(require_officer)):
    farms_with_sensors = db.query(Farm).filter(Farm.has_iot_sensor == True).all()
    results = []
    for farm in farms_with_sensors:
        latest = (
            db.query(SensorReading)
            .filter(SensorReading.farm_id == farm.id)
            .order_by(SensorReading.recorded_at.desc())
            .first()
        )
        if latest:
            results.append({
                "farm_id": str(farm.id),
                "farm_name": farm.name,
                "district": farm.district,
                "soil_moisture": latest.soil_moisture_percent,
                "irrigation_needed": (latest.soil_moisture_percent or 50) < 35,
            })
    by_district: Dict[str, Dict] = {}
    for item in results:
        d = item["district"]
        if d not in by_district:
            by_district[d] = {"district": d, "farms": 0, "irrigating": 0}
        by_district[d]["farms"] += 1
        if item["irrigation_needed"]:
            by_district[d]["irrigating"] += 1
    return list(by_district.values())
