from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
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

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="KrishiIQ API",
    description="AI-powered agricultural advisory system for Indian farmers",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://krishil-q-frontend.vercel.app",
    ],
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
    return {
        "message": "KrishiIQ API Running"
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "KrishiIQ API",
        "version": "1.0.0",
    }