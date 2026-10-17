# PowerSense: Design Doc

Hacktoberfest 2026 entry. A web app that tells you when power is out or likely to go, and what to do about it. **Gemma**, an open-weight model, is the reasoning core: it weighs the signals, decides how worried to be, and explains itself in plain English or Pidgin.

## Stack

| Layer | Choice |
|---|---|
| Frontend | Astro (static pages, small interactive islands), installable as a PWA |
| Backend | Python with FastAPI, SQLite, httpx, a background scheduler (APScheduler) |
| AI | Gemma through a hosted or local endpoint, called from the backend only |
| Validation | Pydantic models for every request and for Gemma's JSON output |

## Core Loop

**Tap, signals, Gemma, alert, feedback.**

1. The user taps "light is on" or "light is off". The tap is saved locally and synced.
2. The backend gathers signals for the user's area: recent reports, weather, optional grid data.
3. Rules compute facts and hard limits. Gemma reads the signals and returns a structured assessment.
4. The Power Window shows the state, the reason, Gemma's message and actions.
5. The user taps thumbs up or down.

## Gemma's Role

Gemma is not a text decorator. Every alert depends on it. It does three jobs in a single call.

1. **Assess.** It weighs the evidence and picks the state and risk level. Examples: a storm forecast plus a shaky grid reading raises concern; one lone "off" report with no weather signal does not.
2. **Advise.** It writes a short message and 2 or 3 actions tailored to the persona (student, shop owner, remote worker) and the time of day.
3. **Explain.** It returns a plain-language "why am I being warned?" shown behind a "Why?" button.

It writes in English or Pidgin, based on the user's setting.

### Guardrails (rules around Gemma)

Gemma is the reasoner, but a small model can be wrong, so deterministic rules set the limits:

- **Out now** can only be returned when the rule is met: 3+ "off" reports from different devices, within 2 km, in the last 60 minutes, with no newer "on" report. If the rule is met, Gemma cannot downgrade it.
- Gemma may choose between **Elevated risk**, **Possible soon** and **All clear** from the evidence. It cannot invent signals that are not in its input.
- Output must pass the Pydantic schema. If it fails, retry once, then use the rule-based state with a template message.
- Messages must never claim certainty ("power will go at 3pm"). The prompt requires hedged language for anything predictive.

### Output schema

```json
{
  "state": "out_now | elevated_risk | possible_soon | all_clear",
  "risk": "low | medium | high",
  "reason": "3 confirmed reports within 2 km",
  "message": "Light's confirmed out near you. Charge your laptop and phone now.",
  "actions": ["Charge your laptop", "Pump water"],
  "why": "Three different devices near you reported no power in the last hour."
}
```

### Input to Gemma

Structured facts only, never raw user text: rule-based state and whether it is a hard floor, report counts and ages, weather summary for the next 3 hours, optional grid trend, local time, persona, language.

### Model hosting

Call Gemma through one `gemma.py` module using an OpenAI-compatible chat interface, with the base URL, API key and model name in environment variables. This keeps the provider swappable: a hosted Gemma endpoint, or Ollama running Gemma locally as a backup. Confirm which provider and Gemma size to use before building (see Open Items). Cache Gemma results per area, persona, language and signal fingerprint for a few minutes to stay within free-tier limits.

## Users

| Persona | Need | Example action |
|---|---|---|
| Student | Charged laptop before class | "Charge your laptop now." |
| Shop owner | Protect fridge or freezer stock | "Keep the freezer shut. Plan for a cut." |
| Remote worker | Stay online for calls | "Switch to a power bank or mobile data soon." |

The user picks a persona and language once, stored locally. No login: each device gets a random ID.

## States

| State | Source of the decision | Signal type |
|---|---|---|
| **Out now** | Rule (hard floor, see Guardrails) | Reactive |
| **Elevated risk** | Gemma, usually from thunderstorm or heavy rain forecast in the next 3 hours | Predictive (likely, not guaranteed) |
| **Possible soon** | Gemma, from a sharp drop in national generation (optional, feature-flagged) | Weak, grid-wide |
| **All clear** | Default when nothing else applies | n/a |

## Architecture

