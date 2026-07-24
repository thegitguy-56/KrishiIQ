from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine, SessionLocal
from app.config import settings
from app.api import (
    auth,
    farms,
    sensors,
    disease,
    advisory,
    weather,
    dashboard,
    ai,
    farmers,
    crops,
    history,
)


def _auto_seed():
    """Seed the database only if it is empty (no users exist yet)."""
    from app.models.user import User, UserRole
    from app.models.farmer import Farmer
    from app.models.farm import Farm
    from app.models.crop import CropRecord, Season, CropStatus
    from app.models.sensor_reading import SensorReading
    from app.models.disease_detection import DiseaseDetection
    from app.models.advisory import Advisory, AdvisoryType
    from app.services.auth_service import hash_password
    import uuid
    from datetime import datetime, date, timedelta

    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            print("Database already seeded — skipping.")
            return

        print("Empty database detected — seeding test accounts...")

        officer_user = User(id=str(uuid.uuid4()), phone="9000000001", email="officer@krishiiq.com",
                            hashed_password=hash_password("officer123"), role=UserRole.OFFICER, preferred_language="en")
        farmer_user = User(id=str(uuid.uuid4()), phone="9000000002", email="farmer@krishiiq.com",
                           hashed_password=hash_password("farmer123"), role=UserRole.FARMER, preferred_language="ta")
        admin_user = User(id=str(uuid.uuid4()), phone="9000000003", email="admin@krishiiq.com",
                          hashed_password=hash_password("admin123"), role=UserRole.ADMIN, preferred_language="en")

        db.add_all([officer_user, farmer_user, admin_user])
        db.flush()

        farmer = Farmer(id=str(uuid.uuid4()), user_id=farmer_user.id, name="Murugan Krishnamoorthy",
                        district="Coimbatore", state="Tamil Nadu", soil_health_card_id="TN-CBE-2024-001234",
                        total_land_acres=4.5, profile_data={})
        db.add(farmer)
        db.flush()

        farm1 = Farm(id=str(uuid.uuid4()), farmer_id=farmer.id, name="North Field", area_acres=2.5,
                     latitude=11.0168, longitude=76.9558, soil_type="black_cotton",
                     irrigation_source="Borewell", has_iot_sensor=True, sensor_device_id="DEV-001",
                     district="Coimbatore", village="Perur")
        farm2 = Farm(id=str(uuid.uuid4()), farmer_id=farmer.id, name="South Field", area_acres=2.0,
                     latitude=11.0050, longitude=76.9620, soil_type="loam",
                     irrigation_source="Canal", has_iot_sensor=False,
                     district="Coimbatore", village="Perur")
        db.add_all([farm1, farm2])
        db.flush()

        crop1 = CropRecord(id=str(uuid.uuid4()), farm_id=farm1.id, crop_name="Rice",
                           crop_variety="ADT 43", season=Season.KHARIF, status=CropStatus.GROWING,
                           sowing_date=date.today() - timedelta(days=45),
                           expected_harvest_date=date.today() + timedelta(days=75),
                           area_acres=2.5, expected_yield_kg=11250)
        db.add(crop1)
        db.flush()

        now = datetime.utcnow()
        for i in range(24):
            db.add(SensorReading(farm_id=farm1.id, device_id="DEV-001",
                                 soil_moisture_percent=55 - i * 0.8, soil_temperature_celsius=28 + (i % 5) * 0.3,
                                 soil_ph=6.8, nitrogen_ppm=45 + (i % 3) * 5,
                                 phosphorus_ppm=28, potassium_ppm=55,
                                 air_temperature_celsius=32, air_humidity_percent=65,
                                 recorded_at=now - timedelta(hours=i)))

        db.add(DiseaseDetection(farm_id=farm1.id, image_url="https://example.com/demo/brown_spot.jpg",
                                detected_disease="Brown_Spot", confidence_score=0.87, severity="medium",
                                affected_area_percent=25.4,
                                treatment_recommendation="Apply Mancozeb or Tricyclazole fungicide.",
                                raw_predictions={"Brown_Spot": 0.87, "Healthy": 0.08}, is_pest_anomaly="false",
                                created_at=now - timedelta(days=2)))

        db.add(Advisory(farmer_id=farmer.id, crop_record_id=crop1.id,
                        advisory_type=AdvisoryType.IRRIGATION,
                        title_en="Irrigation needed for North Field",
                        title_hi="नॉर्थ फील्ड के लिए सिंचाई आवश्यक",
                        title_ta="நார்த் வயலுக்கு நீர்பாசனம் தேவை",
                        body_en="Soil moisture is at 31%. No rainfall expected. Irrigate within 24 hours.",
                        body_hi="मिट्टी की नमी 31% है। 24 घंटों के भीतर सिंचाई करें।",
                        body_ta="மண் ஈரப்பதம் 31%. 24 மணி நேரத்திற்குள் பாசனம் செய்யவும்.",
                        priority="high", is_read="false", created_at=now - timedelta(hours=3)))

        db.commit()
        print("✅ Seed complete! Officer: 9000000001/officer123 | Farmer: 9000000002/farmer123 | Admin: 9000000003/admin123")

    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    _auto_seed()
    yield
    # Shutdown (nothing needed)


app = FastAPI(
    title="KrishiIQ API",
    description="AI-powered agricultural advisory system for Indian farmers",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — origins read from env var so GitHub Pages URL can be added without code changes
_cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(farms.router, prefix="/api/v1")
app.include_router(sensors.router, prefix="/api/v1")
app.include_router(disease.router, prefix="/api/v1")
app.include_router(advisory.router, prefix="/api/v1")
app.include_router(weather.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(farmers.router, prefix="/api/v1")
app.include_router(crops.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")

uploads_dir = Path(__file__).resolve().parents[1] / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)

app.mount(
    "/uploads",
    StaticFiles(directory=str(uploads_dir)),
    name="uploads",
)

@app.get("/")
def root():
    return {"message": "KrishiIQ API Running"}

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "KrishiIQ API",
        "version": "1.0.0",
    }