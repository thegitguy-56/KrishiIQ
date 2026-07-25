"""
Static inventory of the KrishiIQ backend, compiled by reading
backend/app/**/*.py in the thegitguy-56/KrishiIQ repository.

Kept separate from generate_reports.py so it's easy to update this file
by hand as the backend evolves (new routers, new endpoints) without
touching the report-generation logic.
"""

BACKEND_STACK = {
    "framework": "FastAPI 0.111.0",
    "orm": "SQLAlchemy 2.0.31",
    "migrations": "Alembic 1.13.2",
    "database_driver": "psycopg2-binary 2.9.9 (PostgreSQL / Neon Tech in production, SQLite for local/CI)",
    "auth": "python-jose (JWT, HS256) + passlib/bcrypt for password hashing",
    "cache": "redis 5.0.7 (optional — app degrades gracefully if unavailable)",
    "ml": "torch, torchvision, timm, torch-geometric (disease detection + GNN pest-spread model)",
    "background": "celery 5.4.0 (declared as a dependency; no worker/task wiring observed in the routers reviewed)",
    "storage": "aiofiles (local disk /uploads) + boto3 declared for future S3 use",
}

# (module_path, purpose)
MODULE_INVENTORY = [
    ("backend/app/main.py", "FastAPI app factory, CORS config, router registration, DB auto-seed on empty database"),
    ("backend/app/config.py", "pydantic-settings Settings — env-driven configuration incl. SECRET_KEY, DB URL, API keys"),
    ("backend/app/database.py", "SQLAlchemy engine/session factory + optional Redis client"),
    ("backend/app/api/deps.py", "Auth dependencies: get_current_user, require_farmer, require_officer, require_admin"),
    ("backend/app/api/auth.py", "Registration, login, refresh-token endpoints"),
    ("backend/app/api/farms.py", "Farm CRUD, scoped to the authenticated farmer"),
    ("backend/app/api/farmers.py", "Farmer profile read/update"),
    ("backend/app/api/crops.py", "Crop record CRUD"),
    ("backend/app/api/disease.py", "Image upload + ML disease detection, per-farm disease history, district alerts"),
    ("backend/app/api/dashboard.py", "Officer-facing aggregated analytics (9 endpoints)"),
    ("backend/app/api/advisory.py", "Personalized irrigation/fertilizer/pest advisory generation"),
    ("backend/app/api/ai.py", "AI chat assistant (Groq-backed) + public AI config"),
    ("backend/app/api/sensors.py", "IoT sensor ingestion (unauthenticated) + per-farm sensor reads"),
    ("backend/app/api/weather.py", "Weather forecast proxy"),
    ("backend/app/api/history.py", "Farmer-facing historical summaries (crops/sensors/diseases/water/carbon)"),
    ("backend/app/api/create_admin_officer.py", "Standalone script (not a router) to seed/repair the officer & admin accounts"),
    ("backend/app/services/auth_service.py", "Password hashing (bcrypt), JWT encode/decode, user lookups"),
    ("backend/app/services/advisory_service.py", "Business logic generating advisory records from sensor/weather/disease data"),
    ("backend/app/services/openai_service.py", "Groq/OpenAI-compatible LLM integration for chat + treatment enhancement"),
    ("backend/app/services/weather_service.py", "External weather API integration with Redis caching"),
    ("backend/app/services/otp_service.py", "OTP helper (referenced by config.DEV_OTP_CODE)"),
    ("backend/app/ml/disease_detector.py", "EfficientNet-based crop disease image classifier"),
    ("backend/app/ml/gnn_model.py", "Graph neural network for pest/disease spatial spread risk"),
    ("backend/app/ml/yield_predictor.py", "Yield prediction model"),
    ("backend/app/models/*.py", "SQLAlchemy ORM models: User, Farmer, Farm, CropRecord, SensorReading, DiseaseDetection, Advisory"),
    ("backend/app/schemas/*.py", "Pydantic request/response schemas per resource"),
]

