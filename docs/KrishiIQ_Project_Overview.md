# 🌾 KrishiIQ — Complete Project Overview & Run Guide

> **AI-Powered Agricultural Advisory System** for Indian farmers.  
> Built by your friend. You're here to understand it and fix bugs.

---

## 📐 What Is This Project?

KrishiIQ is a **3-part full-stack smart farming platform** that helps Indian farmers make better decisions about their crops using IoT sensors, weather data, machine learning, and LLMs (Large Language Models like GPT-4o-mini).

The name is a play on "Krishi" (Hindi/Tamil for *agriculture*) + "IQ" (intelligence).

### Who Uses It?

| User Type | Interface | What They Do |
|---|---|---|
| 🧑‍🌾 **Farmer** | Flutter Mobile App | Gets AI advisories, detects crop diseases, chats with AI |
| 👨‍💼 **Agricultural Officer** | React Web Dashboard | Monitors all farms in their district |
| 🛡️ **Admin** | React Web Dashboard | Manages users, farms, system config |

---

## 🗂️ Project Structure

```
KrishilQ/
├── backend/           ← Python FastAPI (the brain / API server)
├── web-dashboard/     ← React + Vite (officer/admin web portal)
├── mobile/            ← Flutter (farmer mobile app)
├── docs/              ← App flow PDF document
├── scripts/           ← Helper scripts (Flutter setup)
├── docker-compose.yml ← Docker setup (optional)
├── start-dev.ps1      ← ONE-CLICK script to start backend + web
└── PRODUCTION.md      ← Production deployment notes
```

---

## 🧠 Part 1 — Backend (FastAPI + AI/ML)

**Location:** `backend/`  
**Language:** Python 3.x  
**Framework:** FastAPI  
**Database:** SQLite (dev) / PostgreSQL (prod)

### What it does:
The backend is the **brain of the whole system**. It:
- Serves a REST API consumed by both the web dashboard and the mobile app
- Runs an advisory engine that reads sensor data and auto-generates farming advice
- Runs ML inference for crop disease detection (EfficientNet deep learning model)
- Connects to OpenAI GPT-4o-mini for AI chat and multilingual advice
- Fetches weather data from OpenWeatherMap
- Optionally uses Redis for caching and Celery for background tasks

### Key Files & Folders:

| Path | Purpose |
|---|---|
| `app/main.py` | FastAPI app entry point, all routers registered here |
| `app/config.py` | All settings loaded from `.env` via Pydantic |
| `app/database.py` | SQLAlchemy engine setup + Redis connection |
| `app/api/` | All API route handlers (auth, farms, sensors, disease, advisory, AI chat, etc.) |
| `app/services/` | Business logic (advisory engine, OpenAI chat, weather, OTP auth) |
| `app/ml/` | ML model code (disease detector, yield predictor, GNN model) |
| `app/models/` | SQLAlchemy database table definitions |
| `app/schemas/` | Pydantic request/response schemas |
| `alembic/` | Database migrations |
| `seed.py` | Creates test accounts and demo data |
| `reset.py` | Wipes the database |
| `.env` | **Active environment variables (API keys, DB URL, etc.)** |

### API Routes (all prefixed `/api/v1`):

| Router | Handles |
|---|---|
| `/auth` | Register, login (OTP-based + password), JWT tokens |
| `/farms` | CRUD for farm records |
| `/sensors` | Sensor reading ingestion and retrieval |
| `/disease` | Upload crop photo → disease detection via EfficientNet |
| `/advisory` | Get/generate farming advisories |
| `/weather` | Weather forecast fetch |
| `/dashboard` | Aggregated stats for the web dashboard |
| `/ai` | AI chat with GPT-4o-mini |
| `/farmers` | Farmer profiles |
| `/crops` | Crop records management |
| `/history` | Disease and advisory history |

### ML Models (in `app/ml/`):
- **`disease_detector.py`** — EfficientNet model that classifies 16 crop disease types from images
- **`yield_predictor.py`** — Predicts yield based on soil/weather features
- **`gnn_model.py`** — Graph Neural Network for cross-field disease spread analysis

> ⚠️ **NOTE:** The actual `.pt` model weight files are NOT included in the repo.  
> They're expected at `backend/ml/weights/efficientnet_disease.pt`, etc.  
> Without them, disease detection and yield prediction endpoints will fail gracefully.

### `.env` — Current Active Config:
```
DATABASE_URL=sqlite:///./krishiiq_local.db    ← Local SQLite (fine for dev)
SECRET_KEY=your-super-secret-key-...         ← Change in prod!
OPENAI_API_KEY=sk-proj-...                   ← Real key present
GOOGLE_MAPS_API_KEY=AIzaSy...                ← Real key present
OPENWEATHER_API_KEY=your_openweather_api_key ← ⚠️ PLACEHOLDER - needs real key
AWS_ACCESS_KEY_ID=your_aws_key               ← ⚠️ PLACEHOLDER - S3 uploads won't work
DEV_OTP_CODE=123456                          ← Dev shortcut - any OTP login uses 123456
```

---

## 🌐 Part 2 — Web Dashboard (React + Vite)

