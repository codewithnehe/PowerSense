"""Pydantic models shared by the API, signals, rules and Gemma layers."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

State = Literal["out_now", "elevated_risk", "possible_soon", "all_clear"]
Risk = Literal["low", "medium", "high"]
Persona = Literal["student", "shop_owner", "remote_worker"]
Language = Literal["en"]
ReportStatus = Literal["on", "off"]


class ReportSummary(BaseModel):
    """Aggregated report facts. Never contains device IDs or coordinates."""

    model_config = ConfigDict(extra="forbid")

    off_reports_last_60m: int = Field(ge=0)
    on_reports_last_60m: int = Field(ge=0)
    distinct_devices: int = Field(ge=0)
    latest_report_age_minutes: int | None = Field(default=None, ge=0)
    latest_status: ReportStatus | None = None


class WeatherSummary(BaseModel):
    """Small, already-summarised weather window for the area."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=3, max_length=200)
    precipitation_probability: float | None = Field(default=None, ge=0, le=1)
    window_hours: int = Field(default=3, ge=1, le=6)


class GridSummary(BaseModel):
    """Optional national grid signal. Missing data is not an outage."""

    model_config = ConfigDict(extra="forbid")

    available: bool
    trend: str | None = Field(default=None, max_length=120)


class SignalFacts(BaseModel):
    """Aggregated facts that may be sent to Gemma.

    This model deliberately has no device IDs, coordinates, raw report text,
    or free-text user input. Keep it that way.
    """

    model_config = ConfigDict(extra="forbid")

    local_time: datetime
    persona: Persona
    language: Language
    rule_state: State
    rule_is_floor: bool = False
    reports: ReportSummary
    weather: WeatherSummary | None = None
    grid: GridSummary | None = None


class AreaSignals(BaseModel):
    """Signals for one approximate area cell, plus demo metadata."""

    model_config = ConfigDict(extra="forbid")

    cell: str = Field(min_length=4, max_length=12)
    area_label: str = Field(min_length=2, max_length=120)
    is_demo: bool = False
    facts: SignalFacts


class AlertAssessment(BaseModel):
    """The exact JSON contract Gemma must satisfy."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    state: State
    risk: Risk
    reason: str = Field(min_length=3, max_length=300)
    message: str = Field(min_length=3, max_length=500)
    actions: list[str] = Field(min_length=2, max_length=3)
    why: str = Field(min_length=3, max_length=600)

    @field_validator("actions")
    @classmethod
    def clean_actions(cls, actions: list[str]) -> list[str]:
        """Reject blank, oversized or duplicated actions."""
        cleaned = [action.strip() for action in actions]
        if any(not action or len(action) > 120 for action in cleaned):
            raise ValueError("actions must be non-empty and at most 120 characters")
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("actions must be unique")
        return cleaned


class GemmaResult(BaseModel):
    """Validated assessment plus provenance for the fallback path."""

    assessment: AlertAssessment
    used_fallback: bool
    attempts: int = Field(ge=0)
    error: str | None = None


class AlertResponse(BaseModel):
    """Public shape of GET /alert for the Power Window."""

    cell: str
    area_label: str
    persona: Persona
    language: Language
    state: State
    risk: Risk
    reason: str
    message: str
    actions: list[str]
    why: str
    rule_state: State
    used_fallback: bool
    is_demo: bool
    created_at: datetime


class HealthResponse(BaseModel):
    """Basic liveness response."""

    status: str
