-- =====================================================================
-- MedFlow · Step 2 · Migration 0001 — core schema
-- STATUS: PROPOSED. Written WITHOUT access to the live Supabase schema.
-- Every CREATE uses IF NOT EXISTS so that, if the six core tables already
-- exist in Supabase, this file does not drop or replace them. In that case
-- the column-level differences must be reconciled first — see
-- supabase/SCHEMA_ASSUMPTIONS.md (assumptions A1–A12).
--
-- Conventions
--   * All patient data is SYNTHETIC (babies.is_synthetic is forced TRUE).
--   * Hospital columns prefixed `sim_` are SIMULATED operational values.
--   * Tables documented as "wholly synthetic" carry is_synthetic = TRUE
--     enforced by a CHECK constraint.
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- Reference catalogues (justification: give equipment / specialist /
-- facility identifiers real foreign keys instead of free text)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS equipment_types (
    code        text PRIMARY KEY CHECK (code ~ '^(EQ|FAC)_[A-Z0-9_]+$'),
    name        text NOT NULL,
    category    text NOT NULL CHECK (category IN ('EQUIPMENT', 'FACILITY')),
    description text NOT NULL,
    CHECK ((category = 'EQUIPMENT' AND code LIKE 'EQ\_%')
        OR (category = 'FACILITY'  AND code LIKE 'FAC\_%'))
);
COMMENT ON TABLE equipment_types IS
  'Catalogue of equipment (EQ_*) and care facilities (FAC_*) used for matching.';

CREATE TABLE IF NOT EXISTS specialist_types (
    code        text PRIMARY KEY CHECK (code ~ '^SP_[A-Z0-9_]+$'),
    name        text NOT NULL,
    description text NOT NULL
);

-- ---------------------------------------------------------------------
-- 1. hospitals
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hospitals (
    id                   text PRIMARY KEY CHECK (id ~ '^HOSP[0-9]{3}$'),
    name                 text NOT NULL UNIQUE,
    short_name           text NOT NULL,
    is_fictional         boolean NOT NULL,
    -- Public facts (verified or approximate — see coordinate_quality and
    -- data/hospital_sources.json). Not synthetic.
    locality             text NOT NULL,
    address              text,
    latitude             numeric(9,6) NOT NULL CHECK (latitude  BETWEEN -90  AND 90),
    longitude            numeric(9,6) NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    coordinate_quality   text NOT NULL CHECK (coordinate_quality IN
                          ('SOURCED', 'PROXY_SOURCED', 'APPROXIMATE_LOCALITY', 'FICTIONAL')),
    -- Demo-network flags (system configuration, not a claim about the hospital)
    is_active            boolean NOT NULL DEFAULT true,
    can_refer            boolean NOT NULL DEFAULT false,
    can_receive          boolean NOT NULL DEFAULT true,
    -- SIMULATED operational values
    sim_nicu_level       smallint NOT NULL CHECK (sim_nicu_level BETWEEN 1 AND 4),
    sim_readiness_score  numeric(3,2) NOT NULL CHECK (sim_readiness_score BETWEEN 0 AND 1),
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);
COMMENT ON COLUMN hospitals.sim_nicu_level IS
  'SIMULATED. Not the hospital''s real NICU level. Demo value only.';
COMMENT ON COLUMN hospitals.sim_readiness_score IS
  'SIMULATED operational readiness 0–1. Demo value only.';

-- ---------------------------------------------------------------------
-- 2. hospital_equipment  (wholly synthetic; holds EQ_* and FAC_* codes)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hospital_equipment (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    hospital_id     text NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
    equipment_code  text NOT NULL REFERENCES equipment_types(code),
    quantity        smallint NOT NULL DEFAULT 1 CHECK (quantity >= 0),
    sim_available   boolean NOT NULL DEFAULT true,
    sim_note        text,
    is_synthetic    boolean NOT NULL DEFAULT true CHECK (is_synthetic),
    UNIQUE (hospital_id, equipment_code)
);

