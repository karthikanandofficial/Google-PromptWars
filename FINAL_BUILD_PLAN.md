# MonsoonSaathi — Final Architecture & Build Plan

> Hackathon window: 3 hours | Stack: Gemini-first, Firebase, FastAPI, Next.js 14

---

## 0. Problem Statement

Monsoon-prone Indian citizens and ward coordinators lack a single, phase-aware, multilingual tool that converts IMD weather alerts and citizen-reported conditions into personalized household action plans, real-time situational triage, and post-disaster government relief claim guidance — delivered over channels they already use.

---

## 1. System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                   CITIZEN / COORDINATOR                         │
│           WhatsApp (Twilio Sandbox)  │  Web Dashboard           │
└──────────────────┬───────────────────────────────┬─────────────┘
                   │                               │
                   ▼                               ▼
         ┌──────────────────┐         ┌────────────────────────┐
         │  Twilio Webhook   │         │  Next.js 14 Dashboard  │
         │  POST /webhook    │         │  /map  /triage  /relief│
         └────────┬─────────┘         └─────────────┬──────────┘
                  │                                 │
                  └───────────────┬─────────────────┘
                                  │ HTTP / SSE
                                  ▼
               ┌──────────────────────────────────────┐
               │           FastAPI Backend             │
               │                                      │
               │  ┌──────────────────────────────┐   │
               │  │       Phase Router            │   │
               │  │  (3-axis state machine)       │   │
               │  │  phase × risk_tier × hours    │   │
               │  └──────────────┬────────────────┘   │
               │                 │                    │
               │  ┌──────────────▼────────────────┐   │
               │  │        Planner Agent           │   │
               │  │  selects sub-agents + tools    │   │
               │  └──┬──┬───┬────┬────┬───────────┘   │
               │     │  │   │    │    │               │
               │  VulnAgent │ AlertAgent  CoordAgent  │
               │  PrepAgent │ ReliefAgent ReportAgent │
               │            │                        │
               │  ┌─────────▼──────────────────────┐ │
               │  │       Reviewer Agent            │ │
               │  │  validate → repair → confidence │ │
               │  └────────────────────────────────┘ │
               │                 │                   │
               │  ┌──────────────▼────────────────┐  │
               │  │      Response Cache (TTL)      │  │
               │  │  key: (pincode, phase, lang)   │  │
               │  └────────────────────────────────┘  │
               └──────────┬──────────────────────────┘
                          │
          ┌───────────────┼──────────────────┐
          ▼               ▼                  ▼
   Gemini 2.0 Flash  Firebase Firestore  NDMA GeoJSON
   (all LLM calls,   (sessions, reports, (flood zones,
    structured JSON)  real-time feed)     local file)
          │
          ▼
   IMD RSS Feed
   (live alerts,
    parsed per req)
  
```

### State Machine — Phase Router

```
ONBOARD → set language + pincode → READY
READY   → keyword match:
            PREPARE  → profile complete? → RUN_PLAN
                     → profile missing?  → COLLECT_PROFILE → RUN_PLAN
            ALERT    → IMD_FETCH → TRANSLATE → RESPOND
            REPORT   → INTAKE → STORE(Firestore) → ACK
            RELIEF   → LOSS_INTAKE → SCHEME_MATCH → RESPOND
            COORD    → AGGREGATE(pincode, 6h) → TRIAGE_BRIEF
          → free text → continue active flow
