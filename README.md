# 🌾 KrishiIQ — AI-Powered Agricultural Advisory System

KrishiIQ is an end-to-end smart farming platform built to help Indian farmers make better decisions about their crops. It combines IoT sensor data, weather forecasts, machine learning, and large language models to deliver personalised advisory — in the farmer's own language — directly on their phone.

The system has three parts that work together: a Python backend that handles all the intelligence, a web dashboard for agricultural officers, and a Flutter mobile app for farmers in the field.

---

## The Problem It Solves

Farmers in India often lack timely access to expert advice on irrigation, fertilizers, and disease treatment. By the time they notice a problem, crop damage has already happened. KrishiIQ closes that gap by continuously monitoring farm conditions and pushing actionable recommendations before problems escalate.

---

## How It Works

### 1. 📱 Farmer Mobile App (Flutter)

The app is what farmers actually use day-to-day. When they open it they see a personalised greeting ("Vanakkam, Farmer!") in their chosen language — English, Hindi, or Tamil.

**What farmers can do:**

- **Check their advisory feed** — The app shows cards like "Irrigate within 24 hours" or "Apply urea fertilizer — nitrogen levels are low." These are generated automatically based on the farm's live sensor readings and weather forecast. Each advisory can be read aloud using text-to-speech, so literacy is not a barrier.

- **Detect crop diseases from a photo** — The farmer taps "Crop Health", takes a photo of a sick plant with their camera, and the app sends it to the backend. An EfficientNet deep learning model classifies the disease from 16 possible conditions (Bacterial Blight, Late Blight, Leaf Blast, Rust, Mosaic Virus, etc.) and returns the diagnosis plus a recommended treatment — again in the farmer's language.

- **Chat with an AI assistant** — A full conversation screen backed by GPT-4o-mini / Groq where farmers can ask anything about their crops in plain language and get a helpful reply.

- **View irrigation scheduling** — Based on soil moisture readings from sensors and the 12-hour rainfall forecast, the app tells the farmer whether to irrigate, how much, and when.

- **Log soil data manually** — Farmers can enter soil readings if they don't have automated sensors.

- **Works offline** — Data is cached locally using Hive so the app is usable even without a network connection.

---

### 2. 🌐 Web Dashboard (React)

This is for agricultural officers and district admins, not farmers. It gives a bird's-eye view of all the farms under their jurisdiction.

**What officers can see:**

- **District Overview** — Total farmers registered, total farms, total area in acres, and count of active high-severity disease alerts — all on one screen with live charts.

- **Crop Yield Trends** — A line chart tracking kg/acre over time across different crop types, so officers can spot district-wide production patterns.

- **Farm Map** — An interactive map (Leaflet or Google Maps) showing all registered farms as pins. Officers can click a farm to see its details.

- **Disease Alerts** — A feed of all disease detections reported across farms, filterable by severity, so officers can prioritise which farmers need immediate follow-up.

- **Farmer Profiles** — A searchable list of all registered farmers with their contact details, farm sizes, and crop history.

- **Analytics** — Deeper charts on soil health, sensor trends, and advisory effectiveness over time.

---

### 3. ⚙️ Backend (FastAPI + AI/ML)

The backend is the brain. It runs continuously, pulling sensor data, checking weather, and generating advisories automatically. It also serves the API that both the dashboard and mobile app consume.

**Key intelligence layers:**

- **Advisory Engine** — Reads the latest sensor reading for each farm (soil moisture, nitrogen, phosphorus, potassium, temperature, pH). Compares against thresholds. If soil moisture drops below 35% and no rain is expected, it generates an irrigation advisory in all three languages and stores it. Similar logic runs for fertilizer deficiencies and pest risk.

- **Disease Detection** — Accepts an uploaded crop photo, preprocesses it, and runs inference through a fine-tuned EfficientNet model trained on 16 disease classes. Returns the disease name, confidence score, and treatment text in English, Hindi, and Tamil.

- **LLM Chat** — Routes farmer questions through OpenAI GPT-4o-mini (primary) or Groq (fallback) with an agriculture-specific system prompt so answers are relevant and grounded.

- **Weather Integration** — Fetches forecasts from OpenWeatherMap for each farm's GPS coordinates. Rain probability feeds directly into irrigation logic.

- **GNN Field Analysis** — A Graph Neural Network model for cross-field analysis (linking neighbouring farms to identify spreading disease patterns).

---

## Technology Choices

| What | Why |
|---|---|
| FastAPI | Async Python, automatic OpenAPI docs, fast to build |
| SQLite (dev) / PostgreSQL (prod) | Simple local dev, production-grade at scale |
| EfficientNet via PyTorch + timm | State-of-the-art accuracy at low inference cost for image classification |
| OpenAI GPT-4o-mini + Groq fallback | Cost-effective LLM with a fast fallback |
| Flutter + Riverpod | Single codebase for Android and iOS, reactive state management |
| Hive | Lightweight local DB for offline caching on mobile |
| React + Tailwind + Recharts | Fast dashboard UI with minimal boilerplate |
| Zustand | Lightweight auth state for the web app |

---

## Supported Languages

The mobile app and all AI-generated advisories support:
- 🇬🇧 English
- 🇮🇳 Hindi
- 🇮🇳 Tamil

Disease treatment texts, irrigation alerts, and fertilizer recommendations are all stored and served in all three languages simultaneously.

---

## Project Structure at a Glance

```
KrishilQ/
├── backend/          # FastAPI — API, ML inference, advisory engine, LLM chat
├── web-dashboard/    # React + Vite — officer/admin dashboard
└── mobile/           # Flutter — farmer-facing Android & iOS app
```

---

## Who It's For

| User | Interface | Role |
|---|---|---|
| Farmer | Mobile App | Receives advisories, detects diseases, chats with AI |
| Agricultural Officer | Web Dashboard | Monitors district farms, tracks disease outbreaks |
| Admin | Web Dashboard | Manages users, farms, and system configuration |

---

Built with ❤️ to bring precision agriculture to every Indian farmer.