**Location:** `web-dashboard/`  
**Language:** JavaScript (JSX)  
**Framework:** React 18 + Vite  
**Styling:** Tailwind CSS  
**State Management:** Zustand

### What it does:
A web portal **only for officers and admins** (farmers are blocked). Shows a bird's-eye view of all farms in a district.

### Pages:

| Page | Route | What it shows |
|---|---|---|
| `Login.jsx` | `/login` | Phone + password login form |
| `Dashboard.jsx` | `/dashboard` | Stats cards (total farmers, farms, alerts), charts |
| `Farmers.jsx` | `/farmers` | Searchable list of all farmer profiles |
| `FarmMap.jsx` | `/map` | Interactive map with farm pins (Leaflet) |
| `DiseaseAlerts.jsx` | `/disease-alerts` | Feed of all disease detections, filterable by severity |
| `Analytics.jsx` | `/analytics` | Soil health & sensor trend charts |
| `Unauthorized.jsx` | `/unauthorized` | Shown if a farmer tries to access dashboard |

### Key Files:

| Path | Purpose |
|---|---|
| `src/App.jsx` | Router setup + protected routes |
| `src/store/authStore.js` | Zustand auth state (login/logout, user info) |
| `src/services/` | Axios API calls to the backend |
| `src/components/Layout/` | Sidebar + header shell |
| `.env.local` | Frontend env vars (e.g., Google Maps key) |
| `vite.config.js` | Vite config (dev proxy to backend) |

### Dependencies:
- `react-router-dom` — Routing
- `recharts` — Charts and graphs
- `react-leaflet` + `leaflet` — Farm map
- `@react-google-maps/api` — Google Maps alternative
- `zustand` — Auth state
- `axios` — HTTP calls to backend
- `react-hot-toast` — Toast notifications
- `lucide-react` — Icons

---

## 📱 Part 3 — Mobile App (Flutter)

**Location:** `mobile/`  
**Language:** Dart  
**Framework:** Flutter (supports Android, iOS, Web, Windows)  
**State Management:** Riverpod

### What it does:
A farmer-facing mobile app that works **offline** (via Hive local DB). Supports English, Hindi, and Tamil.

### Screens:

| Screen | Purpose |
|---|---|
| `splash_screen.dart` | App loading / auth check |
| `welcome_screen.dart` | Intro screen |
| `language_select_screen.dart` | Choose language (EN/HI/TA) |
| `login_screen.dart` | Phone + password login |
| `register_screen.dart` | New farmer registration |
| `farm_setup_screen.dart` | Set up first farm after registration |
| `home_screen.dart` | Main dashboard — personalized greeting, quick cards |
| `advisory_screen.dart` | AI-generated farming advisories with TTS read-aloud |
| `crop_health_screen.dart` | Take/upload a photo → disease detection |
| `ai_chat_screen.dart` | Full conversational AI chat with GPT |
| `irrigation_screen.dart` | Irrigation scheduling based on sensors + weather |
| `soil_data_screen.dart` | Manual soil data entry |
| `sensors_tab_screen.dart` | Live sensor readings view |
| `farm_map_screen.dart` | Map view of the farmer's own farms |
| `history_screen.dart` | Past advisories and disease detections |
| `profile_screen.dart` | Farmer profile, settings |
| `farm_data_input_screen.dart` | Manual farm data logging |
| `main_shell.dart` | Bottom navigation shell (5 tabs) |

### Key Config:

```dart
// mobile/lib/config/app_config.dart
class AppConfig {
  static const String ngrokUrl = 'https://revise-large-divinely.ngrok-free.dev';
  static String get baseUrl => '$ngrokUrl/api/v1';
  // ⚠️ This ngrok URL is hardcoded — it will EXPIRE
  // For local dev, change baseUrl to: 'http://10.0.2.2:8001/api/v1' (Android emulator)
  //                                or: 'http://localhost:8001/api/v1' (web/desktop)
}
```

### Key Dependencies:
- `flutter_riverpod` — State management
- `go_router` — Navigation
- `dio` — HTTP client
- `hive` + `hive_flutter` — Offline local storage
- `flutter_tts` — Text-to-speech for advisory read-aloud
- `speech_to_text` — Voice input
- `image_picker` — Camera/gallery for disease detection
- `geolocator` — GPS for farm location
- `fl_chart` — Charts
- `google_fonts` — Typography
- `flutter_map` + `latlong2` — Farm map

---

## 🧪 Test Accounts (after running `seed.py`)

| Role | Phone | Password |
|---|---|---|
| 🧑‍💼 Officer | `9000000001` | `officer123` |
| 🧑‍🌾 Farmer | `9000000002` | `farmer123` |
| 🛡️ Admin | `9000000003` | `admin123` |

> Note: In dev mode, **any OTP prompt accepts `123456`** (set in `.env` as `DEV_OTP_CODE`).

---

## 🚀 How to Run Everything

### Prerequisites — Install These First

| Tool | Purpose | Install |
|---|---|---|
| Python 3.10+ | Backend | python.org |
| Node.js 18+ / npm | Web dashboard | nodejs.org |
| Flutter SDK 3.3+ | Mobile app | flutter.dev |
| (Optional) Redis | Caching/sessions | If not running, app still works |