```

---

## 2. Tech Stack

| Layer | Choice | Justification |
|---|---|---|
| Frontend | Next.js 14 + TypeScript | App Router; SSE streaming support native |
| Backend/logic | FastAPI (Python, async) | Async agents; fast to wire; Twilio-compatible |
| AI | Gemini 2.0 Flash — structured JSON output | Cheapest fast model; `response_mime_type=JSON` |
| Google Service 1 | Gemini API | Every LLM call — planning, generation, translation |
| Google Service 2 | Firebase Firestore | Sessions, reports, real-time dashboard feed |
| State/data layer | Firebase Firestore | Persistent, real-time; shared backend+frontend |
| Caching | `cachetools.TTLCache` in-process | TTL 1800s plans, 300s alerts; zero infra overhead |
| Parallelism | `asyncio.gather` | VulnLookup + IMD fetch run concurrently pre-plan |
| Real data sources | IMD RSS (live), NDMA GeoJSON (bundled), Firestore (user), Gemini (AI output) | Nothing mocked or hardcoded |
| Auth | Firebase Google Sign-In (coordinator view) | Test creds shared with evaluators |
| Deployment | Cloud Run (backend), Vercel (frontend) | Push-to-deploy; free tier; both live |

---

## 3. Core Mechanism — Phase-Aware Household Intelligence Engine

### Variables driving behavior

| Variable | Source | Values |
|---|---|---|
| `phase` | Phase Router keyword | PREPARE / DURING / AFTER |
| `risk_tier` | NDMA GeoJSON lookup | HIGH / MEDIUM / LOW |
| `hours_until_event` | IMD alert timestamp | 0–72h |
| `language` | User-set in ONBOARD | en / hi / ta / te / kn / ml |
| `household_profile` | COLLECT_PROFILE flow | `{floor, dependents, transport, pincode}` |

### Discrete states and what changes

| State | Tone | Max words | Format | Vocabulary |
|---|---|---|---|---|
| PREPARE + HIGH + 48h | Calm, directive | 200 | Time-tagged (NOW / 6H / 24H) | Plain, specific |
| PREPARE + LOW + 48h | Informational | 120 | Single checklist | Relaxed |
| DURING + HIGH + ≤6h | Urgent, imperative | 80 | 3 numbered steps only | Short sentences |
| AFTER (any tier) | Empathetic, procedural | 300 | Scheme cards + draft text | Administrative |
| COORD (any tier) | Analytical | 150 | Priority-ranked table | Operational |

### System prompt template

```python
SYSTEM_TEMPLATE = """
You are MonsoonSaathi, a disaster preparedness assistant for India.

PHASE: {phase}
RISK TIER: {risk_tier} (historical flood data for pincode {pincode})
LANGUAGE: Respond entirely in {language}. Simple, clear vocabulary.
PROFILE: Floor {floor}, {dependents} dependents, transport: {transport}

PHASE RULES:
- PREPARE: Time-tagged plan. Sections: NOW / IN 6 HOURS / IN 24 HOURS.
  Be specific to floor level and transport. Max {max_words} words.
- DURING: 3 immediate steps only. Short sentences. Max 80 words.
- AFTER: Match schemes from context. Return: scheme name, eligibility reason,
  required documents, draft one-paragraph application. Max 300 words.
- COORD: Synthesize reports into CRITICAL/HIGH/MEDIUM priority actions with zone.
  Max 150 words.

CONTEXT (AFTER only): {scheme_rules}
REPORTS (COORD only): {aggregated_reports}

OUTPUT: Return valid JSON only:
{{
  "response_text": "...",
  "phase": "{phase}",
  "confidence": 0.0-1.0,
  "action_items": ["..."],
  "warnings": ["..."],
  "metadata": {{"word_count": int, "language": "{language}", "source": "live"}}
}}

If confidence < 0.5, explain in warnings[]. Never return free text outside this schema.
"""
```

The LLM never decides routing. Routing is deterministic. The LLM only sees a fully-specified prompt with no ambiguity left to resolve.

---

## 4. Stage-by-Stage Build Plan

### Stage 0 — Scaffold `(20 min)`

**Agent prompt:**
```
Create a monorepo with backend/ (FastAPI, Python 3.11) and frontend/ (Next.js 14, 
TypeScript, shadcn/ui, Tailwind, Framer Motion).

