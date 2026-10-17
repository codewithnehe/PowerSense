"""PowerSense FastAPI application."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models import HealthResponse
from app.routes.alert import router as alert_router

settings = get_settings()

app = FastAPI(
    title="PowerSense",
    description="Gemma-powered power-outage assessments for Nigeria.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(alert_router)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness check used by local development and deploys."""
    return HealthResponse(status="ok")
