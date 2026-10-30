"""
Step 2 data validation — file-level checks (no database needed).

    python3 -m pytest data/tests -q
"""
import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[1]
REF = date(2026, 10, 31)


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


BABIES = load("baby_dataset.json")["babies"]
EXPECTED = load("expected_requirements.json")["expected_requirements"]
EXP = {e["baby_code"]: e for e in EXPECTED}
NET = load("bengaluru_hospitals.json")["hospitals"]
HOSP = {h["id"]: h for h in NET}
SRC = {h["id"]: h for h in load("hospital_sources.json")["hospitals"]}
SCEN = load("demo_transfer_scenario.json")
DIST = load("condition_distribution.json")

sys.path.insert(0, str(DATA / "generator"))
from network import EQUIPMENT_TYPES, SPECIALIST_TYPES  # noqa: E402

EQ = {c for c, _, cat, _ in EQUIPMENT_TYPES if cat == "EQUIPMENT"}
FAC = {c for c, _, cat, _ in EQUIPMENT_TYPES if cat == "FACILITY"}
SP = {c for c, _, _ in SPECIALIST_TYPES}
RAW_TEXT_FIELDS = ["medical_history", "condition_summary", "clinical_notes", "current_care", "transfer_reason"]
EXPECTED_KEYS = {"required_nicu_level", "required_bed_type", "required_equipment",
                 "required_care_facilities", "required_specialists", "expected_priority", "condition_category"}


def raw_text(b):
    return " ".join([b[f] for f in RAW_TEXT_FIELDS] + b["symptoms"] + [b["oxygen_support"]["notes"]])


# ------------------------------------------------------------ counts & identifiers
def test_exactly_30_records():
    assert len(BABIES) == 30 and len(EXPECTED) == 30
    assert load("baby_dataset.json")["count"] == 30


def test_codes_unique_five_digit():
    codes = [b["baby_code"] for b in BABIES]
    assert len(set(codes)) == 30
    assert all(re.fullmatch(r"[1-9][0-9]{4}", c) for c in codes)
    assert set(codes) == set(EXP)


def test_condition_distribution_matches_config():
    assert sum(c["count"] for c in DIST["categories"]) == DIST["total"] == 30
    for c in DIST["categories"]:
        got = sum(1 for e in EXPECTED if e["condition_category"] == c["id"])
        assert got == c["count"], c["id"]


# ------------------------------------------------------------ Aarav
def test_primary_demo_baby():
    a = next(b for b in BABIES if b["baby_code"] == "10482")
    assert a["full_name"] == "Aarav Kumar"
    assert a["date_of_birth"] == "2026-08-25"
    assert a["age_days_at_reference"] == 67
    assert (REF - date(2026, 8, 25)).days == 67
    assert a["birth_weight_g"] == 1250
    assert (a["gestational_age_weeks"], a["gestational_age_days"]) == (30, 0)
    assert a["current_hospital_id"] == "HOSP001"


# ------------------------------------------------------------ dates and ages
@pytest.mark.parametrize("b", BABIES, ids=lambda b: b["baby_code"])
def test_dates_and_ages(b):
    dob = date.fromisoformat(b["date_of_birth"])
    assert b["reference_date"] == "2026-10-31"
    assert dob <= REF
    assert b["age_days_at_reference"] == (REF - dob).days
    assert 0 <= b["age_days_at_reference"] <= 120, "should be a newborn/young infant"


@pytest.mark.parametrize("b", BABIES, ids=lambda b: b["baby_code"])
def test_notes_agree_with_structured_fields(b):
    age = b["age_days_at_reference"]
    m = re.match(r"Day (\d+)", b["clinical_notes"])
    assert m and int(m.group(1)) == age, "clinical note day must equal computed age"
    assert f"Weight {b['current_weight_g']} g" in b["clinical_notes"]
    s = b["condition_summary"]
    if age == 0:
        assert re.search(r"\b\d+ hours? old\b", s)
        assert b["current_weight_g"] == b["birth_weight_g"]
    else:
        assert f"{age} day" in s, "summary age must equal computed age"


@pytest.mark.parametrize("b", BABIES, ids=lambda b: b["baby_code"])
def test_physiological_plausibility(b):
    bw, cw, age, ga = b["birth_weight_g"], b["current_weight_g"], b["age_days_at_reference"], b["gestational_age_weeks"]
    assert 22 <= ga <= 42 and 0 <= b["gestational_age_days"] <= 6
    assert cw >= 0.85 * bw, "weight loss over 15%"
    assert cw <= bw + 30 * age + 1, "implausible weight gain"
    if ga >= 37:
        assert bw >= 2200
    if ga <= 28:
        assert bw <= 1300


@pytest.mark.parametrize("b", BABIES, ids=lambda b: b["baby_code"])
def test_oxygen_support_consistent(b):
    o = b["oxygen_support"]
    assert o["mode"] in {"ROOM_AIR", "NASAL_CANNULA", "HFNC", "CPAP", "CONVENTIONAL_VENTILATION", "HFOV"}
    assert 0.21 <= o["fio2"] <= 1.0
    if o["mode"] == "ROOM_AIR":
        assert o["fio2"] == 0.21 and o["flow_lpm"] is None
    if o["mode"] in {"NASAL_CANNULA", "HFNC"}:
        assert o["flow_lpm"] is not None
    if o["mode"] in {"CPAP", "CONVENTIONAL_VENTILATION", "HFOV"}:
        assert o["flow_lpm"] is None