```
/backend
  app/main.py            FastAPI app, CORS, routes
  app/routes/reports.py  POST /reports, GET /reports/area
  app/routes/alert.py    GET /alert?cell=&persona=&lang=
  app/services/
    weather.py           OpenWeatherMap 3-hour forecast, cached by location cell
    grid.py              Nigeria Power Data, optional, cached, feature-flagged
    nepawatch.py         optional bonus input, cached
    signals.py           collects all signals into one structured object
    rules.py             hard facts and guardrails (out-now rule, expiry)
    gemma.py             model call, JSON validation, retry
    prompts.py           English and Pidgin prompt templates
    fallback.py          rule-based state plus template messages
  app/scheduler.py       timed fetches for weather, grid, NEPAWatch
  app/db.py, models.py   SQLite tables and Pydantic models
  tests/                 rules tests and Gemma scenario tests

/frontend
  src/pages/index.astro  Power Window
  src/pages/report.astro Report buttons
  src/components/        PowerWindow, ReportButtons, WhyDrawer, FeedbackButtons
  src/lib/queue.ts       IndexedDB queue and sync
  src/lib/api.ts         calls to the FastAPI backend
  public/sw.js           service worker for offline use
```

Request flow for `GET /alert`: load cached signals, run `rules.py`, call `gemma.py` with the facts, validate, store the alert, return it.

## Data Model

**reports**: `id`, `device_id`, `status` (on/off), `cell` (geohash, about 1 km), `event_time`, `is_demo`.

**alerts**: `id`, `cell`, `persona`, `lang`, `state`, `risk`, `message`, `rule_state`, `used_fallback`, `created_at`.

**feedback**: `alert_id`, `device_id`, `helpful`, `created_at`.

Storing `rule_state` beside Gemma's state lets you measure how often Gemma agrees with the rules and how users rate each.

## Data Sources

| Source | Use | Notes |
|---|---|---|
| Our reports | Main signal | Own endpoint and database |
| OpenWeatherMap | Storm and rain signal | Free tier, cached |
| Nigeria Power Data (nigeriapowerdata.com) | Optional grid trend | Server-side only, 10 to 15 minute timer, cached |
| NEPAWatch | Optional bonus | 100 requests/day: poll every 30 to 60 minutes, never per user |

Nigeria Power Data endpoints used: `/api/health`, `/api/grid/live`, `/api/generation?hours=24&limit=288`, `/api/geography/search?q=`, `/api/states/{slug}`. Response shapes are unverified: check them with a real call and keep parsing in `grid.py`. The app must work with reports plus weather alone.

## Offline Reporting

- Each tap is stored in IndexedDB with coordinates and its event time.
- Sync when the app opens and on the `online` event. Do not rely on Background Sync (not supported on iOS Safari).
- Reports older than 60 minutes do not count toward "Out now".

## Power Window

1. **Status:** the state and the time of the latest report.
2. **Reason:** one line from Gemma.
3. **Message and actions:** from Gemma.
4. **Why?** drawer with Gemma's explanation.
5. **Feedback:** "Was this right?" thumbs up or down.

## Privacy and Abuse

- Round coordinates to about 1 km on the server.
- Rate limit writes per device.
- Send Gemma only aggregated facts, never device IDs or exact coordinates.
- Show a short note about what location data is stored.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Gemma gives a wrong or overconfident state | Rule floor for "Out now", schema validation, hedged-language prompt |
| Invalid JSON from the model | One retry, then rule-based fallback |
| Model slow or rate limited | Result caching, smaller Gemma variant, template fallback |
| Uneven Pidgin quality | Test early with example prompts, tune, fall back to English |
| False or spam reports | 3 distinct devices, radius, time window, rate limiting |
| Sparse data on stage | Seeded reports flagged `is_demo`, weather fallback |
| API limits (NEPAWatch) | Server-side cache, slow timer, app works without it |

## Build Order

1. Thin slice: hardcoded signals, call Gemma, validate the JSON, show it in a basic Astro page.
2. Prompts for English and Pidgin, with a small set of test scenarios.
3. FastAPI app, database, report endpoint.
4. Astro report page with local queue and sync.
5. Weather service and `signals.py`.
6. `rules.py` with tests, then wire rules and Gemma together.
7. Full Power Window with Why and feedback.
8. Optional grid signal ("Possible soon").
9. Seed demo data, test on a phone.
10. Write up the project on DEV.

## Demo Plan

1. Seed reports so there is data on stage.
2. Ask the audience to open the URL and tap a report.
3. Show Gemma's alert and tap "Why?" to show its reasoning.
4. Switch the language to Pidgin live.
5. Say plainly that demo reports are seeded and that weather is the main forward-looking signal.

## Out of Scope

Accounts, push notifications, native app, saved routines, fine-tuning Gemma.

## Open Items

- Choose the Gemma provider and size (hosted endpoint or local Ollama), and confirm it meets the hackathon's open-weight rule.
- Confirm hackathon submission rules (license, repo visibility, write-up format).
- Verify the Nigeria Power Data and NEPAWatch response fields and terms.
- Tune the out-now threshold and the "sharp drop" threshold from feedback data.