-- ---------------------------------------------------------------------
-- 3. hospital_specialists  (wholly synthetic)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hospital_specialists (
    id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    hospital_id      text NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
    specialist_code  text NOT NULL REFERENCES specialist_types(code),
    sim_count        smallint NOT NULL DEFAULT 1 CHECK (sim_count >= 0),
    sim_on_call_24x7 boolean NOT NULL DEFAULT true,
    is_synthetic     boolean NOT NULL DEFAULT true CHECK (is_synthetic),
    UNIQUE (hospital_id, specialist_code)
);

-- ---------------------------------------------------------------------
-- Supporting: hospital_capacity  (wholly synthetic)
-- Reservation and occupancy are separate columns (architecture §8).
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hospital_capacity (
    id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    hospital_id    text NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
    bed_type       text NOT NULL CHECK (bed_type IN
                    ('NICU_HDU', 'NICU_INTENSIVE', 'NICU_SURGICAL', 'NICU_CARDIAC')),
    total_beds     smallint NOT NULL CHECK (total_beds >= 0),
    occupied_beds  smallint NOT NULL CHECK (occupied_beds >= 0),
    reserved_beds  smallint NOT NULL DEFAULT 0 CHECK (reserved_beds >= 0),
    checked_at     timestamptz NOT NULL DEFAULT now(),
    is_synthetic   boolean NOT NULL DEFAULT true CHECK (is_synthetic),
    UNIQUE (hospital_id, bed_type),
    CHECK (occupied_beds + reserved_beds <= total_beds)
);
COMMENT ON TABLE hospital_capacity IS
  'SIMULATED bed capacity. Never live bed availability.';

-- ---------------------------------------------------------------------
-- 4. babies  (raw synthetic clinical record ONLY — no expected answers)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS babies (
    baby_code              text PRIMARY KEY CHECK (baby_code ~ '^[1-9][0-9]{4}$'),
    full_name              text NOT NULL,
    sex                    text NOT NULL CHECK (sex IN ('MALE', 'FEMALE')),
    date_of_birth          date NOT NULL,
    reference_date         date NOT NULL DEFAULT DATE '2026-10-31',
    age_days_at_reference  integer NOT NULL,
    birth_weight_g         integer NOT NULL CHECK (birth_weight_g BETWEEN 400 AND 5500),
    current_weight_g       integer NOT NULL CHECK (current_weight_g BETWEEN 400 AND 7000),
    gestational_age_weeks  smallint NOT NULL CHECK (gestational_age_weeks BETWEEN 22 AND 42),
    gestational_age_days   smallint NOT NULL DEFAULT 0 CHECK (gestational_age_days BETWEEN 0 AND 6),
    medical_history        text NOT NULL,
    condition_summary      text NOT NULL,
    symptoms               text[] NOT NULL CHECK (cardinality(symptoms) > 0),
    clinical_notes         text NOT NULL,
    oxygen_support_mode    text NOT NULL CHECK (oxygen_support_mode IN
                            ('ROOM_AIR', 'NASAL_CANNULA', 'HFNC', 'CPAP',
                             'CONVENTIONAL_VENTILATION', 'HFOV')),
    oxygen_fio2            numeric(3,2) NOT NULL CHECK (oxygen_fio2 BETWEEN 0.21 AND 1.00),
    oxygen_flow_lpm        numeric(4,1) CHECK (oxygen_flow_lpm IS NULL OR oxygen_flow_lpm > 0),
    oxygen_support_notes   text NOT NULL,
    current_care           text NOT NULL,
    current_hospital_id    text NOT NULL REFERENCES hospitals(id),
    transfer_reason        text NOT NULL,
    report_ref             text NOT NULL UNIQUE
                            CHECK (report_ref ~ '^synthetic-reports/[0-9]{5}/[a-z0-9_]+\.pdf$'),
    is_synthetic           boolean NOT NULL DEFAULT true CHECK (is_synthetic),
    created_at             timestamptz NOT NULL DEFAULT now(),
    CHECK (date_of_birth <= reference_date),
    CHECK (age_days_at_reference = reference_date - date_of_birth),
    CHECK (oxygen_support_mode <> 'ROOM_AIR' OR (oxygen_fio2 = 0.21 AND oxygen_flow_lpm IS NULL))
);
COMMENT ON TABLE babies IS
  'SYNTHETIC newborn records. Fictional people. Expected requirements live in baby_expected_requirements and must never be joined into AI input.';
