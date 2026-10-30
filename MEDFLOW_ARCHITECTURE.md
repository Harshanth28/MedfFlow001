# MedFlow — Architecture

> Neonatal hospital referral coordination **prototype**.
> All patient, hospital-capacity, specialist-availability and response-history data is **synthetic**.
> Real Bengaluru hospital names are used only as demonstration network references, not as claims of partnership or live availability.

Status: **Locked in Step 1 (2026-10-31).** Items marked *(open)* are decisions that need an input which did not exist at Step 1. They are resolved in the step named beside them, and must not be guessed earlier.

---

## 1. Overall system architecture

```
┌──────────────────────────────┐        HTTPS (JSON, Bearer JWT)       ┌───────────────────────────────────┐
│ Frontend (React + Vite SPA)  │ ─────────────────────────────────────▶│ Backend (Node.js + Express)       │
│ - role-aware shell           │                                       │ - auth middleware (verify JWT)    │
│ - referrer / receiver / admin│◀───────────────────────────────────── │ - role + hospital authorisation   │
│ - holds ONLY anon key + JWT  │                                       │ - modular REST routers            │
└──────────────────────────────┘                                       │ - services: matching, AI, ML,     │
            │ Supabase Auth (login only)                               │   workflow, reports, audit        │
            ▼                                                          └───────┬───────────────┬───────────┘
┌──────────────────────────────┐                                               │               │
│ Supabase Auth                │◀──────── verify JWT ───────────────────────────┘               │
└──────────────────────────────┘                                                               │
┌──────────────────────────────────────────────────────────────────────────────┐                │
│ Supabase PostgreSQL                                                          │◀───────────────┘
│ - core tables + supporting tables (§4)                                       │  user-scoped client (RLS)
│ - RLS policies (defence in depth)                                            │  + RPC workflow functions
│ - Postgres functions for transactional workflow (accept_offer, etc.)         │
│ Supabase Storage: private bucket `synthetic-reports`                         │
└──────────────────────────────────────────────────────────────────────────────┘
        Backend-only outbound:  Gemini API (@google/genai)   ·   ML model JSON artifact (local file)
        Offline:                Python training pipeline (pandas, scikit-learn) → model artifact
```

Principles:
- **One database.** Supabase PostgreSQL only. No SQLite or second store. (Step 1 found no SQLite code, so there is no migration conflict.)
- **The backend is the security boundary.** The frontend never receives the service-role key, the Gemini key or report storage URLs.
- **Hard constraints before scores.** Eligibility filtering always runs before distance, the Weighted Sum Model or ML.
- **No unnecessary infrastructure.** No microservices, no queues, no Redis. A single Express process with an in-process expiry sweeper.

## 2. Repository layout (target)

```
/backend        Express app (src/routes, src/services, src/middleware, src/lib), tests
/frontend       React + Vite SPA, tests
/ml             Python training pipeline, tests, model artifact output
/supabase       migrations/ (ordered SQL), seed/, policies
/data           synthetic datasets (baby_dataset.json, expected_requirements.json, …)
/docs           API, schema, ML, synthetic data, demo accounts
MEDFLOW_PROJECT_STATE.md · MEDFLOW_ARCHITECTURE.md · MEDFLOW_IMPLEMENTATION_LOG.md · README.md · .env.example
```

## 3. Frontend modules (Step 3 shell, Step 8 completion)

| Module | Role | Notes |
|---|---|---|
| Auth / login | all | Supabase Auth sign-in; JWT kept in memory/session storage, never the service key |
| App shell + role router | all | REFERRER → `/referrer`, RECEIVER → `/receiver`, ADMIN → `/admin`; loading, error and unauthorised states |
| Referrer dashboard | REFERRER | counts and recent activity from `/api/referrals` |
| Create referral wizard | REFERRER | code lookup → record preview → AI extraction → clinician review → matching |
| Matching results | REFERRER | ranked eligible list + exclusion reasons; simulated values labelled |
| Referral tracking | REFERRER | timeline of offers and responses, transfer status |
| Receiver dashboard + detail | RECEIVER | own hospital's offers only; accept / decline with reason |
| Transfer management | REFERRER, RECEIVER | coordination states (not ambulance tracking) |
| Secure report viewer | accepted RECEIVER | streams through `/api/transfers/:id/report` only |
| Admin | ADMIN | hospitals, users, capabilities, simulated capacity, audit log |
| ML information | all | model status, metrics, limitations; no accuracy marketing |

