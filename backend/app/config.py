"""Environment-backed application settings."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_GEMMA_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
DEFAULT_GEMMA_MODEL = "gemma-4-26b-a4b-it"


class Settings(BaseModel):
    """Runtime configuration. Secrets come from the environment only."""

    gemma_base_url: str = DEFAULT_GEMMA_BASE_URL
    gemma_api_key: str = ""
    gemma_model: str = DEFAULT_GEMMA_MODEL
    gemma_timeout_seconds: float = Field(default=90.0, gt=0)
    gemma_max_tokens: int = Field(default=4000, gt=0)
    gemma_temperature: float = Field(default=0.2, ge=0, le=2)
    frontend_origins: str = "http://localhost:4321,http://127.0.0.1:4321"

    @property
    def cors_origins(self) -> list[str]:
        """Return the configured browser origins as a clean list."""
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]

    @property
    def is_gemma_configured(self) -> bool:
        """Whether an API key is available for the Gemma endpoint."""
        return bool(self.gemma_api_key)


def load_environment() -> None:
    """Load local .env files without overriding variables already exported."""
    load_dotenv(REPO_ROOT / ".env")
    load_dotenv(BACKEND_ROOT / ".env")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Read settings once from the environment."""
    load_environment()
    return Settings(
        gemma_base_url=os.getenv("GEMMA_BASE_URL", DEFAULT_GEMMA_BASE_URL),
        gemma_api_key=os.getenv("GEMMA_API_KEY", ""),
        gemma_model=os.getenv("GEMMA_MODEL", DEFAULT_GEMMA_MODEL),
        gemma_timeout_seconds=float(os.getenv("GEMMA_TIMEOUT_SECONDS", "90")),
        gemma_max_tokens=int(os.getenv("GEMMA_MAX_TOKENS", "4000")),
        gemma_temperature=float(os.getenv("GEMMA_TEMPERATURE", "0.2")),
        frontend_origins=os.getenv(
            "FRONTEND_ORIGINS",
            "http://localhost:4321,http://127.0.0.1:4321",
        ),
    )