COMMENT ON COLUMN babies.report_ref IS
  'Object path in the PRIVATE Supabase Storage bucket. Never a public URL.';

-- ---------------------------------------------------------------------
-- Supporting: expected requirement profiles (evaluation ground truth)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS baby_expected_requirements (
    baby_code             text PRIMARY KEY REFERENCES babies(baby_code) ON DELETE CASCADE,
    required_nicu_level   smallint NOT NULL CHECK (required_nicu_level BETWEEN 1 AND 4),
    required_bed_type     text NOT NULL CHECK (required_bed_type IN
                           ('NICU_HDU', 'NICU_INTENSIVE', 'NICU_SURGICAL', 'NICU_CARDIAC')),
    expected_priority     text NOT NULL CHECK (expected_priority IN
                           ('EMERGENCY', 'URGENT', 'SEMI_URGENT')),
    is_synthetic          boolean NOT NULL DEFAULT true CHECK (is_synthetic)
);
COMMENT ON TABLE baby_expected_requirements IS
  'EVALUATION ONLY. Never sent to the AI provider. Never shown as the extraction result.';

CREATE TABLE IF NOT EXISTS baby_expected_equipment (
    baby_code       text NOT NULL REFERENCES baby_expected_requirements(baby_code) ON DELETE CASCADE,
    equipment_code  text NOT NULL REFERENCES equipment_types(code),
    PRIMARY KEY (baby_code, equipment_code)
);
COMMENT ON TABLE baby_expected_equipment IS
  'Expected equipment (EQ_*) and care facilities (FAC_*); category from equipment_types.';

CREATE TABLE IF NOT EXISTS baby_expected_specialists (
    baby_code        text NOT NULL REFERENCES baby_expected_requirements(baby_code) ON DELETE CASCADE,
    specialist_code  text NOT NULL REFERENCES specialist_types(code),
    PRIMARY KEY (baby_code, specialist_code)
);

-- ---------------------------------------------------------------------
-- Supporting: AI requirement extractions (populated from Step 4)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ai_requirement_extractions (
    id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    baby_code          text NOT NULL REFERENCES babies(baby_code),
    method             text NOT NULL CHECK (method IN ('AI', 'MANUAL')),
    provider           text,
    model              text,
    raw_output         jsonb,
    validation_status  text NOT NULL CHECK (validation_status IN
                        ('VALID', 'FAILED_VALIDATION', 'PROVIDER_ERROR', 'NOT_APPLICABLE')),
    validation_errors  jsonb,
    draft_requirements jsonb,
    approved_requirements jsonb,
    review_status      text NOT NULL DEFAULT 'PENDING_REVIEW'
                        CHECK (review_status IN ('PENDING_REVIEW', 'CONFIRMED', 'REJECTED')),
    reviewed_by        uuid,   -- auth.users.id; FK added in Step 3
    reviewed_at        timestamptz,
    created_by         uuid,   -- auth.users.id; FK added in Step 3
    created_at         timestamptz NOT NULL DEFAULT now(),
    CHECK (method = 'AI' OR provider IS NULL),
    CHECK (review_status <> 'CONFIRMED'
           OR (approved_requirements IS NOT NULL AND reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL))
);

