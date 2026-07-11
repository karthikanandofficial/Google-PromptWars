# MonsoonSaathi

A phase-aware, multilingual monsoon preparedness assistant for India. Built for the Google PromptWars hackathon.

**Live URLs**
- Frontend: https://frontend-three-plum-30.vercel.app
- Backend API: https://monsoon-saathi-api.vercel.app
- Health check: https://monsoon-saathi-api.vercel.app/api/health

---

## What It Does

Indian families receive district-level IMD weather alerts with no guidance on what it means for *their specific household*. MonsoonSaathi converts those alerts — and citizen-reported field conditions — into three distinct modes of help:

| Mode | When | What the user gets |
|---|---|---|
| **PREPARE** | 24–72h before a flood | Time-tagged household plan (NOW / IN 6H / IN 24H), in their language, tuned to their floor level and transport |
| **DURING** | Active event, ≤6h left | Three imperative sentences. Nothing else. |
| **AFTER** | Post-disaster | Matched government relief schemes (SDRF/NDRF/PMFBY) with a draft application they can copy-paste |

A coordinator triage board aggregates citizen reports across a pincode and generates a priority-ranked (CRITICAL / HIGH / MEDIUM) action brief for local ward officers.

---

## Architecture

```
Citizen / Coordinator
  │
  ├── WhatsApp (Twilio) ──────────────────────┐
  └── Web Dashboard (Next.js 14)              │
      /map  /triage  /relief                  │
                                              │ HTTP / SSE
                                              ▼
                              FastAPI Backend
                                    │
                          Phase-Aware Router
                          (risk tier × phase × hours)
                                    │
               ┌────────────────────┼────────────────────┐
               ▼                    ▼                    ▼
         PrepareAgent          AlertAgent           ReliefAgent
         CoordAgent            ReportAgent          ReviewerAgent
               │
               ├── Gemini 2.0 Flash (all LLM calls, structured JSON)
               ├── Firebase Firestore (sessions, reports, real-time feed)
               ├── NDMA GeoJSON (flood zone lookup, loaded at startup)
               └── IMD RSS Feed (live alert parsing, 300s cache)
```

### Phase-Aware Household Intelligence Engine

Before any LLM call, the system determines:
- **Risk tier** — from NDMA GeoJSON flood zone data (HIGH / MEDIUM / LOW)
- **Household vulnerability** — floor level, dependents, transport (3-question onboarding)
- **Urgency window** — hours until event from IMD alert timestamp

These three variables route to a specialized agent with a purpose-built prompt schema. The LLM never decides routing. Routing is deterministic.

| State | Tone | Max words | Format |
|---|---|---|---|
| PREPARE + HIGH + 48h | Calm, directive | 200 | Time-tagged (NOW / 6H / 24H) |
| DURING + HIGH + ≤6h | Urgent, imperative | 80 | 3 numbered steps only |
| AFTER (any tier) | Empathetic, procedural | 300 | Scheme cards + draft text |
| COORD (any tier) | Analytical | 150 | Priority-ranked table |

---

## Tech Stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind, Framer Motion, shadcn/ui |
| Backend | FastAPI (Python 3.11), async |
| AI | Gemini 2.0 Flash — structured JSON output via `response_mime_type=application/json` |
| Google Service 1 | Gemini API — every LLM call (prepare, alert, relief, triage, review) |
| Google Service 2 | Firebase Firestore — sessions, citizen reports, real-time dashboard feed |
| Caching | `cachetools.TTLCache` — 1800s for preparedness plans, 300s for alerts |
| Real data | IMD RSS feed (live), NDMA GeoJSON (bundled), Firestore (user-generated), NDRF/SDRF/PMFBY rules |
| WhatsApp | Twilio — webhook with X-Twilio-Signature validation |
| Deployment | Vercel (frontend + backend, free tier) |

---

## Project Structure