Backend folder structure:
  api/webhook.py          # Twilio POST handler
  api/routes.py           # REST endpoints for dashboard
  agents/planner.py       # Planner agent (routing logic)
  agents/vulnerability.py # GeoJSON flood zone lookup
  agents/prepare.py       # Preparedness plan agent
  agents/alert.py         # IMD alert + translation agent
  agents/report.py        # Report intake agent
  agents/relief.py        # Scheme matching agent
  agents/coordinator.py   # Triage synthesis agent
  agents/reviewer.py      # Output validator + repair loop
  prompts/templates.py    # SYSTEM_TEMPLATE + phase-specific variants
  services/gemini.py      # Gemini client wrapper, structured output
  services/firestore.py   # Session + report CRUD
  services/imd.py         # IMD RSS feed parser
  cache/response_cache.py # TTLCache keyed (pincode, phase, lang)
  data/flood_zones.geojson
  data/schemes.json       # NDRF/SDRF/PMFBY eligibility rules (public)
  data/imd_fallback.json  # Last-known IMD alerts (used only if RSS down)
  config.py               # Pydantic Settings from env vars
  main.py

Frontend folder structure:
  app/map/page.tsx         # Live reports heatmap
  app/triage/page.tsx      # Coordinator triage board
  app/relief/page.tsx      # Scheme lookup tool
  components/PhaseIndicator.tsx
  components/ReportFeed.tsx
  components/TriageBoard.tsx
  components/SchemeCard.tsx
  components/StreamingResponse.tsx
  components/WorkflowProgress.tsx
  lib/firestore.ts
  lib/api.ts

All secrets in .env (backend) and .env.local (frontend). Zero hardcoded values.
Install: google-generativeai firebase-admin fastapi uvicorn cachetools httpx 
         python-dotenv pydantic-settings
```

---

### Stage 1 — Core agents + Gemini integration `(40 min)`

**Agent prompt:**
```
Implement in backend/:

1. config.py — Pydantic Settings loading: GEMINI_API_KEY, TWILIO_AUTH_TOKEN,
   TWILIO_ACCOUNT_SID, FIREBASE_CREDENTIALS_PATH. Fail fast (raise) if any missing.

2. services/gemini.py — async call_gemini(system: str, user: str, schema: dict) -> dict
   Use response_mime_type='application/json' + response_schema. 
   Retry max 2x on JSON parse failure. Log retries. Return typed dict.

3. cache/response_cache.py — TTLCache from cachetools. Key: (pincode, phase, language).
   TTL: 1800s for PREPARE, 300s for ALERT. Expose get_cached, set_cached.

4. agents/vulnerability.py — Load flood_zones.geojson at startup (not per-request).
   get_risk_tier(pincode: str) -> RiskTier. District lookup, return HIGH/MEDIUM/LOW + 
   flood_frequency. Unknown pincode → MEDIUM + warning (never crash).

5. agents/prepare.py — async generate_plan(profile: HouseholdProfile, risk_tier: RiskTier,
   language: str) -> PreparednessPlan. Check cache first. Build prompt from SYSTEM_TEMPLATE
   phase=PREPARE. Call gemini. Pass through reviewer. Return structured plan.

6. agents/alert.py — async get_alert(pincode: str, language: str) -> AlertResponse.
   services/imd.py parses IMD RSS live. On RSS failure, load imd_fallback.json and set
   metadata.source='fallback'. Translate+simplify via Gemini. Cache 300s.

7. agents/relief.py — async match_schemes(loss_description: str, language: str) -> SchemeMatch.
   Load schemes.json as context string. Call Gemini with phase=AFTER + scheme_rules injected.
   Return: schemes[], documents_needed[], draft_application str.

8. agents/coordinator.py — async synthesize_triage(pincode: str, hours: int=6) -> TriageBrief.
   Fetch reports from Firestore for pincode+timewindow. Call Gemini with aggregated texts.
   Return priority-ranked action list with CRITICAL/HIGH/MEDIUM labels.

9. agents/reviewer.py — validate_and_repair(response: dict, schema: dict) -> dict.
   Check required fields exist. If confidence < 0.5, add to warnings[]. 
   If malformed JSON, retry once. Never return raw exception to caller.

All agents: TypedDict for inputs/outputs. All prompts from prompts/templates.py only.
```

---

### Stage 2 — Twilio webhook + phase router `(20 min)`

**Agent prompt:**
```
Implement api/webhook.py and router.py:

Phase Router (state machine per session):
- Load session from Firestore by SHA256-hashed phone number
- No session → ONBOARD: ask language preference, then pincode, save to Firestore
- Session exists → keyword detect: PREPARE / ALERT / REPORT / RELIEF / COORD
- Free text during active flow → continue that flow
- After every turn: save updated session state to Firestore