-- ---------------------------------------------------------------------
-- 5. transfer_requests  (= the REFERRAL; backs /api/referrals)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transfer_requests (
    id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    baby_code               text NOT NULL REFERENCES babies(baby_code),
    source_hospital_id      text NOT NULL REFERENCES hospitals(id),
    extraction_id           uuid REFERENCES ai_requirement_extractions(id),
    approved_requirements   jsonb NOT NULL,
    priority                text NOT NULL CHECK (priority IN ('EMERGENCY', 'URGENT', 'SEMI_URGENT')),
    status                  text NOT NULL DEFAULT 'OPEN'
                             CHECK (status IN ('DRAFT', 'OPEN', 'CONFIRMED', 'NO_MATCH', 'CANCELLED')),
    payload_policy          text NOT NULL DEFAULT 'demo' CHECK (payload_policy IN ('demo', 'pseudonymous')),
    created_by              uuid,   -- FK to auth.users in Step 3
    created_at              timestamptz NOT NULL DEFAULT now(),
    updated_at              timestamptz NOT NULL DEFAULT now(),
    closed_at               timestamptz,
    CHECK ((status IN ('CONFIRMED', 'NO_MATCH', 'CANCELLED')) = (closed_at IS NOT NULL))
);
-- One active referral per baby at a time
CREATE UNIQUE INDEX IF NOT EXISTS ux_transfer_requests_active_baby
    ON transfer_requests (baby_code) WHERE status IN ('DRAFT', 'OPEN');

-- ---------------------------------------------------------------------
-- 6. transfer_attempts  (= the OFFER; backs /api/offers)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transfer_attempts (
    id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    transfer_request_id  uuid NOT NULL REFERENCES transfer_requests(id) ON DELETE CASCADE,
    hospital_id          text NOT NULL REFERENCES hospitals(id),
    sequence_no          smallint NOT NULL CHECK (sequence_no >= 1),
    status               text NOT NULL DEFAULT 'PENDING'
                          CHECK (status IN ('PENDING', 'ACCEPTED', 'REJECTED',
                                            'EXPIRED', 'CANCELLED', 'CONFIRMED')),
    minimal_payload      jsonb NOT NULL,
    match_snapshot       jsonb,
    offered_at           timestamptz NOT NULL DEFAULT now(),
    response_deadline    timestamptz NOT NULL,
    responded_at         timestamptz,
    responded_by         uuid,      -- FK to auth.users in Step 3
    rejection_reason     text,
    CHECK (response_deadline > offered_at),
    CHECK (status NOT IN ('ACCEPTED', 'REJECTED', 'CONFIRMED') OR responded_at IS NOT NULL),
    CHECK (status <> 'PENDING' OR responded_at IS NULL),
    CHECK (rejection_reason IS NULL OR status = 'REJECTED'),
    -- minimal payload must never carry clinical narrative
    CHECK (NOT (minimal_payload ?| ARRAY['clinical_notes', 'medical_history',
                                          'symptoms', 'condition_summary', 'report_ref'])),
    UNIQUE (transfer_request_id, hospital_id),
    UNIQUE (transfer_request_id, sequence_no)
);
-- Sequential escalation: at most one PENDING offer per referral
CREATE UNIQUE INDEX IF NOT EXISTS ux_attempts_one_pending
    ON transfer_attempts (transfer_request_id) WHERE status = 'PENDING';
-- Concurrency guard: at most one accepted/confirmed offer per referral
CREATE UNIQUE INDEX IF NOT EXISTS ux_attempts_one_accepted
    ON transfer_attempts (transfer_request_id) WHERE status IN ('ACCEPTED', 'CONFIRMED');
CREATE INDEX IF NOT EXISTS ix_attempts_hospital_status
    ON transfer_attempts (hospital_id, status);
CREATE INDEX IF NOT EXISTS ix_attempts_pending_deadline
    ON transfer_attempts (response_deadline) WHERE status = 'PENDING';

