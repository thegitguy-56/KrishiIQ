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
    import random

    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            print("Database already seeded — skipping.")
            return

        print("Empty database detected — seeding rich demo data...")

        # ── Users ──────────────────────────────────────────────────────────
        officer = User(id=str(uuid.uuid4()), phone="9000000001", email="officer@krishiiq.com",
                       hashed_password=hash_password("officer123"), role=UserRole.OFFICER, preferred_language="en")
        admin = User(id=str(uuid.uuid4()), phone="9000000003", email="admin@krishiiq.com",
                     hashed_password=hash_password("admin123"), role=UserRole.ADMIN, preferred_language="en")
        db.add_all([officer, admin])
        db.flush()

        # ── Farmer accounts + profiles across 5 Tamil Nadu districts ───────
        FARMERS_DATA = [
            ("9000000002", "farmer1@krishiiq.com", "farmer123", "Murugan Krishnamoorthy", "Coimbatore", "ta", 4.5),
            ("9100000001", "farmer2@krishiiq.com", "farmer123", "Selvi Ramasamy",          "Salem",      "ta", 3.2),
            ("9100000002", "farmer3@krishiiq.com", "farmer123", "Rajan Natarajan",          "Madurai",    "hi", 6.0),
            ("9100000003", "farmer4@krishiiq.com", "farmer123", "Kavitha Sundaram",         "Coimbatore", "en", 2.8),
            ("9100000004", "farmer5@krishiiq.com", "farmer123", "Anbu Velusamy",            "Trichy",     "ta", 5.5),
            ("9100000005", "farmer6@krishiiq.com", "farmer123", "Priya Manoharan",          "Salem",      "en", 1.9),
            ("9100000006", "farmer7@krishiiq.com", "farmer123", "Gopal Subramaniam",        "Madurai",    "ta", 7.0),
            ("9100000007", "farmer8@krishiiq.com", "farmer123", "Lakshmi Perumal",          "Trichy",     "ta", 3.5),
        ]

        farmer_users, farmer_objs = [], []
        for phone, email, pwd, name, district, lang, acres in FARMERS_DATA:
            u = User(id=str(uuid.uuid4()), phone=phone, email=email,
                     hashed_password=hash_password(pwd), role=UserRole.FARMER, preferred_language=lang)
            db.add(u)
            db.flush()
            f = Farmer(id=str(uuid.uuid4()), user_id=u.id, name=name, district=district,
                       state="Tamil Nadu", total_land_acres=acres, profile_data={})
            db.add(f)
            db.flush()
            farmer_users.append(u)
            farmer_objs.append(f)

        # ── Farms — coordinates spread across Tamil Nadu ──────────────────
        FARMS_DATA = [
            # (farmer_idx, name, acres, lat, lon, soil, irrigation, district, village, has_sensor)
            (0, "North Field",        2.5,  11.0168, 76.9558, "black_cotton", "Borewell",   "Coimbatore", "Perur",      True),
            (0, "South Field",        2.0,  11.0050, 76.9620, "loam",         "Canal",      "Coimbatore", "Perur",      False),
            (1, "Selvi Farm A",       1.8,  11.6630, 78.1460, "red_loam",     "Borewell",   "Salem",      "Attur",      True),
            (1, "Selvi Farm B",       1.4,  11.6700, 78.1520, "sandy_loam",   "Rainfed",    "Salem",      "Attur",      False),
            (2, "Rajan East Plot",    3.2,   9.9252, 78.1198, "alluvial",     "Canal",      "Madurai",    "Melur",      True),
            (2, "Rajan West Plot",    2.8,   9.9100, 78.1050, "black_cotton", "Borewell",   "Madurai",    "Melur",      True),
            (3, "Kavitha Garden",     2.8,  11.0400, 76.9700, "loam",         "Drip",       "Coimbatore", "Chettipalayam", True),
            (4, "Anbu Main Farm",     3.0,  10.7900, 78.7000, "clay",         "Canal",      "Trichy",     "Srirangam",  True),
            (4, "Anbu Second Farm",   2.5,  10.8100, 78.7200, "black_cotton", "Borewell",   "Trichy",     "Srirangam",  False),
            (5, "Priya Terrace",      1.9,  11.6450, 78.1560, "sandy_loam",   "Drip",       "Salem",      "Omalur",     True),
            (6, "Gopal Large Field",  4.0,   9.9500, 78.1400, "alluvial",     "Canal",      "Madurai",    "Vadipatti",  True),
            (6, "Gopal River Side",   3.0,   9.9350, 78.1300, "loam",         "River Lift", "Madurai",    "Vadipatti",  True),
            (7, "Lakshmi Farm 1",     2.0,  10.8300, 78.6800, "clay",         "Borewell",   "Trichy",     "Manachanallur", True),
            (7, "Lakshmi Farm 2",     1.5,  10.8450, 78.6950, "red_loam",     "Rainfed",    "Trichy",     "Manachanallur", False),
        ]

        farm_objs = []
        for fi, name, acres, lat, lon, soil, irr, dist, village, sensor in FARMS_DATA:
            dev_id = f"DEV-{len(farm_objs)+1:03d}" if sensor else None
            farm = Farm(id=str(uuid.uuid4()), farmer_id=farmer_objs[fi].id,
                        name=name, area_acres=acres, latitude=lat, longitude=lon,
                        soil_type=soil, irrigation_source=irr, district=dist, village=village,
                        has_iot_sensor=sensor, sensor_device_id=dev_id)
            db.add(farm)
            db.flush()
            farm_objs.append(farm)

        # ── Crop records spread across seasons ────────────────────────────
        CROPS_DATA = [
            # (farm_idx, crop_name, variety, season, status, sow_days_ago, harvest_days, area, exp_yield)
            (0,  "Rice",       "ADT 43",        Season.KHARIF, CropStatus.GROWING,    45,  75, 2.5, 11250),
            (1,  "Sugarcane",  "Co 86032",      Season.KHARIF, CropStatus.GROWING,    90, 270, 2.0, 90000),
            (2,  "Groundnut",  "TMV 2",         Season.RABI,   CropStatus.SOWING,     10, 110, 1.8,  3060),
            (3,  "Maize",      "Hybrid DHM 117",Season.RABI,   CropStatus.GROWING,    30,  90, 1.4,  8400),
            (4,  "Rice",       "CO 51",         Season.KHARIF, CropStatus.GROWING,    60,  60, 3.2, 14400),
            (5,  "Cotton",     "MCU 5",         Season.KHARIF, CropStatus.HARVESTING, 150, 10, 2.8, 11200),
            (6,  "Tomato",     "PKM 1",         Season.ZAID,   CropStatus.GROWING,    20,  70, 2.8, 39200),
            (7,  "Rice",       "ADT 36",        Season.KHARIF, CropStatus.GROWING,    50,  70, 3.0, 13500),
            (8,  "Banana",     "Robusta",       Season.KHARIF, CropStatus.GROWING,   120, 180, 2.5, 62500),
            (9,  "Groundnut",  "VRI 2",         Season.RABI,   CropStatus.SOWING,      5, 115, 1.9,  3230),
            (10, "Rice",       "ADT 43",        Season.KHARIF, CropStatus.GROWING,    55,  65, 4.0, 18000),
            (11, "Sugarcane",  "Co 8011",       Season.KHARIF, CropStatus.GROWING,   100, 260, 3.0,135000),
            (12, "Maize",      "COHM 5",        Season.RABI,   CropStatus.GROWING,    25,  95, 2.0, 12000),
            (13, "Onion",      "Aggregatum",    Season.RABI,   CropStatus.SOWING,      8, 100, 1.5,  9000),
        ]

        crop_objs = []
        for fi, crop_name, variety, season, status, sow_ago, harvest_days, area, exp_yield in CROPS_DATA:
            sow_date = date.today() - timedelta(days=sow_ago)
            harvest_date = date.today() + timedelta(days=harvest_days)
            actual_yield = round(exp_yield * random.uniform(0.85, 1.05), 0) if status == CropStatus.HARVESTING else None
            cr = CropRecord(id=str(uuid.uuid4()), farm_id=farm_objs[fi].id,
                            crop_name=crop_name, crop_variety=variety, season=season, status=status,
                            sowing_date=sow_date, expected_harvest_date=harvest_date,
                            area_acres=area, expected_yield_kg=exp_yield, actual_yield_kg=actual_yield)
            db.add(cr)
            db.flush()
            crop_objs.append(cr)

        # ── Sensor readings for sensor-equipped farms ─────────────────────
        now = datetime.utcnow()
        sensor_farm_idxs = [i for i, (_, _, _, _, _, _, _, _, _, has_s) in enumerate(FARMS_DATA) if has_s]
        for fi in sensor_farm_idxs:
            farm = farm_objs[fi]
            base_moisture = random.uniform(30, 65)
            for i in range(48):  # 48 hours of hourly readings
                db.add(SensorReading(
                    farm_id=farm.id,
                    device_id=farm.sensor_device_id,
                    soil_moisture_percent=round(max(15, base_moisture - i * 0.4 + random.uniform(-2, 2)), 1),
                    soil_temperature_celsius=round(28 + (i % 6) * 0.3 + random.uniform(-1, 1), 1),
                    soil_ph=round(random.uniform(6.2, 7.2), 1),
                    nitrogen_ppm=round(random.uniform(35, 65), 1),
                    phosphorus_ppm=round(random.uniform(20, 40), 1),
                    potassium_ppm=round(random.uniform(45, 75), 1),
                    air_temperature_celsius=round(32 + random.uniform(-3, 5), 1),
                    air_humidity_percent=round(random.uniform(50, 80), 1),
                    recorded_at=now - timedelta(hours=i),
                ))

        # ── Disease detections — mix of severities for alerts + map ───────
        DISEASES = [
            # (farm_idx, disease, confidence, severity, area_pct, days_ago)
            (0,  "Brown_Spot",       0.87, "medium",   25.4, 2),
            (1,  "Healthy",          0.92, "low",        0.0, 1),
            (4,  "Leaf_Blast",       0.91, "high",      42.0, 1),
            (5,  "Bacterial_Blight", 0.88, "high",      38.5, 3),
            (6,  "Tomato Leaf Curl", 0.85, "medium",    20.0, 4),
            (7,  "Brown_Spot",       0.79, "medium",    18.0, 2),
            (10, "Neck_Blast",       0.95, "critical",  60.0, 1),
            (11, "Healthy",          0.96, "low",        0.0, 1),
            (12, "Rust",             0.83, "high",      35.0, 5),
        ]

        TREATMENTS = {
            "Brown_Spot":       "Apply Mancozeb or Tricyclazole fungicide. Improve potassium nutrition.",
            "Healthy":          "No treatment needed. Crop appears healthy.",
            "Leaf_Blast":       "Apply Tricyclazole or Isoprothiolane. Avoid excess nitrogen.",
            "Bacterial_Blight": "Apply copper-based bactericide. Remove infected leaves.",
            "Tomato Leaf Curl": "Control whitefly vector. Apply imidacloprid. Remove infected plants.",
            "Neck_Blast":       "Apply Tricyclazole immediately. Reduce nitrogen. Drain fields.",
            "Rust":             "Apply Propiconazole or Mancozeb. Remove severely infected leaves.",
        }

        for fi, disease, conf, severity, area_pct, days_ago in DISEASES:
            farm = farm_objs[fi]
            treat = TREATMENTS.get(disease, "Consult an agriculture expert.")
            db.add(DiseaseDetection(
                farm_id=farm.id,
                image_url=f"https://example.com/demo/{disease.lower()}.jpg",
                detected_disease=disease,
                confidence_score=conf,
                severity=severity,
                affected_area_percent=area_pct,
                treatment_recommendation=treat,
                raw_predictions={disease: conf, "Healthy": round(1 - conf, 2)},
                is_pest_anomaly="false",
                created_at=now - timedelta(days=days_ago),
            ))

        # ── Advisories for farmers ────────────────────────────────────────
        ADVISORIES = [
            (0, 0, AdvisoryType.IRRIGATION,
             "Irrigation needed — North Field",
             "मिट्टी की नमी 28% है। 12 घंटे में सिंचाई करें।",
             "மண் ஈரப்பதம் 28%. 12 மணி நேரத்திற்குள் பாசனம்.",
             "Soil moisture has dropped to 28% in North Field. Irrigate within 12 hours to avoid crop stress.",
             "high"),
            (2, 4, AdvisoryType.DISEASE,
             "Leaf Blast Alert — Rajan East Plot",
             "पत्ती विस्फोट की चेतावनी। ट्राइसाइक्लाजोल लगाएं।",
             "இலை வெடிப்பு எச்சரிக்கை. ட்ரைசைக்லஜோல் பயன்படுத்தவும்.",
             "Leaf Blast detected at 91% confidence. Apply Tricyclazole immediately. Avoid excess nitrogen.",
             "critical"),
            (4, 7, AdvisoryType.FERTILIZER,
             "Potassium top-dressing due — Anbu Main Farm",
             "पोटेशियम की कमी। MOP 20 kg/एकड़ डालें।",
             "பொட்டாசியம் குறைபாடு. MOP 20 கிலோ/ஏக்கர் தூவுங்கள்.",
             "Sensor shows potassium at 42 ppm (below optimal 50 ppm). Apply MOP @ 20 kg/acre.",
             "medium"),
            (6, 10, AdvisoryType.DISEASE,
             "Neck Blast Critical — Gopal Large Field",
             "नेक ब्लास्ट गंभीर स्तर पर। तुरंत उपचार करें।",
             "நெக் வெடிப்பு மிக கடுமையானது. உடனே சிகிச்சை.",
             "Critical Neck Blast (95% confidence, 60% area affected). Drain field immediately and apply Tricyclazole.",
             "critical"),
        ]

        for fi, ci, atype, title_en, title_hi, title_ta, body_en, priority in ADVISORIES:
            db.add(Advisory(
                farmer_id=farmer_objs[fi].id,
                crop_record_id=crop_objs[ci].id,
                advisory_type=atype,
                title_en=title_en, title_hi=title_hi, title_ta=title_ta,
                body_en=body_en,
                body_hi=title_hi,
                body_ta=title_ta,
                priority=priority,
                is_read="false",
                created_at=now - timedelta(hours=random.randint(1, 24)),
            ))

        db.commit()
        print("✅ Rich seed complete!")
        print("   Officer: 9000000001 / officer123")
        print("   Farmer:  9000000002 / farmer123  (+ 7 more farmers)")
        print("   Admin:   9000000003 / admin123")

    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        raise
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