Frontend choice: **React + Vite.** No frontend existed at Step 1, so the "preserve existing frontend" rule has nothing to preserve. Eleven role-gated screens with shared state justify a component framework. Vite adds no runtime server. Styling uses plain CSS custom properties (navy/teal palette per Step 8), with no UI kit dependency.

## 4. Database structure

### 4.1 Core tables (names fixed by the specification)

| Table | Purpose in MedFlow | Mapping |
|---|---|---|
| `hospitals` | demo referral centre + receiving hospitals, coordinates, NICU level, active flag | `HOSP001` = fictional Demo Referral Centre |
| `babies` | 30 synthetic newborn records (raw clinical data only) | key = 5-digit `baby_code` |
| `hospital_equipment` | equipment per hospital (synthetic availability) | |
| `hospital_specialists` | specialist types per hospital (synthetic availability) | |
| `transfer_requests` | **the referral** (one per baby referral) | backs `/api/referrals` |
| `transfer_attempts` | **the offer** (one per receiving hospital per referral) | backs `/api/offers` |

Mapping `transfer_requests` → referral and `transfer_attempts` → offer avoids creating duplicate `referrals` / `offers` tables. API names and table names may differ deliberately.

Step 2 defined the columns in `supabase/migrations/20261031000100_core_schema.sql`. This is a **proposal**, tested on local PostgreSQL 16 but **not yet reconciled with the live Supabase schema**. See `supabase/SCHEMA_ASSUMPTIONS.md` (A1–A12). If the live tables differ, reconcile with additive `ALTER` migrations only.

Conventions: hospital operational columns are prefixed `sim_` (simulated). Wholly synthetic tables carry `is_synthetic boolean CHECK (is_synthetic)`. HOSP001 is the fictional referrer; HOSP002–HOSP008 are real Bengaluru hospital names with simulated operational profiles.

### 4.2 Supporting tables (created in Step 2 unless noted)

| Table | Purpose |
|---|---|
| `equipment_types`, `specialist_types` | catalogues giving EQ_*/FAC_*/SP_* identifiers real FKs. Care facilities (FAC_*) share `equipment_types` and `hospital_equipment` (category column) |
| `baby_expected_equipment`, `baby_expected_specialists` | junction tables for the expected profile |
| `hospital_users` (profile) — **Step 3** | maps `auth.users.id` → `hospital_id` + `role` (REFERRER / RECEIVER / ADMIN) |
| `baby_expected_requirements` | evaluation ground truth, **never** sent to Gemini or joined into AI input |
| `hospital_capacity` | synthetic beds by type: `total`, `occupied`, `reserved`, `checked_at`, `is_synthetic` |
| `ai_requirement_extractions` | raw AI draft, validation result, provider, model, reviewed values, reviewer, review time, method (AI / MANUAL) |
| `report_access_grants` | transfer → hospital grant with `expires_at`, `revoked_at` |
| `audit_logs` | actor, hospital, action, object type/id, timestamp, result |
| `transfers` | coordination lifecycle after acceptance (D3 resolved in Step 2: separate table, unique per referral and per accepted attempt) |

### 4.3 Integrity rules
- Partial unique index: at most one `ACCEPTED`/`CONFIRMED` attempt per `transfer_request`.
- Unique `(transfer_request_id, hospital_id)` on attempts, which prevents duplicate offers to one hospital.
- `CHECK` constraints on status enums and on `0 ≤ occupied + reserved ≤ total`.
- Every synthetic operational value carries `is_synthetic = true`, or lives in a table documented as wholly synthetic.

## 5. Backend modules