-- ---------------------------------------------------------------------
-- Supporting: transfers (coordination lifecycle after acceptance; D3)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transfers (
    id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    transfer_request_id   uuid NOT NULL UNIQUE REFERENCES transfer_requests(id),
    accepted_attempt_id   uuid NOT NULL UNIQUE REFERENCES transfer_attempts(id),
    receiving_hospital_id text NOT NULL REFERENCES hospitals(id),
    reserved_bed_type     text NOT NULL CHECK (reserved_bed_type IN
                           ('NICU_HDU', 'NICU_INTENSIVE', 'NICU_SURGICAL', 'NICU_CARDIAC')),
    status                text NOT NULL DEFAULT 'ACCEPTED' CHECK (status IN
                           ('ACCEPTED', 'CONFIRMED', 'PREPARING', 'IN_TRANSIT', 'COMPLETED', 'CANCELLED')),
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now(),
    closed_at             timestamptz,
    CHECK ((status IN ('COMPLETED', 'CANCELLED')) = (closed_at IS NOT NULL))
);
COMMENT ON TABLE transfers IS
  'Demonstration coordination states only. Not ambulance tracking.';

-- ---------------------------------------------------------------------
-- Supporting: report access grants (populated from Step 7)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS report_access_grants (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    transfer_id   uuid NOT NULL REFERENCES transfers(id) ON DELETE CASCADE,
    hospital_id   text NOT NULL REFERENCES hospitals(id),
    granted_at    timestamptz NOT NULL DEFAULT now(),
    expires_at    timestamptz NOT NULL,
    revoked_at    timestamptz,
    revoked_by    uuid,
    revoke_reason text,
    CHECK (expires_at > granted_at),
    CHECK (revoked_at IS NULL OR revoked_at >= granted_at)
);
CREATE INDEX IF NOT EXISTS ix_grants_transfer_hospital
    ON report_access_grants (transfer_id, hospital_id);

-- ---------------------------------------------------------------------
-- Supporting: audit_logs (append-only; enforced by trigger below)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    occurred_at   timestamptz NOT NULL DEFAULT now(),
    actor_user_id uuid,
    actor_hospital_id text REFERENCES hospitals(id),
    action        text NOT NULL,
    object_type   text NOT NULL,
    object_id     text,
    result        text NOT NULL CHECK (result IN ('SUCCESS', 'DENIED', 'FAILED')),
    details       jsonb
);
CREATE INDEX IF NOT EXISTS ix_audit_object ON audit_logs (object_type, object_id);
CREATE INDEX IF NOT EXISTS ix_audit_time   ON audit_logs (occurred_at);

CREATE OR REPLACE FUNCTION audit_logs_append_only() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'audit_logs is append-only (% not allowed)', TG_OP;
END $$;

DROP TRIGGER IF EXISTS trg_audit_logs_append_only ON audit_logs;
CREATE TRIGGER trg_audit_logs_append_only
    BEFORE UPDATE OR DELETE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION audit_logs_append_only();

-- ---------------------------------------------------------------------
-- Row Level Security: ENABLED, NO POLICIES (deny-all for anon and
-- authenticated roles). The backend's service role bypasses RLS.
-- Hospital-scoped policies are written in Step 3.
-- ---------------------------------------------------------------------
ALTER TABLE equipment_types            ENABLE ROW LEVEL SECURITY;
ALTER TABLE specialist_types           ENABLE ROW LEVEL SECURITY;
ALTER TABLE hospitals                  ENABLE ROW LEVEL SECURITY;
ALTER TABLE hospital_equipment         ENABLE ROW LEVEL SECURITY;
ALTER TABLE hospital_specialists       ENABLE ROW LEVEL SECURITY;
ALTER TABLE hospital_capacity          ENABLE ROW LEVEL SECURITY;
ALTER TABLE babies                     ENABLE ROW LEVEL SECURITY;
ALTER TABLE baby_expected_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE baby_expected_equipment    ENABLE ROW LEVEL SECURITY;
ALTER TABLE baby_expected_specialists  ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_requirement_extractions ENABLE ROW LEVEL SECURITY;
ALTER TABLE transfer_requests          ENABLE ROW LEVEL SECURITY;
ALTER TABLE transfer_attempts          ENABLE ROW LEVEL SECURITY;
ALTER TABLE transfers                  ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_access_grants       ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs                 ENABLE ROW LEVEL SECURITY;

COMMIT;
