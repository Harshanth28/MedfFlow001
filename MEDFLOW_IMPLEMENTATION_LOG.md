# MedFlow — Implementation Log

Chronological record of work sessions. Newest entries at the bottom. Times are IST (UTC+05:30).

---

## 2026-10-31 · Step 1 — Existing project audit and final architecture

**Actions**
1. Received the 10-step master plan and the repository URL `https://github.com/Harshanth28/MedfFlow001.git`.
2. Tried to attach the repo with write access → failed: GitHub is not linked to this Claude account.
3. Cloned anonymously (public read) → git warned "cloned an empty repository".
4. Confirmed emptiness: `git log` (no commits), `git ls-remote origin` (no refs), file listing (no files).
5. Tried to reach the user's linked computer as an alternative source → bridge not connected (retried once).
6. User chose to proceed with Step 1 on the empty repository.
7. Checked the toolchain: Node v22.23.4, pandas 3.0.5, scikit-learn 1.9.1.
8. Checked the demo baby's age arithmetic: `date(2026,10,31) - date(2026,8,25)` = 67 days ✔.
9. Wrote `MEDFLOW_ARCHITECTURE.md`, `MEDFLOW_PROJECT_STATE.md` and this log.
10. Ran the ledger completeness check (all 10 step headings + acceptance criteria present).
11. Committed locally. **Not pushed** (no GitHub write access).

**Key decisions** (rationale in `MEDFLOW_ARCHITECTURE.md`)
- `transfer_requests` = referral, `transfer_attempts` = offer, which avoids duplicate tables.
- Workflow transactions run in Postgres functions called via RPC, because supabase-js has no multi-statement transactions.
- ML inference in Node from a JSON artifact (logistic regression parameters), so the backend needs no Python runtime.
- React + Vite frontend, since no frontend existed to preserve.
- Reports streamed through the backend; the client never receives storage URLs.
- Offer expiry via in-process sweeper + expire-on-read; no extra infrastructure.

**Problems found:** see Project State §1.4–1.5 (blocking inputs B1–B6, open decisions D1–D6).

**Next:** Step 2 is blocked until the Supabase project/schema (B1), the neonatal dataset specification (B2) and the original project specification (B3) are supplied.

---

## 2026-10-31 · Step 2 — Supabase database and complete synthetic dataset

**Inputs checked first:** project files, uploads and memory. The neonatal dataset specification file and the Supabase schema were **not** present; only the 10-step plan was attached. Proceeded on the facts stated in the Step 2 brief, recording the gaps rather than inventing them as "supplied".

**Actions**
1. Verified public facts for the 7 Bengaluru hospitals: names and addresses from official sites or Wikipedia; coordinates where a source gives them. Confirmed Rainbow's Electronic City facility through a Jan 2026 report.
2. Wrote the proposed migration (6 core tables, 2 catalogues, 8 supporting tables, constraints, indexes, append-only audit trigger, RLS deny-all).
3. Authored `data/condition_distribution.json` as PROVISIONAL (9 categories, 30 records).
4. Wrote 30 fictional clinical records with raw and expected data kept apart, plus the hospital network with public facts and `sim` profiles kept apart, plus a deterministic generator.
5. Generated all data files and both SQL seeds.
6. Wrote the file-level validator (257 checks). All passed on the first run, so ran a mutation check with 11 injected faults: all detected.
7. Wrote the DB test runner. It starts a throw-away PostgreSQL 16.15 cluster, applies the migration twice and the seeds twice, then runs the positive assertions and 16 negative constraint tests.
8. Verified that each "rejected as expected" came from the intended constraint, since the helper catches any error.
9. Updated the state ledger, the architecture (§4) and `supabase/SCHEMA_ASSUMPTIONS.md`.

**Decisions:** D1 (HOSP002 = Rainbow EC, HOSP003 = Chinmaya), D2 (HOSP001 fictional site near Electronic City) and D3 (separate `transfers` table) resolved. `hospital_users` deferred to Step 3.

**Failures fixed during the step:** none in the data. Process fix: `initdb` refuses to run as root, so the DB tests run as the unprivileged `claude` user.

**Open:** B1 (apply to live Supabase), B2 (real condition distribution), KIMS identity confirmation, B6 (GitHub push: RESOLVED).