---

### Option A: One-Click (Backend + Web Dashboard only)

From the project root in PowerShell:
```powershell
.\start-dev.ps1
```
This opens two PowerShell windows:
- Backend at **http://127.0.0.1:8001**
- Web dashboard at **http://localhost:5173**

---

### Option B: Manual Step-by-Step

#### Step 1 — Set Up and Run the Backend

```powershell
# Navigate to backend
cd "C:\Users\volap\Desktop\New folder\KrishilQ\backend"

# (First time only) Create a virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate

# (First time only) Install dependencies
pip install -r requirements.txt

# (First time only) Seed the database with test data
python seed.py

# Start the backend server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

✅ Backend runs at: **http://127.0.0.1:8001**  
📖 API docs (Swagger UI): **http://127.0.0.1:8001/docs**

---

#### Step 2 — Run the Web Dashboard

```powershell
# Navigate to web dashboard (new terminal)
cd "C:\Users\volap\Desktop\New folder\KrishilQ\web-dashboard"

# (First time only) Install dependencies
npm install

# Start the dev server
npm run dev
```

✅ Web dashboard runs at: **http://localhost:5173**  
Login with: `9000000001` / `officer123`

---

#### Step 3 — Run the Flutter Mobile App

```powershell
# Navigate to mobile app (new terminal)
cd "C:\Users\volap\Desktop\New folder\KrishilQ\mobile"

# (First time only) Get Flutter packages
flutter pub get

# Check available devices
flutter devices

# Run on a connected device or emulator
flutter run

# Or run specifically on Windows desktop (if no emulator)
flutter run -d windows

# Or run in Chrome (web mode)
flutter run -d chrome
```

> ⚠️ **Important:** Before running the mobile app, update `mobile/lib/config/app_config.dart`:
> ```dart
> // For Android emulator → backend
> static const String baseUrl = 'http://10.0.2.2:8001/api/v1';
> 
> // For physical device on same WiFi → use your PC's local IP
> static const String baseUrl = 'http://192.168.x.x:8001/api/v1';
> 
> // For Flutter web/Windows desktop
> static const String baseUrl = 'http://127.0.0.1:8001/api/v1';
> ```

---

## 🔗 How the Three Parts Connect

```
Flutter Mobile App
      │
      │  HTTP (REST API)  ──► backend/.env CORS_ORIGINS must include the origin
      ▼
FastAPI Backend  ──── SQLite DB (krishiiq_local.db)
      │             ──── OpenAI API (GPT-4o-mini)
      │             ──── OpenWeatherMap API
      │             ──── EfficientNet ML model
React Dashboard
      │
      │  HTTP (REST API)
      ▼
FastAPI Backend (same instance)
```

The backend CORS is configured in `app/main.py` to allow:
- `http://localhost:5173` (web dashboard)
- `https://krishil-q-frontend.vercel.app` (deployed frontend)

---

## ⚠️ Known Issues / Things to Check

1. **ngrok URL in mobile config** — `app_config.dart` has a hardcoded ngrok URL that will expire. Change it to `http://10.0.2.2:8001/api/v1` for emulator or your local IP for a physical device.

2. **OpenWeatherMap API key is placeholder** — The `.env` file has `OPENWEATHER_API_KEY=your_openweather_api_key`. Weather features will silently fail without a real key (get one free at openweathermap.org).

3. **AWS S3 keys are placeholder** — Image uploads for disease detection are configured for S3 but the keys are placeholders. Local `uploads/` folder is the fallback.

4. **ML model weights missing** — The `.pt` files for EfficientNet / yield predictor / GNN are not in the repo. Disease detection will return an error without them.

5. **Redis is optional** — If Redis isn't running, the app silently continues without it (see `database.py` try/except).

6. **`seed.py` should only run on an empty DB** — Running it twice will likely cause duplicate key errors. Run `reset.py` first if you need to re-seed.

7. **OpenAI key in `.env`** — There is what appears to be a real OpenAI key in the `.env`. This is a **security risk** — never commit `.env` with real keys to a public repo.

---

## 📊 Tech Stack Summary

| Layer | Technology |
|---|---|
| Backend API | FastAPI (Python) |
| Database | SQLite (dev) → PostgreSQL (prod) |
| Disease ML | EfficientNet via PyTorch + timm |
| Yield ML | Scikit-learn model |
| Field Analysis ML | Graph Neural Network (PyTorch Geometric) |
| AI Chat | OpenAI GPT-4o-mini (+ Groq as fallback) |
| Weather | OpenWeatherMap API |
| Web Frontend | React 18 + Vite + TailwindCSS |
| Charts | Recharts |
| Map | Leaflet / React-Leaflet |
| Auth State (web) | Zustand |
| Mobile | Flutter + Dart |
| Mobile State | Riverpod |
| Mobile Offline | Hive local DB |
| Mobile TTS | flutter_tts |
| Mobile Maps | flutter_map |

---

*Generated from full project analysis — KrishiIQ v1.0.0*