| Router | Step | Responsibility |
|---|---|---|
| `/api/auth` | 3 | session info, logout, login rate limiting (login itself goes via Supabase Auth) |
| `/api/users` | 3 | current user profile; admin user management |
| `/api/hospitals` | 3, 5 | hospital list (scoped); `POST /match` |
| `/api/babies` | 4 | `GET /:code` lookup (5-digit validation) |
| `/api/extractions` | 4 | run AI extraction, manual entry, clinician review/confirm |
| `/api/referrals` | 3, 6 | create referral, list, timeline |
| `/api/offers` | 3, 6 | receiver inbox, `POST /:offerId/respond` |
| `/api/transfers` | 3, 7 | lifecycle transitions, `GET /:id/report` |
| `/api/reports` | 3, 7 | grant management (create / revoke / renew) |
| `/api/admin` | 3, 8 | hospitals, capabilities, simulated capacity, audit log |

Services: `authz`, `babyRegistry`, `aiProvider` (interface) + `GeminiProvider` (+ future `OllamaProvider`), `extractionValidator` (schema validation), `eligibility`, `distance` (Haversine, replaceable), `ranking` (WSM), `responseDelayModel` (ML inference + fallback), `workflow` (state machines), `reports`, `audit`, `expirySweeper`.

Validation: request bodies are validated with a schema library (zod). AI output is validated with the same schemas.

## 6. AI integration (Step 4)

- `AIProvider.extractRequirements(rawRecordText) → ExtractionDraft`. The rest of the backend sees only `ExtractionDraft`, never a Gemini response type.
- `GeminiProvider` uses the official `@google/genai` SDK with a backend-only `GEMINI_API_KEY`. The model name comes from `GEMINI_MODEL` and is chosen in Step 4 against Google's current model list, not hard-coded from memory.
- Structured JSON output is requested, then validated with zod. Malformed or invalid output is stored as `FAILED_VALIDATION` and never auto-corrected.
- Input = raw synthetic clinical record + instructions only. `baby_expected_requirements` is never read by the AI path. A test asserts this.
- On failure: no invented results; manual entry is offered; `method = MANUAL` is recorded.
- Matching requires `review_status = CONFIRMED`. Any test bypass is env-gated (`DEMO_ALLOW_UNREVIEWED=false` by default) and labelled in the UI and audit log.

## 7. Hospital matching flow (Step 5, ML hook in Step 9)

```
approved requirements + source hospital
   → load active hospitals + equipment + specialists + capacity (fresh read, record checked_at)
   → HARD FILTER, each failure produces a human-readable reason:
        inactive · is source · NICU level < required · missing mandatory equipment
        · missing required specialist · no available suitable bed (total − occupied − reserved ≤ 0)
   → eligible set only:
        distance_km = Haversine(source, target)   [straight-line, not road distance or ETA]
        normalised criteria ∈ [0,1]: proximity, readiness, preferred-capability fit
        (+ Step 9: 1 − P(slow response), applied only to the eligible set)
        score = Σ wᵢ·cᵢ   (weights in config, documented)
   → ranked eligible list + full excluded list with reasons
```

Provisional starting weights (to be justified and documented in Step 5): proximity 0.40, readiness 0.30, preferred-capability fit 0.30. Step 9 re-balances to add response-speed. No score can rescue an ineligible hospital, and a test enforces this.

## 8. Referral workflow (Step 6) and transfer lifecycle (Step 7)

**Referral (`transfer_requests.status`):** `DRAFT → OPEN → CONFIRMED | NO_MATCH | CANCELLED`

**Offer (`transfer_attempts.status`):** `PENDING → ACCEPTED → CONFIRMED`, or `PENDING → REJECTED | EXPIRED | CANCELLED`

**Transfer:** `ACCEPTED → CONFIRMED → PREPARING → IN_TRANSIT → COMPLETED`, with `CANCELLED` from any non-terminal state. These are coordination states only, not ambulance tracking.