# (method, path, auth_dependency, description, request_body_or_params)
ENDPOINT_INVENTORY = [
    ("POST", "/api/v1/auth/register", "None (public)", "Register a new user; role is client-supplied (see BIZ-001 finding)", "RegisterRequest JSON"),
    ("POST", "/api/v1/auth/login", "None (public)", "Login with phone + password, returns JWT pair", "LoginRequest JSON"),
    ("POST", "/api/v1/auth/refresh", "None (public, refresh token itself is the credential)", "Exchange a refresh token for a new access/refresh pair", "refresh_token query param"),
    ("GET", "/api/v1/farms/", "require_farmer", "List the caller's own farms", "-"),
    ("POST", "/api/v1/farms/", "require_farmer", "Create a farm", "FarmCreate JSON"),
    ("GET", "/api/v1/farms/{farm_id}", "get_current_user + ownership check", "Get one farm (owner-scoped)", "-"),
    ("PATCH", "/api/v1/farms/{farm_id}", "get_current_user + ownership check", "Update a farm (owner-scoped)", "FarmUpdate JSON"),
    ("DELETE", "/api/v1/farms/{farm_id}", "get_current_user + ownership check", "Delete a farm (owner-scoped)", "-"),
    ("GET", "/api/v1/farmers/me", "require_farmer", "Get own farmer profile", "-"),
    ("PATCH", "/api/v1/farmers/me", "require_farmer", "Update own farmer profile", "FarmerUpdate JSON"),
    ("GET", "/api/v1/crops", "require_farmer", "List crop records across own farms", "-"),
    ("POST", "/api/v1/crops", "require_farmer", "Create a crop record", "CropCreate JSON"),
    ("PATCH", "/api/v1/crops/{crop_id}", "require_farmer + ownership check via farm", "Update a crop record", "CropUpdate JSON"),
    ("POST", "/api/v1/disease/detect", "require_farmer", "Upload an image for ML disease detection", "multipart/form-data: farm_id, image"),
    ("GET", "/api/v1/disease/farm/{farm_id}/history", "require_farmer + ownership check", "Disease detection history for one farm", "limit query param"),
    ("GET", "/api/v1/disease/alerts/district/{district}", "get_current_user (any role)", "District-wide disease alerts", "severity query param"),
    ("GET", "/api/v1/dashboard/overview", "require_officer", "Aggregate KPI overview", "district query param"),
    ("GET", "/api/v1/dashboard/district-heatmap", "require_officer", "Farm count/acreage per district", "-"),
    ("GET", "/api/v1/dashboard/pest-spread-risk", "require_officer", "GNN-based pest spread risk graph", "district query param (required)"),
    ("GET", "/api/v1/dashboard/farmers", "require_officer", "List all farmers with derived stats", "district query param"),
    ("GET", "/api/v1/dashboard/farms-map", "require_officer", "Farm map markers with latest disease status", "district query param (default Coimbatore)"),
    ("GET", "/api/v1/dashboard/crop-distribution", "require_officer", "Crop-type distribution percentages", "-"),
    ("GET", "/api/v1/dashboard/yield-trends", "require_officer", "Monthly yield-per-acre trend by crop", "-"),
    ("GET", "/api/v1/dashboard/districts", "require_officer", "Distinct list of districts", "-"),
    ("GET", "/api/v1/dashboard/water-usage", "require_officer", "Irrigation-needed rollup per district", "-"),
    ("GET", "/api/v1/advisory/personalized", "require_farmer", "Generate + fetch personalized advisories", "-"),
    ("PATCH", "/api/v1/advisory/{advisory_id}/read", "get_current_user (no ownership check — see DAST-004)", "Mark an advisory read", "-"),
    ("GET", "/api/v1/ai/config/public", "None (public)", "Public AI feature flags", "-"),
    ("POST", "/api/v1/ai/chat", "require_farmer", "Farmer AI chat assistant", "ChatRequest JSON"),
    ("POST", "/api/v1/sensors/ingest", "None — see DAST-005", "IoT sensor data ingestion", "SensorReadingCreate JSON"),
    ("POST", "/api/v1/sensors/farm/{farm_id}/register-device", "require_farmer + ownership check", "Pair a device with an owned farm", "device_id query param"),
    ("GET", "/api/v1/sensors/farm/{farm_id}/latest", "get_current_user (no ownership check — see DAST-003)", "Latest sensor reading + derived soil status", "-"),
    ("GET", "/api/v1/sensors/farm/{farm_id}/history", "get_current_user (no ownership check — see DAST-003)", "Sensor reading history", "hours query param"),
    ("GET", "/api/v1/weather/forecast", "get_current_user (any role)", "Weather forecast for coordinates", "lat, lon query params (required)"),
    ("GET", "/api/v1/history/summary", "require_farmer", "Aggregated environmental/usage summary", "-"),
    ("GET", "/api/v1/history/crops", "require_farmer", "Crop history across own farms", "-"),
    ("GET", "/api/v1/history/sensors/{farm_id}", "require_farmer (self-scoped by farm membership check)", "Sensor logs, correctly ownership-filtered", "hours query param (1-720)"),
    ("GET", "/api/v1/history/diseases", "require_farmer", "Disease scan history across own farms", "limit query param"),
    ("GET", "/", "None", "Liveness message", "-"),
    ("GET", "/health", "None", "Health check", "-"),
    ("GET", "/uploads/{path}", "None (StaticFiles mount)", "Uploaded crop images", "-"),
]
