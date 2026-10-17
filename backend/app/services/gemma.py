"""Gemma call, strict JSON extraction, validation, retry and fallback."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.models import AlertAssessment, GemmaResult, SignalFacts
from app.services.fallback import build_fallback
from app.services.prompts import build_messages

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 2
REQUIRED_KEYS = {"state", "risk", "reason", "message", "actions", "why"}


class GemmaResponseError(RuntimeError):
    """Raised when the endpoint returns no usable assistant text."""


def extract_alert_json(text: str) -> dict[str, Any]:
    """Extract the last complete alert-shaped JSON object from model text.

    Gemma 4 is a thinking model and may put reasoning (including example
    JSON) before the final answer. We prefer text after the last
    ``</thought>`` marker, then fall back to scanning the whole reply. The
    last valid object wins, which is normally the final answer.

    Args:
        text: Raw assistant content.

    Returns:
        The parsed JSON object, not yet schema-validated.

    Raises:
        ValueError: If no alert-shaped JSON object is present.
    """
    candidates: list[str] = []
    if "</thought>" in text:
        candidates.append(text.rsplit("</thought>", 1)[1])
    candidates.append(text)

    for candidate in candidates:
        decoder = json.JSONDecoder()
        found: dict[str, Any] | None = None
        for index, char in enumerate(candidate):
            if char != "{":
                continue
            try:
                value, _ = decoder.raw_decode(candidate[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict) and REQUIRED_KEYS.issubset(value):
                found = value
        if found is not None:
            return found

    raise ValueError("no JSON object with the required alert keys found")


async def _request_completion(
    client: httpx.AsyncClient,
    settings: Settings,
    messages: list[dict[str, str]],
) -> str:
    """Call an OpenAI-compatible chat completions endpoint."""
    if not settings.is_gemma_configured:
        raise GemmaResponseError("GEMMA_API_KEY is not configured")

    url = f"{settings.gemma_base_url.rstrip('/')}/chat/completions"
    response = await client.post(
        url,
        headers={
            "Authorization": f"Bearer {settings.gemma_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.gemma_model,
            "messages": messages,
            "temperature": settings.gemma_temperature,
            "max_tokens": settings.gemma_max_tokens,
        },
    )
    response.raise_for_status()

    try:
        payload = response.json()
    except ValueError as exc:
        raise GemmaResponseError("endpoint returned malformed JSON") from exc

    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise GemmaResponseError("endpoint response had no assistant content") from exc

    if isinstance(content, list):
        content = "".join(
            part.get("text", "") for part in content if isinstance(part, dict)
        )
    if not isinstance(content, str) or not content.strip():
        raise GemmaResponseError("endpoint returned empty assistant content")
    return content


async def generate_assessment(
    facts: SignalFacts,
    settings: Settings | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> GemmaResult:
    """Ask Gemma for an assessment, validating and retrying once.

    The input is aggregated facts only. If both attempts fail, the
    deterministic fallback is returned with ``used_fallback=True``.

    Args:
        facts: Anonymous signal facts, including the rule state.
        settings: Optional settings override for tests.
        http_client: Optional client override for tests.

    Returns:
        A validated assessment and its provenance.
    """
    resolved_settings = settings or get_settings()
    if not resolved_settings.is_gemma_configured:
        logger.warning("Gemma API key is not configured; using template fallback")
        return GemmaResult(
            assessment=build_fallback(facts),
            used_fallback=True,
            attempts=0,
            error="GEMMA_API_KEY is not configured",
        )

    owns_client = http_client is None
    client = http_client or httpx.AsyncClient(
        timeout=resolved_settings.gemma_timeout_seconds
    )
    messages = build_messages(facts)
    attempts = 0
    last_error: Exception | None = None

    try:
        while attempts < MAX_ATTEMPTS:
            attempts += 1
            started = time.perf_counter()
            try:
                raw_text = await _request_completion(client, resolved_settings, messages)
            except (httpx.HTTPError, GemmaResponseError) as exc:
                last_error = exc
                logger.warning(
                    "Gemma request failed (attempt %d/%d): %s",
                    attempts,
                    MAX_ATTEMPTS,
                    exc,
                )
                continue

            try:
                assessment = AlertAssessment.model_validate(extract_alert_json(raw_text))
            except (ValueError, ValidationError) as exc:
                last_error = exc
                logger.warning(
                    "Gemma output failed validation (attempt %d/%d): %s",
                    attempts,
                    MAX_ATTEMPTS,
                    str(exc)[:300],
                )
                if attempts < MAX_ATTEMPTS:
                    messages = [
                        *messages,
                        {
                            "role": "user",
                            "content": (
                                "Your previous reply did not match the required "
                                f"schema: {str(exc)[:300]}. Return only a corrected "
                                "JSON object with exactly the allowed values."
                            ),
                        },
                    ]
                continue

            elapsed_ms = int((time.perf_counter() - started) * 1000)
            logger.info(
                "Gemma assessment valid (model=%s, attempt=%d, latency_ms=%d)",
                resolved_settings.gemma_model,
                attempts,
                elapsed_ms,
            )
            return GemmaResult(
                assessment=assessment,
                used_fallback=False,
                attempts=attempts,
            )
    finally:
        if owns_client:
            await client.aclose()

    logger.warning(
        "Gemma failed after %d attempts; using template fallback: %s",
        attempts,
        str(last_error)[:300],
    )
    return GemmaResult(
        assessment=build_fallback(facts),
        used_fallback=True,
        attempts=attempts,
        error=str(last_error)[:500] if last_error else "unknown Gemma error",
    )