Webhook handler:
- POST /webhook — validate Twilio X-Twilio-Signature using TWILIO_AUTH_TOKEN
  Reject with 403 if invalid (use twilio.request_validator)
- Extract From, Body, MediaUrl from form data
- Sanitize Body: strip HTML tags, limit to 500 chars, reject empty
- Route to phase router → get structured response → extract response_text
- Return TwiML XML: <MessagingResponse><Message>{text}</Message></MessagingResponse>

Signature validation happens before any routing. No exceptions.
```

---

### Stage 3 — Next.js dashboard `(35 min)`

**Agent prompt:**
```
Build coordinator dashboard in frontend/ using shadcn/ui + Tailwind + Framer Motion.

Design tokens (CSS custom properties on :root):
  --bg: #0B1120        --bg-surface: #111827    --border: #1E293B
  --accent: #4F8EF7    --warn: #F59E0B          --success: #10B981
  --text-primary: #F8FAFC  --text-secondary: #94A3B8
  Light mode: --bg: #FAFBFF, --bg-surface: #F1F5F9, --border: #E2E8F0, etc.
  Font: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui

Page 1 — /map (Live Reports):
- SVG India outline with 6 pre-defined district zones (Ernakulam, Mumbai, 
  Guwahati, Bhubaneswar, Chennai, Bengaluru) as colored polygons
- Report count badge per zone from Firestore onSnapshot real-time listener
- Zone color intensity: 0 reports = transparent, 1-3 = amber, 4-10 = orange, 10+ = red
- Right panel: ReportFeed component — last 10 reports, timestamp, truncated text, pincode badge
- Skeleton loader while Firestore connects

Page 2 — /triage (Coordinator View):
- Pincode input (aria-label="Enter pincode") + "Generate Triage Brief" button
- On submit: POST /api/triage → SSE stream
- WorkflowProgress component: Fetching reports... → Analyzing... → Generating brief...
  Use Framer Motion staggered fade for each stage
- Results: TriageCard components with CRITICAL (red) / HIGH (amber) / MEDIUM (blue) badges
- Framer Motion stagger on card mount (0.1s delay each)

Page 3 — /relief (Scheme Lookup):
- Textarea: "Describe your loss in any language..." (aria-label set)
- Language selector: 6 options (English, Hindi, Tamil, Telugu, Kannada, Malayalam)
- Submit → POST /api/relief → SSE stream to StreamingResponse component
- SchemeCard per matched scheme: name, eligibility badge (green), document checklist, 
  copy button on draft application text (with success animation on copy)

All pages: dark mode first. ARIA labels on all interactive elements. 
Visible focus states (2px accent outline). Skeleton loaders. 
Tab order verified on /triage (input → language → button → results).
aria-live='polite' on all streaming output containers.
```

---

### Stage 4 — Integration + Firestore wiring `(20 min)`

**Agent prompt:**
```
Wire full integration:

1. services/firestore.py:
   save_session(phone_hash: str, session: UserSession) — upsert doc
   get_session(phone_hash: str) -> UserSession | None
   save_report(report: CitizenReport) — pincode, timestamp, text, phone_hash (SHA256)
   get_reports(pincode: str, hours: int) -> list[CitizenReport]
   Use firebase-admin with credentials from FIREBASE_CREDENTIALS_PATH env var.

2. api/routes.py FastAPI routes:
   POST /api/triage   body: {pincode: str, hours: int=6} → SSE stream coordinator agent
   POST /api/relief   body: {description: str, language: str} → SSE stream relief agent
   GET  /api/reports/{pincode} → last 6h reports for map page
   GET  /api/health   → {gemini: ok|error, firestore: ok|error} via live ping to both

3. frontend/lib/firestore.ts — Firestore client for /map using onSnapshot listener

4. FastAPI CORS middleware — allow Vercel frontend domain + localhost:3000

5. Create backend/scripts/seed_demo.py — writes 5 real-format reports to Firestore across
   pincodes 682001 (Ernakulam) and 400001 (Mumbai). Run once. Not part of app startup logic.
