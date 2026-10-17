# PowerSense

PowerSense is a Hacktoberfest 2026 web app that tells people in Nigeria when
power is out or likely to go, and what to do about it. Gemma is the reasoning
core: it weighs aggregated signals, chooses the state and risk level, writes the
message and actions, and explains itself. Deterministic rules set the limits.

The project follows the design in [`docs/spec.md`](docs/spec.md).

## Current status: step 1 (thin slice)

This commit implements only the first build step:

- Hardcoded, clearly marked demo signals for one area (Lekki Phase 1, Lagos).
- A real Gemma call through an OpenAI-compatible chat endpoint.
- Strict Pydantic validation of the JSON assessment, one corrective retry, then
  a deterministic template fallback.
- `used_fallback` and `is_demo` are returned with every assessment.
- A basic static Astro page that shows state, reason, message, actions and the
  "Why?" explanation.
- Unit tests for the validation, retry and fallback paths.

Not built yet: reports/database, rules engine, caching, weather/grid/NEPAWatch
collectors, offline queue, Pidgin, feedback, and the full Power Window. Those
arrive in later build steps.

## Stack

- Backend: Python 3.11+, FastAPI, Pydantic, httpx, SQLite and APScheduler later.
- Frontend: Astro, TypeScript, IndexedDB and a service worker later.
- AI: Gemma only, called server-side through an OpenAI-compatible endpoint.

## Prerequisites

- Python 3.11 or newer
- [`uv`](https://docs.astral.sh/uv/)
- Node.js 22 or newer and npm

## Environment

The backend reads `.env` from the repository root (and `backend/.env` if
present). Copy the example and fill in the key for your hosted Gemma endpoint:

```bash
cp .env.example .env
# edit .env and set GEMMA_API_KEY
```

`GEMMA_BASE_URL` must be an OpenAI-compatible chat-completions base URL that
serves a Gemma model. `GEMMA_MODEL` is the exact model ID. The API key is only
read by the backend and is never sent to the browser.

| Variable | Purpose | Default |
|---|---|---|
| `GEMMA_BASE_URL` | OpenAI-compatible base URL | `https://generativelanguage.googleapis.com/v1beta/openai` |
| `GEMMA_MODEL` | Gemma model ID | `gemma-4-26b-a4b-it` |
| `GEMMA_API_KEY` | Host credential for the Gemma endpoint | required |
| `GEMMA_TIMEOUT_SECONDS` | Request timeout | `90` |
| `GEMMA_MAX_TOKENS` | Output budget (includes internal thinking) | `4000` |
| `GEMMA_TEMPERATURE` | Sampling temperature | `0.2` |
| `FRONTEND_ORIGINS` | Comma-separated allowed browser origins | localhost ports 4321 |
| `PUBLIC_API_BASE_URL` | Frontend-only; backend URL used by the browser | `http://localhost:8000` |

The frontend reads its own `frontend/.env` file. It is optional for local
development because the API URL defaults to `http://localhost:8000`:

```bash
cp frontend/.env.example frontend/.env
```

## Run the backend

```bash
cd backend
uv sync --extra dev
uv run uvicorn app.main:app --reload --port 8000
```

Verify it:

```bash
curl http://localhost:8000/health
curl "http://localhost:8000/alert?persona=student&lang=en"
```

`GET /alert` can take 15–30 seconds on the current Gemma host because the model
reasons before answering. Result caching is a later step.

## Run the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:4321>. The page calls the backend from the browser, so
the backend must be running. The frontend is static; no server-side rendering is
required.

## Tests and checks

```bash
cd backend
uv run pytest

cd ../frontend
npm run check
npm run build
```

The Gemma tests use a mocked transport and never call the live model. The live
call is exercised by running the app and requesting `/alert`.

## API (step 1)

- `GET /health` → `{"status":"ok"}`
- `GET /alert?persona=student|shop_owner|remote_worker&lang=en` → a validated
  assessment with `state`, `risk`, `reason`, `message`, `actions`, `why`,
  `rule_state`, `used_fallback`, `is_demo` and `created_at`.

## Privacy and guardrails in this step

- Gemma receives only aggregated facts: report counts, latest report age,
  weather summary, optional grid trend, local time, persona and language.
- The request model forbids extra fields, so device IDs, exact coordinates and
  raw user text cannot be added accidentally.
- A failed schema or request triggers one retry, then a safe template tied to
  the rule state.
- Demo signals are marked `is_demo: true` in the response and on the page.

The out-now hard floor, expiry window and rules tests are built in step 6. Until
then `rule_state` is hardcoded to `all_clear` for the demo scenario.
