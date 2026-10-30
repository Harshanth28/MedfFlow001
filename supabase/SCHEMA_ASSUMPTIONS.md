# Schema assumptions — Step 2 (UNVERIFIED against live Supabase)

The live Supabase schema was **not** available in Step 2. The migration in `supabase/migrations/` is a **proposal**. It has been executed and tested against a local PostgreSQL 16.15 server. It has **not** been run against the project's Supabase database.

Every statement uses `CREATE … IF NOT EXISTS`. Run against an existing database, it will **skip** any of the six core tables that already exist, rather than altering them. Therefore, **before applying it to Supabase**:

1. Export the live schema (`pg_dump --schema-only` or Supabase SQL editor).
2. Compare it against the assumptions below.
3. Convert any differences into additive `ALTER TABLE` migrations. Never drop or rename an existing column without a recorded justification.

| ID | Assumption | Why it matters | Verify by |
|---|---|---|---|
| A1 | The six core tables either do not exist yet, or have no conflicting columns | `IF NOT EXISTS` would silently keep an old, incompatible table | schema export |
| A2 | `hospitals.id` is text in the form `HOSP###` | spec and demo use HOSP001–HOSP003 | schema export |
| A3 | `babies` is keyed by the 5-digit code (`baby_code` text) | lookup `GET /api/babies/10482` | schema export |
| A4 | `transfer_requests` = referral and `transfer_attempts` = offer | avoids duplicate referral/offer tables | original specification (B3) |
| A5 | No existing rows in the six tables need preserving | seeds upsert by primary key and replace child rows for the 8 demo hospitals and 30 demo babies only | row counts on live DB |
| A6 | `gen_random_uuid()` available (PostgreSQL ≥ 13, as on Supabase) | UUID primary keys | Supabase version |
| A7 | NICU levels modelled 1–4, with level 4 = surgical/cardiac regional centre | matching compares integers | original specification (B3) |
| A8 | Bed types: `NICU_HDU`, `NICU_INTENSIVE`, `NICU_SURGICAL`, `NICU_CARDIAC` | capacity matching by bed type | original specification (B3) |
| A9 | Equipment and care facilities share one catalogue (`equipment_types.category`) and one hospital table (`hospital_equipment`) | keeps the six core tables unchanged | design review |
| A10 | `hospital_users` (auth.users ↔ hospital ↔ role) is created in Step 3 | depends on Supabase Auth users that do not exist yet | Step 3 |
| A11 | User-reference columns (`created_by`, `reviewed_by`, `responded_by`, `revoked_by`, `actor_user_id`) are plain `uuid`; FKs to `auth.users` are added in Step 3 | `auth` schema absent in local tests | Step 3 |
| A12 | RLS is enabled with **no policies** (deny-all for anon and authenticated roles; the service role bypasses) | secure default until Step 3 writes hospital-scoped policies | Step 3 |

## Tables added beyond the six core tables (and why)

| Table | Reason |
|---|---|
| `equipment_types`, `specialist_types` | Real foreign keys for equipment, facility and specialist identifiers |
| `hospital_capacity` | Synthetic beds with reservation kept separate from occupancy |
| `baby_expected_requirements`, `baby_expected_equipment`, `baby_expected_specialists` | Evaluation ground truth, physically separate from `babies` |
| `ai_requirement_extractions` | Step 4 draft/review records |
| `transfers` | Coordination lifecycle after acceptance. Resolves open decision D3: a separate table, so referral state and transfer state are not mixed |
| `report_access_grants` | Step 7 time-limited report access |
| `audit_logs` | Append-only audit trail; a trigger rejects UPDATE and DELETE |

## Constraints proved by `supabase/tests/run_db_tests.sh`

Age equals the reference date minus DOB · 5-digit codes · hospital FK · private report path only · catalogue FKs for equipment and specialists · `occupied + reserved ≤ total` · `is_synthetic` cannot be false · at most one PENDING offer per referral · at most one ACCEPTED/CONFIRMED offer per referral · one offer per hospital per referral · one active referral per baby · minimal payload cannot contain clinical fields · rejection reason only on REJECTED offers · audit log append-only.
