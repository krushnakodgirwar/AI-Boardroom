from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.app.api.routes import router


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

FRONTEND_DIR = BASE_DIR / "frontend"


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="AI Boardroom",
    description="Multi-Agent Business Decision Simulator",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# API ROUTES
# ============================================================

app.include_router(router)


# ============================================================
# FRONTEND - LANDING PAGE
# ============================================================

@app.get("/", include_in_schema=False)
def landing_page():

    return FileResponse(
        FRONTEND_DIR / "landingpage.html"
    )


# ============================================================
# FRONTEND - BOARDROOM PAGE
# ============================================================

@app.get("/boardroom", include_in_schema=False)
def boardroom_page():

    return FileResponse(
        FRONTEND_DIR / "boardroom.html"
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "project": "AI Boardroom"
    }


# ============================================================
# PROJECT INFO
# ============================================================

@app.get("/api/info")
def project_info():

    return {
        "project": "AI Boardroom",
        "version": "1.0.0",
        "status": "running"
    }