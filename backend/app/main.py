from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import router


app = FastAPI(
    title="AI Boardroom",
    description="Multi-Agent Business Decision Simulator",
    version="1.0.0"
)


# CORS

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


# API ROUTES

app.include_router(router)


# ROOT

@app.get("/")
def root():

    return {
        "project": "AI Boardroom",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }


# HEALTH CHECK

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }