"""GET /alert: build signals, ask Gemma, return the validated assessment."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.models import AlertResponse, Language, Persona
from app.services.gemma import generate_assessment
from app.services.signals import get_demo_signals

router = APIRouter(tags=["alert"])


@router.get("/alert", response_model=AlertResponse)
async def get_alert(
    persona: Persona = "student",
    lang: Language = "en",
) -> AlertResponse:
    """Return Gemma's current assessment for the demo area.

    Signals are hardcoded in step 1. Cell-based signals and caching arrive in
    later steps.
    """
    area = get_demo_signals(persona=persona, language=lang)
    result = await generate_assessment(area.facts)
    assessment = result.assessment

    return AlertResponse(
        cell=area.cell,
        area_label=area.area_label,
        persona=area.facts.persona,
        language=area.facts.language,
        state=assessment.state,
        risk=assessment.risk,
        reason=assessment.reason,
        message=assessment.message,
        actions=assessment.actions,
        why=assessment.why,
        rule_state=area.facts.rule_state,
        used_fallback=result.used_fallback,
        is_demo=area.is_demo,
        created_at=datetime.now(timezone.utc),
    )