# ------------------------------------------------------------ completeness and uniqueness
REQUIRED_RAW = ["baby_code", "full_name", "sex", "date_of_birth", "age_days_at_reference", "birth_weight_g",
                "current_weight_g", "gestational_age_weeks", "medical_history", "condition_summary", "symptoms",
                "clinical_notes", "oxygen_support", "current_care", "current_hospital_id", "transfer_reason",
                "report_ref"]


@pytest.mark.parametrize("b", BABIES, ids=lambda b: b["baby_code"])
def test_raw_record_complete(b):
    for k in REQUIRED_RAW:
        assert b.get(k) not in (None, "", []), k
    assert b["sex"] in {"MALE", "FEMALE"}
    assert b["is_synthetic"] is True
    assert re.fullmatch(r"synthetic-reports/\d{5}/[a-z0-9_]+\.pdf", b["report_ref"])
    assert not b["report_ref"].startswith("http")


@pytest.mark.parametrize("field", RAW_TEXT_FIELDS)
def test_no_repeated_text(field):
    vals = [b[field] for b in BABIES]
    assert len(set(vals)) == 30, f"duplicated {field}"


def test_names_unique():
    assert len({b["full_name"] for b in BABIES}) == 30


# ------------------------------------------------------------ expected requirements
@pytest.mark.parametrize("e", EXPECTED, ids=lambda e: e["baby_code"])
def test_expected_profile_complete_and_valid_ids(e):
    assert e["required_nicu_level"] in {1, 2, 3, 4}
    assert e["required_bed_type"] in {"NICU_HDU", "NICU_INTENSIVE", "NICU_SURGICAL", "NICU_CARDIAC"}
    assert e["expected_priority"] in {"EMERGENCY", "URGENT", "SEMI_URGENT"}
    assert set(e["required_equipment"]) <= EQ, "unknown or misfiled equipment id"
    assert set(e["required_care_facilities"]) <= FAC, "unknown or misfiled facility id"
    assert set(e["required_specialists"]) <= SP, "unknown specialist id"
    assert e["required_equipment"] or e["required_care_facilities"], "no capability requirement"
    assert e["required_specialists"], "no specialist requirement"
    for k in ["required_equipment", "required_care_facilities", "required_specialists"]:
        assert len(e[k]) == len(set(e[k])), f"duplicate in {k}"


@pytest.mark.parametrize("e", EXPECTED, ids=lambda e: e["baby_code"])
def test_bed_type_consistent_with_level(e):
    lvl, bed = e["required_nicu_level"], e["required_bed_type"]
    if bed in {"NICU_SURGICAL", "NICU_CARDIAC"}:
        assert lvl == 4
    if bed == "NICU_HDU":
        assert lvl <= 2
    if bed == "NICU_INTENSIVE":
        assert lvl == 3


# ------------------------------------------------------------ separation of expected answers
def test_raw_dataset_has_no_expected_keys():
    text = (DATA / "baby_dataset.json").read_text()
    for k in EXPECTED_KEYS:
        assert f'"{k}"' not in text, k
    for b in BABIES:
        assert not (EXPECTED_KEYS & set(b))


LEAK_PATTERNS = [r"\b(EQ|FAC|SP|NICU)_[A-Z_]+", r"(?i)\bnicu level\b", r"(?i)\blevel (ii|iii|iv|[1-4])\b",
                 r"(?i)\burgent\b", r"(?i)\bemergency\b", r"(?i)\bpriority\b", r"(?i)semi[-_ ]urgent"]


@pytest.mark.parametrize("b", BABIES, ids=lambda b: b["baby_code"])
def test_no_expected_answers_leak_into_raw_text(b):
    t = raw_text(b)
    for p in LEAK_PATTERNS:
        assert not re.search(p, t), f"pattern {p} found in raw record"
    # specialist / equipment display names must not be pasted in as a list either
    for name in ["Neonatal surgical theatre", "Paediatric cardiac catheterisation lab", "Retinal laser photocoagulation"]:
        assert name.lower() not in t.lower()


# ------------------------------------------------------------ hospitals
def test_hospital_references_valid():
    for b in BABIES:
        assert b["current_hospital_id"] in HOSP
        assert HOSP[b["current_hospital_id"]]["demo_network"]["can_refer"]
    assert set(HOSP) == {f"HOSP00{i}" for i in range(1, 9)}