- Offers are **sequential**: one `PENDING` offer per referral at a time. Rejection or expiry creates the next offer to the next-ranked eligible hospital, after a capacity re-check.
- **Transactions run in Postgres functions** (called via Supabase RPC), because supabase-js cannot run multi-statement transactions. `respond_to_offer(offer_id, action, reason, actor)` locks the referral row (`SELECT … FOR UPDATE`), checks that the offer is `PENDING` and unexpired, re-checks capacity, increments `reserved`, creates the transfer and access grant, cancels any siblings, and writes the audit row, all in one transaction. The functions check the caller's hospital and role themselves.
- Idempotency: repeating a response to an already-decided offer returns the existing outcome and changes nothing.
- Expiry: an in-process sweeper calls idempotent `expire_due_offers()` every 30 s. Reads also treat past-deadline `PENDING` offers as expired. No external scheduler is needed.
- Demo (HOSP001 → baby 10482): HOSP002 must rank first and HOSP003 second through **genuine** seeded data. HOSP002's bed becomes unavailable through a real capacity update between offer and confirmation, so the decline happens through the real action. Nothing is pre-marked as accepted.
- Bed **reservation** (`reserved`) is kept separate from **occupancy** (`occupied`). Closing a transfer never frees a bed automatically.

## 9. ML integration (Step 9)

- Offline: `ml/train.py` (pandas, scikit-learn `LogisticRegression` in a `Pipeline` with scaling). Censored rows are excluded and their count reported. `GroupShuffleSplit` / `GroupKFold` split by `referral_id`, plus a chronological holdout. Leakage columns (`offer_id`, `referral_id`, `responded_at`, `response_minutes`, `offer_status`, target) are dropped by an explicit allow-list of features.
- Artifact: `ml/artifacts/response_delay_v{N}.json` contains feature order, scaler mean/scale, coefficients, intercept, threshold, data SHA-256, metrics and a timestamp.
- **Inference in Node with no Python runtime.** Logistic regression is `sigmoid(w·((x−μ)/σ) + b)`, so the backend computes it directly from the JSON. A parity test checks Node probabilities against scikit-learn's `predict_proba` on the holdout set.
- Fallback: if the artifact is missing or invalid, the service returns `{fallback: true}` and ranking proceeds without the ML term, with the fallback shown in the explanation.
- Operational prediction only. It is not clinical, and makes no reliability claim from synthetic data.

## 10. Security boundaries

| Boundary | Control |
|---|---|
| Browser ↔ backend | Supabase JWT verified on every request; CORS allow-list; `helmet`; JSON body size limits |
| Role / hospital scoping | backend authorisation middleware **and** RLS (`hospital_users` lookup on `auth.uid()`). Hidden buttons are never the control |
| Secrets | `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY` only in backend env; `.env` git-ignored; `.env.example` has no values |
| Login abuse | `express-rate-limit` on auth-adjacent routes; Supabase Auth's own limits |
| Two-stage data sharing | offers expose a configurable minimal payload (`OFFER_PAYLOAD_POLICY=demo|pseudonymous`); full record only after acceptance + valid grant |
| Reports | private bucket; backend streams bytes after authorisation; no public or long-lived URLs reach the client |
| Concurrency | row locks + partial unique indexes in Postgres functions |
| Audit | append-only `audit_logs` (no UPDATE/DELETE policy); no clinical text in application logs |

Not production: no independent security or privacy review, and no DPDP Act 2023 compliance work, since the prototype holds only synthetic data. This must be stated in the README.

## 11. External dependencies (target)

| Area | Dependency | Why |
|---|---|---|
| Backend | express, @supabase/supabase-js, @google/genai, zod, helmet, cors, express-rate-limit, dotenv | minimal stack named in the plan |
| Backend tests | vitest, supertest | unit + API tests |
| Frontend | react, react-dom, react-router, vite, @supabase/supabase-js (anon key, auth only) | SPA |
| E2E (Steps 8, 10) | @playwright/test | desktop + mobile journey tests |
| ML | python ≥3.10, pandas, scikit-learn, pytest | training only |
| Platform | Supabase project (Postgres, Auth, Storage), Gemini API key | |

Toolchain verified in the Step 1 sandbox: Node v22.23.4, scikit-learn 1.9.1, pandas 3.0.5. Package versions are pinned when each package is first installed.
