"""
Run this once after starting the backend to create test accounts and demo data.
Usage: python seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, Base, engine
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

Base.metadata.create_all(bind=engine)
db = SessionLocal()

print("Seeding database...")

# ── Test accounts ──────────────────────────────────────────────────────────────
officer_user = User(
    id=str(uuid.uuid4()),
    phone="9000000001",
    email="officer@krishiiq.com",
    hashed_password=hash_password("officer123"),
    role=UserRole.OFFICER,
    preferred_language="en",
)

farmer_user = User(
    id=str(uuid.uuid4()),
    phone="9000000002",
    email="farmer@krishiiq.com",
    hashed_password=hash_password("farmer123"),
    role=UserRole.FARMER,
    preferred_language="ta",
)

admin_user = User(
    id=str(uuid.uuid4()),
    phone="9000000003",
    email="admin@krishiiq.com",
    hashed_password=hash_password("admin123"),
    role=UserRole.ADMIN,
    preferred_language="en",
)

db.add_all([officer_user, farmer_user, admin_user])
db.flush()

# ── Farmer profile ─────────────────────────────────────────────────────────────
farmer = Farmer(
    id=str(uuid.uuid4()),
    user_id=farmer_user.id,
    name="Murugan Krishnamoorthy",
    district="Coimbatore",
    state="Tamil Nadu",
    soil_health_card_id="TN-CBE-2024-001234",
    total_land_acres=4.5,
)
db.add(farmer)
db.flush()

# ── Farms ──────────────────────────────────────────────────────────────────────
farm1 = Farm(
    id=str(uuid.uuid4()),
    farmer_id=farmer.id,
    name="North Field",
    area_acres=2.5,
    latitude=11.0168,
    longitude=76.9558,
    soil_type="black_cotton",
    irrigation_source="Borewell",
    has_iot_sensor=True,
    sensor_device_id="DEV-001",
    district="Coimbatore",
    village="Perur",
)

farm2 = Farm(
    id=str(uuid.uuid4()),
    farmer_id=farmer.id,
    name="South Field",
    area_acres=2.0,
    latitude=11.0050,
    longitude=76.9620,
    soil_type="loam",
    irrigation_source="Canal",
    has_iot_sensor=False,
    district="Coimbatore",
    village="Perur",
)
db.add_all([farm1, farm2])
db.flush()

# ── Crop records ───────────────────────────────────────────────────────────────
crop1 = CropRecord(
    id=str(uuid.uuid4()),
    farm_id=farm1.id,
    crop_name="Rice",
    crop_variety="ADT 43",
    season=Season.KHARIF,
    status=CropStatus.GROWING,
    sowing_date=date.today() - timedelta(days=45),
    expected_harvest_date=date.today() + timedelta(days=75),
    area_acres=2.5,
    expected_yield_kg=11250,
)
db.add(crop1)
db.flush()

# ── Sensor readings ────────────────────────────────────────────────────────────
now = datetime.utcnow()
for i in range(24):
    db.add(SensorReading(
        farm_id=farm1.id,
        device_id="DEV-001",
        soil_moisture_percent=55 - i * 0.8,
        soil_temperature_celsius=28 + (i % 5) * 0.3,
        soil_ph=6.8,
        nitrogen_ppm=45 + (i % 3) * 5,
        phosphorus_ppm=28,
        potassium_ppm=55,
        air_temperature_celsius=32,
        air_humidity_percent=65,
        recorded_at=now - timedelta(hours=i),
    ))

# ── Disease detection records ──────────────────────────────────────────────────
db.add(DiseaseDetection(
    farm_id=farm1.id,
    image_url="https://example.com/demo/brown_spot.jpg",
    detected_disease="Brown_Spot",
    confidence_score=0.87,
    severity="medium",
    affected_area_percent=25.4,
    treatment_recommendation="Apply Mancozeb or Tricyclazole fungicide. Improve potassium nutrition.",
    raw_predictions={"Brown_Spot": 0.87, "Healthy": 0.08, "Bacterial_Blight": 0.05},
    is_pest_anomaly="false",
    created_at=now - timedelta(days=2),
))

db.add(DiseaseDetection(
    farm_id=farm2.id,
    image_url="https://example.com/demo/leaf_blast.jpg",
    detected_disease="Leaf_Blast",
    confidence_score=0.93,
    severity="high",
    affected_area_percent=41.2,
    treatment_recommendation="Apply Tricyclazole 75 WP at 0.6g/litre. Drain water from field temporarily.",
    raw_predictions={"Leaf_Blast": 0.93, "Neck_Blast": 0.05, "Healthy": 0.02},
    is_pest_anomaly="false",
    created_at=now - timedelta(days=1),
))

# ── Advisories ─────────────────────────────────────────────────────────────────
db.add(Advisory(
    farmer_id=farmer.id,
    crop_record_id=crop1.id,
    advisory_type=AdvisoryType.IRRIGATION,
    title_en="Irrigation needed for North Field",
    title_hi="नॉर्थ फील्ड के लिए सिंचाई आवश्यक",
    title_ta="நார்த் வயலுக்கு நீர்பாசனம் தேவை",
    body_en="Soil moisture is at 31% (below 35% threshold). No rainfall expected in next 12 hours. Irrigate 2–3 inches within 24 hours.",
    body_hi="मिट्टी की नमी 31% है। अगले 12 घंटों में बारिश नहीं। 24 घंटों के भीतर सिंचाई करें।",
    body_ta="மண் ஈரப்பதம் 31% உள்ளது. 24 மணி நேரத்திற்குள் பாசனம் செய்யவும்.",
    priority="high",
    is_read="false",
    created_at=now - timedelta(hours=3),
))

db.add(Advisory(
    farmer_id=farmer.id,
    advisory_type=AdvisoryType.FERTILIZER,
    title_en="Low Nitrogen detected in soil",
    title_hi="मिट्टी में कम नाइट्रोजन पाया गया",
    title_ta="மண்ணில் குறைந்த நைட்ரஜன் கண்டறியப்பட்டது",
    body_en="Soil nitrogen is at 45 ppm (low). Apply urea at 25 kg/acre or use organic compost. Best applied during morning hours.",
    body_hi="नाइट्रोजन 45 ppm है। प्रति एकड़ 25 किग्रा यूरिया डालें।",
    body_ta="நைட்ரஜன் 45 ppm உள்ளது. ஏக்கருக்கு 25 கிலோ யூரியா இடவும்.",
    priority="normal",
    is_read="false",
    created_at=now - timedelta(hours=6),
))

db.add(Advisory(
    farmer_id=farmer.id,
    advisory_type=AdvisoryType.PEST_CONTROL,
    title_en="Brown Spot disease detected — take action",
    title_hi="ब्राउन स्पॉट रोग मिला — उपाय करें",
    title_ta="பிரவுன் ஸ்பாட் நோய் கண்டறியப்பட்டது",
    body_en="Brown Spot detected on North Field with 87% confidence. Severity: Medium. Apply Mancozeb 75 WP at 2g/litre. Spray in early morning.",
    body_hi="87% विश्वास के साथ ब्राउन स्पॉट मिला। Mancozeb 75 WP 2g/लीटर छिड़कें।",
    body_ta="87% நம்பகத்தன்மையுடன் பிரவுன் ஸ்பாட் கண்டறியப்பட்டது. Mancozeb 75 WP 2g/லிட்டர் தெளிக்கவும்.",
    priority="high",
    is_read="false",
    created_at=now - timedelta(hours=2),
))

db.add(Advisory(
    farmer_id=farmer.id,
    advisory_type=AdvisoryType.WEATHER_ALERT,
    title_en="Heavy rain expected in 48 hours",
    title_hi="48 घंटों में भारी बारिश की संभावना",
    title_ta="48 மணி நேரத்தில் கனமழை எதிர்பார்க்கப்படுகிறது",
    body_en="Weather forecast shows 35mm rainfall expected in next 48 hours. Avoid applying fertilizers or pesticides today. Ensure proper field drainage.",
    body_hi="अगले 48 घंटों में 35mm बारिश। उर्वरक न डालें, जल निकासी सुनिश्चित करें।",
    body_ta="48 மணி நேரத்தில் 35mm மழை எதிர்பார்க்கப்படுகிறது. உரம் இடாதீர்கள்.",
    priority="normal",
    is_read="true",
    created_at=now - timedelta(hours=12),
))

db.commit()
db.close()

print("\nSeed complete! Test accounts created:\n")
print("  Officer login -> phone: 9000000001  password: officer123")
print("  Farmer login  -> phone: 9000000002  password: farmer123")
print("  Admin login   -> phone: 9000000003  password: admin123")
print("\nOpen the dashboard and login with any of the above credentials.")