```

---

### Stage 5 — Rubric pass `(20 min)` — MANDATORY

**Agent prompt:**
```
Do not add features. Run the rubric pass only:

SECURITY:
- grep -r "AIza\|GOOG\|sk-\|twilio\|firebase" --include="*.py" --include="*.ts" . 
  Fix any match not in .env files.
- Confirm config.py raises on missing env vars (no silent None)
- Confirm Twilio signature validation active (not commented out)
- Add Pydantic field validators: description max 1000 chars, pincode is 6-digit numeric

ACCESSIBILITY (/triage page only — primary demo path):
- Add role='main' to main content container
- Confirm aria-label on pincode input and submit button
- Confirm aria-live='polite' on streaming output div
- Confirm tab order: input → language dropdown → button → results
- Verify focus ring visible (2px solid var(--accent)) on all interactive elements

TESTING — write in backend/tests/test_vulnerability.py:

  def test_high_risk_pincode_returns_high_tier():
      result = get_risk_tier('682001')  # Ernakulam — HIGH in NDMA data
      assert result.tier == RiskTier.HIGH
      assert result.flood_frequency > 0

  def test_unknown_pincode_defaults_to_medium_with_warning():
      result = get_risk_tier('999999')
      assert result.tier == RiskTier.MEDIUM
      assert len(result.warnings) > 0

