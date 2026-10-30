-- MedFlow Step 2 — database assertions. Run AFTER migrations + hospital_seed.sql + baby_seed.sql.
-- Every check raises an exception on failure; psql is run with ON_ERROR_STOP=1.
\set ON_ERROR_STOP 1

-- ------------------------------------------------------------- positive checks
DO $$
DECLARE n int; r record;
BEGIN
  SELECT count(*) INTO n FROM babies;                       IF n <> 30 THEN RAISE EXCEPTION 'babies count %', n; END IF;
  SELECT count(DISTINCT baby_code) INTO n FROM babies;      IF n <> 30 THEN RAISE EXCEPTION 'distinct codes %', n; END IF;
  SELECT count(*) INTO n FROM baby_expected_requirements;   IF n <> 30 THEN RAISE EXCEPTION 'expected count %', n; END IF;
  SELECT count(*) INTO n FROM hospitals;                    IF n <> 8  THEN RAISE EXCEPTION 'hospital count %', n; END IF;

  SELECT * INTO r FROM babies WHERE baby_code = '10482';
  IF r.full_name <> 'Aarav Kumar' OR r.date_of_birth <> DATE '2026-08-25'
     OR r.age_days_at_reference <> 67 OR (DATE '2026-10-31' - r.date_of_birth) <> 67
     OR r.birth_weight_g <> 1250 OR r.gestational_age_weeks <> 30 OR r.current_hospital_id <> 'HOSP001'
  THEN RAISE EXCEPTION 'Aarav record wrong: %', row_to_json(r); END IF;

  SELECT count(*) INTO n FROM babies WHERE age_days_at_reference <> reference_date - date_of_birth;
  IF n <> 0 THEN RAISE EXCEPTION '% babies with wrong age', n; END IF;

  -- every baby has >=1 specialist and >=1 equipment/facility expectation
  SELECT count(*) INTO n FROM babies b
   WHERE NOT EXISTS (SELECT 1 FROM baby_expected_specialists s WHERE s.baby_code = b.baby_code)
      OR NOT EXISTS (SELECT 1 FROM baby_expected_equipment e WHERE e.baby_code = b.baby_code);
  IF n <> 0 THEN RAISE EXCEPTION '% incomplete expected profiles', n; END IF;

  -- separation: babies table has no expected-requirement columns
  SELECT count(*) INTO n FROM information_schema.columns
   WHERE table_name = 'babies' AND column_name ~ '^(required_|expected_)';
  IF n <> 0 THEN RAISE EXCEPTION 'babies table contains expected-answer columns'; END IF;

  -- demo capacity preconditions
  SELECT total_beds - occupied_beds - reserved_beds INTO n FROM hospital_capacity
   WHERE hospital_id = 'HOSP002' AND bed_type = 'NICU_INTENSIVE';
  IF n <> 1 THEN RAISE EXCEPTION 'HOSP002 free intensive beds = %, expected 1', n; END IF;
  SELECT total_beds - occupied_beds - reserved_beds INTO n FROM hospital_capacity
   WHERE hospital_id = 'HOSP003' AND bed_type = 'NICU_INTENSIVE';
  IF n < 1 THEN RAISE EXCEPTION 'HOSP003 has no free intensive bed'; END IF;

  -- workflow tables start empty (demo must run through real actions)
  SELECT count(*) INTO n FROM transfer_requests; IF n <> 0 THEN RAISE EXCEPTION 'transfer_requests pre-seeded'; END IF;
  SELECT count(*) INTO n FROM transfer_attempts; IF n <> 0 THEN RAISE EXCEPTION 'transfer_attempts pre-seeded'; END IF;

  -- RLS enabled on every MedFlow table
  SELECT count(*) INTO n FROM pg_class c JOIN pg_namespace ns ON ns.oid = c.relnamespace
   WHERE ns.nspname = 'public' AND c.relkind = 'r' AND NOT c.relrowsecurity;
  IF n <> 0 THEN RAISE EXCEPTION '% tables without RLS', n; END IF;
  RAISE NOTICE 'positive checks: OK';
END $$;

