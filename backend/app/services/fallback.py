"""Deterministic template assessment used when Gemma cannot be validated."""

from __future__ import annotations

from app.models import AlertAssessment, Persona, Risk, SignalFacts, State

_RISK_BY_STATE: dict[State, Risk] = {
    "out_now": "high",
    "elevated_risk": "medium",
    "possible_soon": "medium",
    "all_clear": "low",
}

_MESSAGE_BY_STATE: dict[State, str] = {
    "out_now": (
        "Reports suggest power is out near you right now. "
        "Charge what you can and keep essentials ready."
    ),
    "elevated_risk": (
        "Conditions may make an outage more likely soon. "
        "Keep your essential devices charged."
    ),
    "possible_soon": (
        "Power conditions may change soon. "
        "Charge essentials while you can."
    ),
    "all_clear": (
        "No confirmed outage near you right now. "
        "Keep your devices charged when you can."
    ),
}

_REASON_BY_STATE: dict[State, str] = {
    "out_now": "Multiple recent reports from nearby devices.",
    "elevated_risk": "Recent reports and a weather signal suggest elevated risk.",
    "possible_soon": "The grid trend suggests a possible change.",
    "all_clear": "No recent reports met the outage threshold.",
}

_ACTIONS_BY_PERSONA: dict[Persona, list[str]] = {
    "student": ["Charge your laptop and phone", "Keep a power bank ready"],
    "shop_owner": ["Keep the freezer closed", "Charge your phone and backup power"],
    "remote_worker": ["Charge your laptop and power bank", "Have mobile data ready"],
}


def build_fallback(facts: SignalFacts) -> AlertAssessment:
    """Build a safe template assessment from the rule state.

    Args:
        facts: Anonymous signal facts, including the rule-based state.

    Returns:
        A schema-valid assessment that makes no predictive claims.
    """
    state = facts.rule_state
    return AlertAssessment(
        state=state,
        risk=_RISK_BY_STATE[state],
        reason=_REASON_BY_STATE[state],
        message=_MESSAGE_BY_STATE[state],
        actions=_ACTIONS_BY_PERSONA[facts.persona],
        why=(
            "This is a template message used because the AI assessment could not "
            "be validated. It is based only on the current rule state and "
            "aggregated report counts."
        ),
    )