def test_hospital_public_vs_simulated_separation():
    names = {h["public_information"]["name"] for h in NET}
    for wanted in ["Bangalore Baptist", "Chinmaya Mission", "Kempegowda", "Rainbow", "Manipal", "Aster CMI", "Martha"]:
        assert any(wanted in n for n in names), wanted
    for h in NET:
        sim = h["simulated_operational_profile"]
        assert sim["_label"].startswith("SIMULATED")
        assert h["id"] in SRC
        q = h["public_information"]["coordinate_quality"]
        assert q in {"SOURCED", "PROXY_SOURCED", "APPROXIMATE_LOCALITY", "FICTIONAL"}
        assert (q == "FICTIONAL") == h["is_fictional"]
        if not h["is_fictional"]:
            assert SRC[h["id"]]["sources"], "real hospital without a source"
        for item in sim["equipment_and_facilities"]:
            assert item["code"] in EQ | FAC
        assert set(sim["specialists"]) <= SP
        for bed in sim["bed_capacity"]:
            assert 0 <= bed["occupied_beds"] + bed["reserved_beds"] <= bed["total_beds"]
    assert "Not live bed availability" in load("bengaluru_hospitals.json")["notice"]


# ------------------------------------------------------------ minimal payload and scenario
def test_minimal_transfer_payload():
    m = SCEN["minimal_offer_payload"]
    p = m["payload"]
    assert list(p) == m["allowed_fields"]
    assert set(p) == {"baby_code", "baby_name", "date_of_birth", "age_days", "required_nicu_level",
                      "required_equipment", "required_specialists", "priority", "source_hospital_id", "synthetic"}
    assert not set(p) & set(m["forbidden_fields"])
    e = EXP["10482"]
    assert p["baby_code"] == "10482" and p["baby_name"] == "Aarav Kumar"
    assert p["date_of_birth"] == "2026-08-25" and p["age_days"] == 67
    assert p["required_nicu_level"] == e["required_nicu_level"]
    assert p["required_equipment"] == e["required_equipment"] + e["required_care_facilities"]
    assert p["required_specialists"] == e["required_specialists"]
    assert p["priority"] == e["expected_priority"]
    assert p["source_hospital_id"] == "HOSP001" and p["synthetic"] is True
    a = next(b for b in BABIES if b["baby_code"] == "10482")
    blob = json.dumps(p)
    for f in ["clinical_notes", "medical_history", "transfer_reason"]:
        assert a[f][:40] not in blob


def _cap(hid, bed):
    return next(c for c in HOSP[hid]["simulated_operational_profile"]["bed_capacity"] if c["bed_type"] == bed)


def test_demo_scenario_consistency():
    cands = {c["hospital_id"]: c for c in SCEN["expected_candidate_assessment"]["candidates"]}
    order = SCEN["expected_candidate_assessment"]["expected_eligible_order_by_distance"]
    assert order[:2] == ["HOSP002", "HOSP003"]
    assert cands["HOSP001"]["eligible"] is False
    # every exclusion class is represented for 10482
    reasons = " | ".join(r for c in cands.values() if not c["eligible"] for r in c["reasons"])
    for frag in ["source hospital", "unavailable", "missing SP_", "no available", "below required"]:
        assert frag in reasons, frag
    # HOSP002 has exactly one free bed before the demo capacity event, zero after
    c2 = _cap("HOSP002", "NICU_INTENSIVE")
    assert c2["total_beds"] - c2["occupied_beds"] - c2["reserved_beds"] == 1
    c3 = _cap("HOSP003", "NICU_INTENSIVE")
    assert c3["total_beds"] - c3["occupied_beds"] - c3["reserved_beds"] >= 1
    fin = SCEN["expected_final_state"]
    assert fin["capacity"]["HOSP002"]["NICU_INTENSIVE"] == {"total": 10, "occupied": 10, "reserved": 0}
    assert fin["capacity"]["HOSP003"]["NICU_INTENSIVE"] == {"total": c3["total_beds"], "occupied": c3["occupied_beds"], "reserved": 1}
    a1, a2 = fin["attempts"]
    assert (a1["hospital_id"], a1["status"], a1["rejection_reason"]) == ("HOSP002", "REJECTED", "NICU bed unavailable at confirmation time")
    assert (a2["hospital_id"], a2["status"]) == ("HOSP003", "ACCEPTED")
    assert fin["transfer"]["receiving_hospital_id"] == "HOSP003"
    assert SCEN["approved_requirements"]["required_bed_type"] == "NICU_INTENSIVE"


def test_scenario_not_preseeded():
    seed = (DATA / "baby_seed.sql").read_text() + (DATA / "hospital_seed.sql").read_text()
    assert "transfer_requests" not in seed and "transfer_attempts" not in seed and "INSERT INTO transfers" not in seed


# ------------------------------------------------------------ reproducibility
def test_generator_is_deterministic():
    outs = ["baby_dataset.json", "expected_requirements.json", "baby_seed.sql", "hospital_seed.sql",
            "demo_transfer_scenario.json", "baby_testing.md", "hospital_sources.json", "bengaluru_hospitals.json"]
    before = {o: hashlib.sha256((DATA / o).read_bytes()).hexdigest() for o in outs}
    subprocess.run([sys.executable, str(DATA / "generator" / "build_dataset.py")], check=True, capture_output=True)
    after = {o: hashlib.sha256((DATA / o).read_bytes()).hexdigest() for o in outs}
    assert before == after
