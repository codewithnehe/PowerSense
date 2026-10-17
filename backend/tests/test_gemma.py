"""Tests for the Gemma validation, retry and fallback path."""

from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.config import Settings
from app.models import SignalFacts
from app.services.fallback import build_fallback
from app.services.gemma import (
    GemmaResponseError,
    extract_alert_json,
    generate_assessment,
)
from app.services.prompts import build_messages
from app.services.signals import get_demo_signals

VALID_ASSESSMENT = {
    "state": "elevated_risk",
    "risk": "medium",
    "reason": "Recent outage reports and incoming thunderstorm.",
    "message": "Power may go out soon. Charge what matters while you can.",
    "actions": ["Charge your phone", "Keep a torch nearby"],
    "why": "Two nearby devices reported power loss and a storm is likely.",
}

TEST_SETTINGS = Settings(
    gemma_base_url="https://gemma.test/v1",
    gemma_api_key="test-key",
    gemma_model="gemma-test",
    gemma_timeout_seconds=5,
)


def make_facts() -> SignalFacts:
    """Fixed facts for deterministic tests."""
    return get_demo_signals(
        now=datetime(2026, 10, 17, 18, 0, tzinfo=ZoneInfo("Africa/Lagos"))
    ).facts


def completion_response(content: str) -> httpx.Response:
    """Build an OpenAI-compatible chat completion response."""
    return httpx.Response(
        200,
        json={
            "choices": [
                {"index": 0, "message": {"role": "assistant", "content": content}}
            ]
        },
    )


async def test_valid_output_is_accepted_on_first_attempt() -> None:
    """A schema-valid reply is returned unchanged and not marked as fallback."""
    transport = httpx.MockTransport(
        lambda request: completion_response(json.dumps(VALID_ASSESSMENT))
    )
    async with httpx.AsyncClient(transport=transport) as client:
        result = await generate_assessment(
            make_facts(), settings=TEST_SETTINGS, http_client=client
        )

    assert result.used_fallback is False
    assert result.attempts == 1
    assert result.error is None
    assert result.assessment.model_dump() == VALID_ASSESSMENT


async def test_invalid_output_is_retried_with_correction() -> None:
    """An invalid state triggers exactly one corrective retry."""
    calls: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        calls.append(payload)
        if len(calls) == 1:
            return completion_response(
                json.dumps({**VALID_ASSESSMENT, "state": "outage"})
            )
        return completion_response(json.dumps(VALID_ASSESSMENT))

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        result = await generate_assessment(
            make_facts(), settings=TEST_SETTINGS, http_client=client
        )

    assert len(calls) == 2
    assert result.used_fallback is False
    assert result.attempts == 2
    assert result.assessment.state == "elevated_risk"
    assert "did not match the required schema" in calls[1]["messages"][-1]["content"]


async def test_two_invalid_outputs_fall_back_to_rule_state() -> None:
    """After two schema failures the template fallback is used."""
    invalid = {**VALID_ASSESSMENT, "actions": ["Only one action"]}
    transport = httpx.MockTransport(
        lambda request: completion_response(json.dumps(invalid))
    )
    async with httpx.AsyncClient(transport=transport) as client:
        result = await generate_assessment(
            make_facts(), settings=TEST_SETTINGS, http_client=client
        )

    facts = make_facts()
    assert result.used_fallback is True
    assert result.attempts == 2
    assert result.error is not None
    assert result.assessment.state == facts.rule_state
    assert result.assessment.model_dump() == build_fallback(facts).model_dump()


async def test_http_errors_fall_back_after_one_retry() -> None:
    """Transport failures are retried once, then fall back."""
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503, json={"error": "unavailable"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        result = await generate_assessment(
            make_facts(), settings=TEST_SETTINGS, http_client=client
        )

    assert calls == 2
    assert result.used_fallback is True
    assert result.attempts == 2


async def test_missing_api_key_falls_back_without_calling_endpoint() -> None:
    """No key means no request and no retry."""
    settings = TEST_SETTINGS.model_copy(update={"gemma_api_key": ""})
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return completion_response(json.dumps(VALID_ASSESSMENT))

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        result = await generate_assessment(
            make_facts(), settings=settings, http_client=client
        )

    assert called is False
    assert result.used_fallback is True
    assert result.attempts == 0


async def test_thinking_text_before_final_json_is_ignored() -> None:
    """Gemma's thought block may contain example JSON; the final object wins."""
    content = (
        "<thought>Maybe {\"state\": \"all_clear\"} looks right.</thought>\n"
        + json.dumps(VALID_ASSESSMENT)
    )
    transport = httpx.MockTransport(lambda request: completion_response(content))
    async with httpx.AsyncClient(transport=transport) as client:
        result = await generate_assessment(
            make_facts(), settings=TEST_SETTINGS, http_client=client
        )

    assert result.used_fallback is False
    assert result.assessment.state == "elevated_risk"


def test_extract_prefers_last_alert_shaped_object() -> None:
    """Earlier JSON examples are skipped when a later valid answer exists."""
    text = (
        'Example: {"state": "all_clear", "risk": "low", "reason": "r", '
        '"message": "m", "actions": ["a", "b"], "why": "w"}\n'
        'Final: {"state": "elevated_risk", "risk": "medium", "reason": "r2", '
        '"message": "m2", "actions": ["a", "b"], "why": "w2"}'
    )
    extracted = extract_alert_json(text)
    assert extracted["state"] == "elevated_risk"
    assert extracted["reason"] == "r2"


def test_extract_rejects_text_without_alert_json() -> None:
    """Plain prose is not accepted as an assessment."""
    with pytest.raises(ValueError):
        extract_alert_json("Power will definitely go out at 3pm.")


async def test_empty_content_is_treated_as_a_failed_attempt() -> None:
    """Empty assistant content cannot produce an assessment."""
    transport = httpx.MockTransport(lambda request: completion_response("   "))
    async with httpx.AsyncClient(transport=transport) as client:
        result = await generate_assessment(
            make_facts(), settings=TEST_SETTINGS, http_client=client
        )

    assert result.used_fallback is True
    assert result.attempts == 2


async def test_malformed_json_response_falls_back() -> None:
    """A 200 response with a non-JSON body still reaches the fallback path."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"<html>gateway error</html>")
    )
    async with httpx.AsyncClient(transport=transport) as client:
        result = await generate_assessment(
            make_facts(), settings=TEST_SETTINGS, http_client=client
        )

    assert result.used_fallback is True
    assert result.attempts == 2
    assert "malformed JSON" in (result.error or "")


def test_prompt_contains_only_aggregated_facts() -> None:
    """No cell, device identifiers or coordinates reach the model."""
    facts = make_facts()
    messages = build_messages(facts)
    payload = "\n".join(message["content"] for message in messages)

    assert "Current facts" in payload
    assert "device_id" not in payload
    assert "latitude" not in payload
    assert "longitude" not in payload
    assert "6.45" not in payload
    assert "3.39" not in payload

    facts_json = json.loads(messages[-1]["content"].split("\n", 1)[1])
    assert facts_json["rule_state"] == "all_clear"
    assert facts_json["reports"]["distinct_devices"] == 2


def test_unknown_extra_fields_are_rejected() -> None:
    """Gemma cannot smuggle extra fields past the schema."""
    with pytest.raises(Exception):
        from app.models import AlertAssessment

        AlertAssessment.model_validate({**VALID_ASSESSMENT, "confidence": 0.9})
