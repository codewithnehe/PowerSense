"""Hardcoded demo signals for the step-1 thin slice.

This module is intentionally the only place that fabricates signal data.
Later steps replace it with cached weather, optional grid data and real
aggregated reports. Demo data is marked `is_demo=True` so it can never be
mistaken for a real reading.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.models import (
    AreaSignals,
    GridSummary,
    Language,
    Persona,
    ReportSummary,
    SignalFacts,
    WeatherSummary,
)

LAGOS_TZ = ZoneInfo("Africa/Lagos")
DEMO_CELL = "s14k9q"
DEMO_AREA_LABEL = "Lekki Phase 1, Lagos"


def get_demo_signals(
    persona: Persona = "student",
    language: Language = "en",
    now: datetime | None = None,
) -> AreaSignals:
    """Return a fixed, anonymous storm-risk scenario for the thin slice.

    Args:
        persona: Persona used to tailor Gemma's advice.
        language: Response language.
        now: Optional clock override for tests.

    Returns:
        Aggregated signals for one approximate area cell.
    """
    local_time = now or datetime.now(LAGOS_TZ)
    facts = SignalFacts(
        local_time=local_time,
        persona=persona,
        language=language,
        rule_state="all_clear",
        rule_is_floor=False,
        reports=ReportSummary(
            off_reports_last_60m=2,
            on_reports_last_60m=0,
            distinct_devices=2,
            latest_report_age_minutes=12,
            latest_status="off",
        ),
        weather=WeatherSummary(
            summary="Thunderstorm likely within 2 hours",
            precipitation_probability=0.75,
            window_hours=3,
        ),
        # The optional grid feed is not wired yet. unavailable means no data,
        # not an outage.
        grid=GridSummary(available=False, trend=None),
    )
    return AreaSignals(
        cell=DEMO_CELL,
        area_label=DEMO_AREA_LABEL,
        is_demo=True,
        facts=facts,
    )