```
.
├── backend/
│   ├── agents/
│   │   ├── alert.py          # IMD alert fetch + Gemini translation
│   │   ├── coordinator.py    # Triage synthesis from citizen reports
│   │   ├── planner.py        # Phase state machine + intent routing
│   │   ├── prepare.py        # Household preparedness plan generator
│   │   ├── relief.py         # SDRF/NDRF/PMFBY scheme matcher
│   │   ├── report.py         # Citizen report intake
│   │   ├── reviewer.py       # Output validator + repair loop
│   │   └── vulnerability.py  # NDMA GeoJSON flood zone lookup
│   ├── api/
│   │   ├── routes.py         # REST + SSE endpoints
│   │   └── webhook.py        # Twilio POST handler
│   ├── data/
│   │   ├── flood_zones.geojson   # NDMA public flood zone data
│   │   ├── imd_fallback.json     # Last-known IMD alerts (RSS backup)
│   │   └── schemes.json          # NDRF/SDRF/PMFBY eligibility rules
│   ├── scripts/
│   │   └── seed_demo.py      # Seeds demo reports to Firestore
│   ├── services/
│   │   ├── firestore.py      # Session + report CRUD
│   │   ├── gemini.py         # Gemini client wrapper (google-genai SDK)
│   │   └── imd.py            # IMD RSS feed parser
│   ├── tests/
│   │   └── test_vulnerability.py
│   ├── config.py             # Pydantic Settings, fail-fast on missing vars
│   ├── main.py               # FastAPI app + CORS
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── map/page.tsx      # Live reports heatmap (SVG India + Firestore onSnapshot)
│   │   ├── triage/page.tsx   # Coordinator triage board (SSE streaming)
│   │   └── relief/page.tsx   # Scheme lookup tool (SSE streaming)
│   ├── components/
│   │   ├── WorkflowProgress.tsx
│   │   ├── SchemeCard.tsx
│   │   └── StreamingResponse.tsx
│   └── lib/
│       ├── api.ts            # SSE client for triage + relief
│       └── firestore.ts      # Firestore client for real-time map
├── api/
│   └── index.py              # Vercel Python runtime entry point
├── render.yaml               # Render deployment config (alternative)
├── vercel.json               # Vercel backend routing config
└── requirements.txt          # Root-level copy for Vercel build
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Service info |
| `GET` | `/api/health` | Live ping to Gemini + Firestore |
| `GET` | `/api/alert?pincode=&language=` | IMD alert, translated to target language |
| `GET` | `/api/reports/{pincode}?hours=6` | Citizen reports for a pincode |
| `POST` | `/api/triage` | SSE stream — coordinator triage brief |
| `POST` | `/api/relief` | SSE stream — matched relief schemes + draft application |
| `POST` | `/webhook` | Twilio WhatsApp webhook |

**Triage request body:**
```json
{ "pincode": "682001", "hours": 6 }
```

**Relief request body:**
```json
{ "description": "My house was destroyed in the flood", "language": "English" }
```

Both `/api/triage` and `/api/relief` return Server-Sent Events:
```
data: {"stage": "Fetching reports...", "done": false}
data: {"stage": "Analyzing...", "done": false}
data: {"stage": "Complete", "done": true, "result": {...}}
data: [DONE]
```

---

## Local Development

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Copy and fill in secrets
cp .env.example .env

# Run
uvicorn backend.main:app --reload --port 8000
```

**Required env vars** (`backend/.env`):
```
GEMINI_API_KEY=...
TWILIO_AUTH_TOKEN=...
TWILIO_ACCOUNT_SID=...
FIREBASE_CREDENTIALS_PATH=Firebase.json   # or FIREBASE_CREDENTIALS_JSON=<base64>
```

### Frontend

```bash
cd frontend
npm install

# Copy and fill in secrets
cp .env.local.example .env.local

# Run
npm run dev
```

**Required env vars** (`frontend/.env.local`):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FIREBASE_API_KEY=...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=...
NEXT_PUBLIC_FIREBASE_PROJECT_ID=...
```

### Seed demo data

```bash
python -m backend.scripts.seed_demo
```

Seeds 8 reports across Ernakulam (682001), Mumbai (400001), Guwahati (781001), and Bhubaneswar (751001).

### Run tests

```bash
pytest backend/tests/ -v
```

77 tests across 9 files, covering every backend module. External boundaries (Gemini, Firestore, IMD network) are mocked; internal logic is never mocked.

| Test file | Covers |
|---|---|
| `test_vulnerability.py` | NDMA GeoJSON risk tier lookup, unknown-pincode fallback |
| `test_planner.py` | Intent detection (incl. Hindi), language/pincode parsing, state machine routing |
| `test_reviewer.py` | Schema validation, field repair, low-confidence warnings, fallback responses |
| `test_response_cache.py` | TTL cache keying, case normalization, phase routing |
| `test_imd.py` | HTML extraction, fallback alerts, network-failure degradation |
| `test_prepare.py` | Profile injection into prompts, cache hits, risk-tier word budgets |
| `test_relief.py` | Scheme rules loading and injection, reviewer repair of partial output |
| `test_coordinator.py` | Report aggregation into prompts, empty-report short circuit |
| `test_routes.py` / `test_webhook.py` | Input validation (422s), SSE stream format, health checks, Twilio signature rejection, sanitization, phone hashing |

The suite runs without any `.env` file — `conftest.py` injects fake credentials, so no live service is touched.

---

## Supported Languages

English, Hindi, Tamil, Telugu, Kannada, Malayalam — all AI output is generated in the selected language via Gemini translation, not a lookup table.

---

## Demo Pincodes

| Pincode | District | Risk Tier | Reports seeded |
|---|---|---|---|
| 682001 | Ernakulam, Kerala | HIGH | 4 |
| 400001 | Mumbai, Maharashtra | HIGH | 2 |
| 781001 | Guwahati, Assam | HIGH | 1 |
| 751001 | Bhubaneswar, Odisha | HIGH | 1 |
| 560001 | Bengaluru, Karnataka | LOW | 0 |

---

## Security

- All secrets loaded via Pydantic Settings from environment variables — app fails fast on startup if any are missing
- Twilio `X-Twilio-Signature` validated before any webhook routing
- Phone numbers stored as SHA256 hashes in Firestore — never plaintext
- API inputs validated: pincode must be 6-digit numeric, description capped at 1000 chars
- Firebase credentials passed as base64-encoded JSON env var on Vercel (no file mounts needed)
- `.gitignore` excludes all secret files: `backend/.env`, `frontend/.env.local`, `Firebase.json`

---

## Google Services Used

1. **Gemini API** (`google-genai` SDK) — called in every agent. All LLM output is structured JSON via `response_mime_type=application/json`. Model: `gemini-2.0-flash` (falls back to `gemini-3.5-flash` on quota exhaustion).

2. **Firebase Firestore** — two collections:
   - `sessions/` — keyed by SHA256-hashed phone number, stores conversation state
   - `reports/` — citizen-submitted field reports, queried by pincode + time window; frontend subscribes via `onSnapshot` for real-time map updates