Run: pytest backend/tests/ — confirm both pass before moving on.
```

---

### Stage 6 — Demo rehearsal `(15 min)`

Walk this exact path cold (no pre-warmed state, fresh session):

1. WhatsApp → send "HI" to Twilio sandbox → confirm language prompt returned
2. Select Malayalam → send pincode 682001 → confirm HIGH risk tier in response
3. Send "PREPARE" → complete 3 profile questions → confirm time-tagged Malayalam plan
4. Send "ALERT" → confirm response contains real IMD text (check `metadata.source`)
5. Send "REPORT water at knee level near junction" → confirm Firestore write
6. Browser → `/triage` → enter 682001 → confirm triage brief mentions the report above
7. Browser → `/relief` → describe loss → confirm real Gemini scheme match
8. Browser → `/map` → confirm the report submitted in step 5 appears in report feed

**Most likely failure point**: IMD RSS may be intermittent. Before pitching, hit `/api/alert?pincode=682001` and check `metadata.source`. If `fallback`, confirm the fallback text is clearly distinct from a live response and that the fallback source is logged server-side.

**Repeat as evaluator**: fresh session, pincode 400001, English, no prior state. Every feature must work cold.

**Total**: 20 + 40 + 20 + 35 + 20 + 20 + 15 = **170 min (2h 50min)**. 10 min buffer.

---

## 5. QA / Failure Checklist

1. **Cold flow is real**: Delete all Firestore test sessions. Send "HI" from a new number. Confirm onboarding, profile collection, and plan generation complete — no cached or canned text in any response.

2. **Google service round-trip**: `GET /api/health` must return `{gemini: ok, firestore: ok}` via live pings. If either fails, fix before submission — this is the Google Services axis.

3. **No secrets in source**: `grep -r "AIza\|GOOG\|firebase\|twilio\|sk-" --include="*.py" --include="*.ts" --include="*.tsx" .` — zero matches expected outside `.env` and `.env.local`.

4. **IMD source is real or fallback is labelled**: Re-hit `/api/alert` twice 5 minutes apart. Response should differ if IMD RSS updated. If RSS is down, `metadata.source` must say `fallback` — never `live` when serving cached file.

5. **Triage reflects real reports**: Add a unique report to Firestore for a test pincode. Hit `/api/triage` with that pincode. Confirm the triage brief explicitly references the report content — not a generic output that would appear even with an empty report set.

---

## 6. Cut List

| Feature | Why it's tempting | Why to cut |
|---|---|---|
| Voice note transcription (Whisper) | Improves low-literacy reach | Adds external paid API + 45min integration. Text input covers demo. |
| Google Maps interactive map | Looks impressive to judges | SVG heatmap delivers same information. Maps API not needed for Google Services score — Gemini + Firestore already cover it. |
| Multi-turn conversation memory (RAG) | Shows technical depth | Single-session Firestore state is sufficient for the demo. Full retrieval pipeline is 60+ min of work with marginal value. |

**Non-cuttable under any time pressure:**
- Gemini API integration — it is the Google Services axis. Faking with hardcoded text is a disqualification.
- Firebase Firestore real-time connection — same reason.
- The `test_vulnerability.py` unit tests — they are the Testing axis. An empty test file is not a test.

An unfinished real feature is safe. A finished fake feature is a disqualification.

---

## 7. Architectural Elegance Callout

"Every other solution in this room will call an LLM with the same generic monsoon safety prompt regardless of who's asking, when, or what the alert says. MonsoonSaathi's differentiator is not the WhatsApp integration or the multilingual support — it's the Phase-Aware Household Intelligence Engine in `agents/planner.py`. Before a single token is generated, the system determines risk tier from NDMA GeoJSON, household vulnerability from a 3-question profile, and urgency from the IMD alert's hours-until-event timestamp — then routes to a specialized agent with a purpose-built prompt schema. A HIGH-risk ground-floor household with 48 hours gets a calm 200-word multi-day plan in Malayalam. The same household with 6 hours left gets three imperative sentences and nothing else. The same household filing a claim the next morning gets a bureaucratic navigator that outputs a draft application they can copy-paste to a government portal. Same user. Same pincode. Three agents. Three schemas. The LLM is not doing the routing — the system is. The LLM only sees a fully-specified, ambiguity-free prompt. That's what separates orchestration from chatbot."

---

## 8. 60-Second Pitch Script

Every monsoon season, Indian families receive the same district-level IMD alert and have no idea what it means for *their* specific household.

We built MonsoonSaathi — a WhatsApp-native, multilingual assistant backed by a phase-aware AI orchestration engine that knows whether you're 48 hours before a flood, in the middle of one, or filing a relief claim the morning after.

The key mechanism: before any LLM call is made, the system determines your risk tier from NDMA flood data, your household vulnerability from three questions, and your urgency window from the current alert — then routes to a specialized agent with a purpose-built prompt. A high-risk family with 6 hours left doesn't get a checklist. They get three sentences.

Let me show you — I'll send a WhatsApp message right now and show the coordinator triage board update live.

With another 48 hours, we'd add voice input for low-literacy users and wire the coordinator dashboard into actual municipal ward networks via the district NIC portals.

---

## 9. Governance Deltas

Paste these into `governance_prompt.md` before priming the coding agent:

- **Google Service selected**: Gemini 2.0 Flash API — called in every agent (prepare, alert, relief, coordinator, reviewer); Firebase Firestore — called for session persistence, report storage, and real-time dashboard feed via `onSnapshot`
- **Efficiency approach**: In-process `cachetools.TTLCache` keyed on `(pincode, phase, language)` — 1800s TTL for preparedness plans, 300s for alerts; `asyncio.gather` runs VulnerabilityAgent + IMD fetch concurrently before plan generation; Reviewer only retries once to avoid double spend
- **Testing scope**: `test_high_risk_pincode_returns_high_tier` (known HIGH-risk Ernakulam pincode 682001 in NDMA dataset) + `test_unknown_pincode_defaults_to_medium_with_warning` (pincode not in GeoJSON → MEDIUM + non-empty warnings list)
- **Security scope**: All secrets loaded via Pydantic Settings from env vars; Twilio X-Twilio-Signature validated before routing; phone numbers stored as SHA256 hash in Firestore; all API inputs sanitized and capped (pincode: 6-digit numeric, description: ≤1000 chars); no `eval` or `dangerouslySetInnerHTML` anywhere
- **Real data sources**: IMD RSS feed (live parse per request, 300s cache); NDMA GeoJSON (bundled public domain, loaded at startup); Gemini 2.0 Flash (all AI output — zero hardcoded responses); Firebase Firestore (user-generated session + reports); NDRF/SDRF/PMFBY eligibility rules embedded as structured text from public NDMA documents in `schemes.json`; test coordinator credentials: `coord-demo@monsoon.dev / Demo2024!` — shared with evaluators, reaches /triage and /relief