-- ------------------------------------------------------------- constraint (negative) checks
-- Each block must FAIL inside; reaching the end means the constraint is missing.
CREATE OR REPLACE FUNCTION pg_temp.expect_fail(label text, stmt text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
  BEGIN
    EXECUTE stmt;
  EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'rejected as expected: % (%)', label, SQLERRM;
    RETURN;
  END;
  RAISE EXCEPTION 'constraint missing: % was accepted', label;
END $$;

BEGIN;
SELECT pg_temp.expect_fail('wrong age', $q$INSERT INTO babies (baby_code, full_name, sex, date_of_birth, age_days_at_reference, birth_weight_g, current_weight_g, gestational_age_weeks, medical_history, condition_summary, symptoms, clinical_notes, oxygen_support_mode, oxygen_fio2, oxygen_support_notes, current_care, current_hospital_id, transfer_reason, report_ref) VALUES ('99991','X','MALE','2026-10-01',5,3000,3000,39,'h','s',ARRAY['a'],'n','ROOM_AIR',0.21,'o','c','HOSP001','t','synthetic-reports/99991/a.pdf')$q$);
SELECT pg_temp.expect_fail('4-digit code', $q$INSERT INTO babies (baby_code, full_name, sex, date_of_birth, age_days_at_reference, birth_weight_g, current_weight_g, gestational_age_weeks, medical_history, condition_summary, symptoms, clinical_notes, oxygen_support_mode, oxygen_fio2, oxygen_support_notes, current_care, current_hospital_id, transfer_reason, report_ref) VALUES ('9999','X','MALE','2026-10-30',1,3000,3000,39,'h','s',ARRAY['a'],'n','ROOM_AIR',0.21,'o','c','HOSP001','t','synthetic-reports/99990/a.pdf')$q$);
SELECT pg_temp.expect_fail('unknown hospital FK', $q$UPDATE babies SET current_hospital_id = 'HOSP099' WHERE baby_code = '10482'$q$);
SELECT pg_temp.expect_fail('public report URL', $q$UPDATE babies SET report_ref = 'https://x/y.pdf' WHERE baby_code = '10482'$q$);
SELECT pg_temp.expect_fail('unknown equipment id', $q$INSERT INTO baby_expected_equipment VALUES ('10482','EQ_TELEPORTER')$q$);
SELECT pg_temp.expect_fail('unknown specialist id', $q$INSERT INTO baby_expected_specialists VALUES ('10482','SP_WIZARD')$q$);
SELECT pg_temp.expect_fail('over-booked capacity', $q$UPDATE hospital_capacity SET occupied_beds = 10, reserved_beds = 1 WHERE hospital_id = 'HOSP002' AND bed_type = 'NICU_INTENSIVE'$q$);
SELECT pg_temp.expect_fail('non-synthetic equipment row', $q$UPDATE hospital_equipment SET is_synthetic = false WHERE id = (SELECT min(id) FROM hospital_equipment)$q$);
ROLLBACK;

-- workflow constraints, using a throw-away referral inside a rolled-back transaction
BEGIN;
INSERT INTO transfer_requests (id, baby_code, source_hospital_id, approved_requirements, priority)
VALUES ('00000000-0000-0000-0000-000000000001', '10482', 'HOSP001', '{}'::jsonb, 'URGENT');
INSERT INTO transfer_attempts (transfer_request_id, hospital_id, sequence_no, minimal_payload, response_deadline)
VALUES ('00000000-0000-0000-0000-000000000001', 'HOSP002', 1, '{"baby_code":"10482"}', now() + interval '15 minutes');
SELECT pg_temp.expect_fail('second PENDING offer for same referral', $q$INSERT INTO transfer_attempts (transfer_request_id, hospital_id, sequence_no, minimal_payload, response_deadline) VALUES ('00000000-0000-0000-0000-000000000001','HOSP003',2,'{}', now() + interval '15 minutes')$q$);
SELECT pg_temp.expect_fail('payload containing clinical_notes', $q$INSERT INTO transfer_attempts (transfer_request_id, hospital_id, sequence_no, status, minimal_payload, response_deadline, responded_at) VALUES ('00000000-0000-0000-0000-000000000001','HOSP005',3,'REJECTED','{"clinical_notes":"x"}', now() + interval '15 minutes', now())$q$);
SELECT pg_temp.expect_fail('duplicate offer to same hospital', $q$INSERT INTO transfer_attempts (transfer_request_id, hospital_id, sequence_no, status, minimal_payload, response_deadline, responded_at) VALUES ('00000000-0000-0000-0000-000000000001','HOSP002',4,'REJECTED','{}', now() + interval '15 minutes', now())$q$);
SELECT pg_temp.expect_fail('second active referral for baby', $q$INSERT INTO transfer_requests (baby_code, source_hospital_id, approved_requirements, priority) VALUES ('10482','HOSP001','{}','URGENT')$q$);
SELECT pg_temp.expect_fail('rejection reason on a PENDING offer', $q$UPDATE transfer_attempts SET rejection_reason = 'x' WHERE sequence_no = 1$q$);
-- move offer 1 to REJECTED legitimately, then try two ACCEPTED offers
UPDATE transfer_attempts SET status = 'REJECTED', responded_at = now(), rejection_reason = 'NICU bed unavailable at confirmation time' WHERE sequence_no = 1;
INSERT INTO transfer_attempts (transfer_request_id, hospital_id, sequence_no, status, minimal_payload, response_deadline, responded_at)
VALUES ('00000000-0000-0000-0000-000000000001', 'HOSP003', 2, 'ACCEPTED', '{}', now() + interval '15 minutes', now());
SELECT pg_temp.expect_fail('two ACCEPTED offers for one referral', $q$INSERT INTO transfer_attempts (transfer_request_id, hospital_id, sequence_no, status, minimal_payload, response_deadline, responded_at) VALUES ('00000000-0000-0000-0000-000000000001','HOSP005',3,'ACCEPTED','{}', now() + interval '15 minutes', now())$q$);
INSERT INTO audit_logs (action, object_type, object_id, result) VALUES ('TEST', 'test', '1', 'SUCCESS');
SELECT pg_temp.expect_fail('audit log UPDATE', $q$UPDATE audit_logs SET result = 'FAILED'$q$);
SELECT pg_temp.expect_fail('audit log DELETE', $q$DELETE FROM audit_logs$q$);
ROLLBACK;

SELECT 'ALL DATABASE ASSERTIONS PASSED' AS result;
