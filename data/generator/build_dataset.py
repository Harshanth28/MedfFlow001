#!/usr/bin/env python3
"""
Build every Step 2 data file from the two source modules.

    python3 data/generator/build_dataset.py

Deterministic: same inputs -> byte-identical outputs. Never hand-edit the outputs;
edit clinical_records.py / network.py / ../condition_distribution.json and re-run.
"""
import json
import math
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent
sys.path.insert(0, str(HERE))

from clinical_records import RECORDS, REFERENCE_DATE          # noqa: E402
from network import (EQUIPMENT_TYPES, HOSPITALS, RETRIEVED,     # noqa: E402
                     SOURCES, SPECIALIST_TYPES)

REF = date.fromisoformat(REFERENCE_DATE)
EQ_CATEGORY = {code: cat for code, _, cat, _ in EQUIPMENT_TYPES}
SYNTHETIC_NOTICE = ("SYNTHETIC DEMONSTRATION DATA. All people are fictional. "
                    "Not real patients and not for clinical use.")
SIM_NOTICE = ("Hospital names and public facts are real; every operational value "
              "(NICU level, equipment, specialists, beds, readiness) is SIMULATED. "
              "Not live bed availability. No partnership is implied.")
DEMO_DECLINE_REASON = "NICU bed unavailable at confirmation time"
MINIMAL_PAYLOAD_FIELDS = ["baby_code", "baby_name", "date_of_birth", "age_days",
                          "required_nicu_level", "required_equipment", "required_specialists",
                          "priority", "source_hospital_id", "synthetic"]


def dump(name, obj):
    (DATA / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sql(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, list):
        return "ARRAY[" + ", ".join(sql(x) for x in v) + "]::text[]" if v else "ARRAY[]::text[]"
    return "'" + str(v).replace("'", "''") + "'"


def haversine_km(a, b):
    """Scenario sanity check only. The application's distance service is built in Step 5."""
    r = 6371.0088
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


# ------------------------------------------------------------------ babies
def build_babies():
    babies, expected = [], []
    for rec in RECORDS:
        raw = dict(rec["raw"])
        age = (REF - date.fromisoformat(raw["date_of_birth"])).days
        out = {
            "baby_code": raw["baby_code"],
            "full_name": raw["full_name"],
            "sex": raw["sex"],
            "date_of_birth": raw["date_of_birth"],
            "reference_date": REFERENCE_DATE,
            "age_days_at_reference": age,
            "birth_weight_g": raw["birth_weight_g"],
            "current_weight_g": raw["current_weight_g"],
            "gestational_age_weeks": raw["gestational_age_weeks"],
            "gestational_age_days": raw["gestational_age_days"],
            "medical_history": raw["medical_history"],
            "condition_summary": raw["condition_summary"],
            "symptoms": raw["symptoms"],
            "clinical_notes": raw["clinical_notes"],
            "oxygen_support": raw["oxygen_support"],
            "current_care": raw["current_care"],
            "current_hospital_id": raw["current_hospital_id"],
            "transfer_reason": raw["transfer_reason"],
            "report_ref": f"synthetic-reports/{raw['baby_code']}/clinical_summary_v1.pdf",
            "is_synthetic": True,
        }
        babies.append(out)
        e = rec["expected"]
        expected.append({
            "baby_code": raw["baby_code"],
            "condition_category": rec["category"],
            "required_nicu_level": e["required_nicu_level"],
            "required_bed_type": e["required_bed_type"],
            "required_equipment": e["required_equipment"],
            "required_care_facilities": e["required_care_facilities"],
            "required_specialists": e["required_specialists"],
            "expected_priority": e["expected_priority"],
        })
    return babies, expected


# ------------------------------------------------------------------ hospitals
def build_hospital_files():
    hospitals_json = []
    for h in HOSPITALS:
        s = h["sim"]
        hospitals_json.append({
            "id": h["id"],
            "short_name": h["short_name"],
            "is_fictional": h["is_fictional"],
            "public_information": dict(h["public"], retrieved=None if h["is_fictional"] else RETRIEVED),
            "demo_network": h["network"],
            "simulated_operational_profile": {
                "_label": "SIMULATED — not the hospital's real capability or capacity",
                "nicu_level": s["nicu_level"],
                "readiness_score": s["readiness"],
                "equipment_and_facilities": [
                    {"code": c, "available": c not in s["unavailable_equipment"],
                     "note": s["unavailable_equipment"].get(c)} for c in s["equipment"]],
                "specialists": s["specialists"],
                "bed_capacity": [{"bed_type": bt, "total_beds": t, "occupied_beds": o, "reserved_beds": 0}
                                 for bt, (t, o) in s["capacity"].items()],
            },
        })
    dump("bengaluru_hospitals.json", {
        "notice": SIM_NOTICE, "public_facts_retrieved": RETRIEVED,
        "coordinate_quality_legend": {
            "SOURCED": "coordinates taken from a cited public source",
            "PROXY_SOURCED": "coordinates of a co-located institution from a cited source",
            "APPROXIMATE_LOCALITY": "address verified, coordinates approximated to the locality; not geocoded",
            "FICTIONAL": "invented site for the fictional referral centre"},
        "hospitals": hospitals_json})
    dump("hospital_sources.json", {
        "retrieved": RETRIEVED,
        "policy": "Only the 'verified' items come from public sources. Everything operational is simulated.",
        "hospitals": [{"id": h["id"], "name": h["public"]["name"],
                       "coordinate_quality": h["public"]["coordinate_quality"], **SOURCES[h["id"]]}
                      for h in HOSPITALS]})


# ------------------------------------------------------------------ SQL
def hospital_seed_sql():
    L = ["-- MedFlow hospital network seed — GENERATED by data/generator/build_dataset.py. Do not edit.",
         f"-- {SIM_NOTICE}", "BEGIN;", ""]
    for code, name, cat, desc in EQUIPMENT_TYPES:
        L.append(f"INSERT INTO equipment_types (code, name, category, description) VALUES "
                 f"({sql(code)}, {sql(name)}, {sql(cat)}, {sql(desc)}) "
                 f"ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, category = EXCLUDED.category, description = EXCLUDED.description;")
    for code, name, desc in SPECIALIST_TYPES:
        L.append(f"INSERT INTO specialist_types (code, name, description) VALUES "
                 f"({sql(code)}, {sql(name)}, {sql(desc)}) "
                 f"ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description;")
    L.append("")
    for h in HOSPITALS:
        p, n, s = h["public"], h["network"], h["sim"]
        L.append(
            "INSERT INTO hospitals (id, name, short_name, is_fictional, locality, address, latitude, longitude, "
            "coordinate_quality, is_active, can_refer, can_receive, sim_nicu_level, sim_readiness_score) VALUES ("
            + ", ".join(sql(x) for x in [h["id"], p["name"], h["short_name"], h["is_fictional"], p["locality"],
                                        p["address"], p["latitude"], p["longitude"], p["coordinate_quality"],
                                        n["is_active"], n["can_refer"], n["can_receive"], s["nicu_level"],
                                        s["readiness"]])
            + ") ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, short_name = EXCLUDED.short_name, "
              "is_fictional = EXCLUDED.is_fictional, locality = EXCLUDED.locality, address = EXCLUDED.address, "
              "latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, coordinate_quality = EXCLUDED.coordinate_quality, "
              "is_active = EXCLUDED.is_active, can_refer = EXCLUDED.can_refer, can_receive = EXCLUDED.can_receive, "
              "sim_nicu_level = EXCLUDED.sim_nicu_level, sim_readiness_score = EXCLUDED.sim_readiness_score, updated_at = now();")
    ids = ", ".join(sql(h["id"]) for h in HOSPITALS)
    L += ["", f"DELETE FROM hospital_equipment   WHERE hospital_id IN ({ids});",
          f"DELETE FROM hospital_specialists WHERE hospital_id IN ({ids});",
          f"DELETE FROM hospital_capacity    WHERE hospital_id IN ({ids});"]
    for h in HOSPITALS:
        s = h["sim"]
        for c in s["equipment"]:
            note = s["unavailable_equipment"].get(c)
            L.append(f"INSERT INTO hospital_equipment (hospital_id, equipment_code, sim_available, sim_note) VALUES "
                     f"({sql(h['id'])}, {sql(c)}, {sql(note is None)}, {sql(note)});")
        for c in s["specialists"]:
            L.append(f"INSERT INTO hospital_specialists (hospital_id, specialist_code) VALUES ({sql(h['id'])}, {sql(c)});")
        for bt, (t, o) in s["capacity"].items():
            L.append(f"INSERT INTO hospital_capacity (hospital_id, bed_type, total_beds, occupied_beds, reserved_beds, checked_at) "
                     f"VALUES ({sql(h['id'])}, {sql(bt)}, {t}, {o}, 0, TIMESTAMPTZ '2026-10-31 00:00:00+05:30');")
    L += ["", "COMMIT;", ""]
    return "\n".join(L)


def baby_seed_sql(babies, expected):
    L = ["-- MedFlow baby seed — GENERATED by data/generator/build_dataset.py. Do not edit.",
         f"-- {SYNTHETIC_NOTICE}",
         "-- Requires hospital_seed.sql first. Expected requirements go to SEPARATE tables.",
         "BEGIN;", ""]
    cols = ["baby_code", "full_name", "sex", "date_of_birth", "reference_date", "age_days_at_reference",
            "birth_weight_g", "current_weight_g", "gestational_age_weeks", "gestational_age_days",
            "medical_history", "condition_summary", "symptoms", "clinical_notes",
            "oxygen_support_mode", "oxygen_fio2", "oxygen_flow_lpm", "oxygen_support_notes",
            "current_care", "current_hospital_id", "transfer_reason", "report_ref"]
    for b in babies:
        o = b["oxygen_support"]
        vals = [b["baby_code"], b["full_name"], b["sex"], b["date_of_birth"], b["reference_date"],
                b["age_days_at_reference"], b["birth_weight_g"], b["current_weight_g"],
                b["gestational_age_weeks"], b["gestational_age_days"], b["medical_history"],
                b["condition_summary"], b["symptoms"], b["clinical_notes"], o["mode"], o["fio2"],
                o["flow_lpm"], o["notes"], b["current_care"], b["current_hospital_id"],
                b["transfer_reason"], b["report_ref"]]
        upd = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols[1:])
        L.append(f"INSERT INTO babies ({', '.join(cols)}) VALUES ({', '.join(sql(v) for v in vals)}) "
                 f"ON CONFLICT (baby_code) DO UPDATE SET {upd};")
    codes = ", ".join(sql(b["baby_code"]) for b in babies)
    L += ["", f"DELETE FROM baby_expected_requirements WHERE baby_code IN ({codes});"]
    for e in expected:
        L.append(f"INSERT INTO baby_expected_requirements (baby_code, required_nicu_level, required_bed_type, expected_priority) "
                 f"VALUES ({sql(e['baby_code'])}, {e['required_nicu_level']}, {sql(e['required_bed_type'])}, {sql(e['expected_priority'])});")
        for c in e["required_equipment"] + e["required_care_facilities"]:
            L.append(f"INSERT INTO baby_expected_equipment (baby_code, equipment_code) VALUES ({sql(e['baby_code'])}, {sql(c)});")
        for c in e["required_specialists"]:
            L.append(f"INSERT INTO baby_expected_specialists (baby_code, specialist_code) VALUES ({sql(e['baby_code'])}, {sql(c)});")
    L += ["", "COMMIT;", ""]
    return "\n".join(L)


# ------------------------------------------------------------------ demo scenario
def satisfies(h, e):
    """Data-consistency check for the documented demo only (not the Step 5 engine)."""
    s = h["sim"]
    avail = set(s["equipment"]) - set(s["unavailable_equipment"])
    beds = s["capacity"].get(e["required_bed_type"])
    reasons = []
    if not h["network"]["is_active"]:
        reasons.append("inactive")
    if s["nicu_level"] < e["required_nicu_level"]:
        reasons.append(f"NICU level {s['nicu_level']} below required {e['required_nicu_level']}")
    for c in e["required_equipment"] + e["required_care_facilities"]:
        if c not in s["equipment"]:
            reasons.append(f"missing {c}")
        elif c not in avail:
            reasons.append(f"{c} unavailable ({s['unavailable_equipment'][c]})")
    for c in e["required_specialists"]:
        if c not in s["specialists"]:
            reasons.append(f"missing {c}")
    if beds is None or beds[0] - beds[1] <= 0:
        reasons.append(f"no available {e['required_bed_type']} bed")
    return reasons


def build_scenario(babies, expected):
    aarav = next(b for b in babies if b["baby_code"] == "10482")
    exp = next(e for e in expected if e["baby_code"] == "10482")
    src = next(h for h in HOSPITALS if h["id"] == "HOSP001")
    src_xy = (src["public"]["latitude"], src["public"]["longitude"])
    candidates = []
    for h in HOSPITALS:
        if h["id"] == "HOSP001":
            candidates.append({"hospital_id": h["id"], "eligible": False, "reasons": ["source hospital"]})
            continue
        reasons = satisfies(h, exp)
        candidates.append({
            "hospital_id": h["id"], "name": h["public"]["name"],
            "straight_line_km_approx": round(haversine_km(src_xy, (h["public"]["latitude"], h["public"]["longitude"])), 1),
            "eligible": not reasons, "reasons": reasons or ["all mandatory requirements satisfied"]})
    payload = {
        "baby_code": aarav["baby_code"], "baby_name": aarav["full_name"],
        "date_of_birth": aarav["date_of_birth"], "age_days": aarav["age_days_at_reference"],
        "required_nicu_level": exp["required_nicu_level"],
        "required_equipment": exp["required_equipment"] + exp["required_care_facilities"],
        "required_specialists": exp["required_specialists"],
        "priority": exp["expected_priority"], "source_hospital_id": "HOSP001", "synthetic": True,
    }
    return {
        "notice": SYNTHETIC_NOTICE + " " + SIM_NOTICE,
        "scenario_id": "DEMO-10482-ESCALATION",
        "reference_date": REFERENCE_DATE,
        "baby_code": "10482",
        "source_hospital_id": "HOSP001",
        "assumption": "The clinician approves requirements identical to the expected profile for 10482. "
                      "In the live demo the approved values come from the Step 4 review screen.",
        "approved_requirements": {k: exp[k] for k in ["required_nicu_level", "required_bed_type",
                                                       "required_equipment", "required_care_facilities",
                                                       "required_specialists", "expected_priority"]},
        "expected_candidate_assessment": {
            "_note": "Expected outcome derived from seeded data, for Step 5 tests to confirm. "
                     "Distances are approximate straight-line km from approximate coordinates; not road distance or ETA.",
            "candidates": candidates,
            "expected_eligible_order_by_distance": [c["hospital_id"] for c in sorted(
                (c for c in candidates if c["eligible"]), key=lambda c: c["straight_line_km_approx"])],
        },
        "minimal_offer_payload": {
            "policy": "demo",
            "allowed_fields": MINIMAL_PAYLOAD_FIELDS,
            "forbidden_fields": ["medical_history", "clinical_notes", "symptoms", "condition_summary",
                                 "report_ref", "current_care", "oxygen_support", "transfer_reason"],
            "pseudonymous_policy_replaces": {"baby_code": "referral_token", "baby_name": None, "date_of_birth": None},
            "payload": payload,
        },
        "steps": [
            {"n": 1, "actor": "HOSP001 REFERRER", "action": "Look up baby 10482", "expect": "Aarav Kumar, 67 days"},
            {"n": 2, "actor": "HOSP001 REFERRER", "action": "Run AI extraction, review and confirm requirements", "expect": "review_status CONFIRMED"},
            {"n": 3, "actor": "system", "action": "Match hospitals", "expect": "eligible ranked list begins HOSP002, HOSP003 (to be verified in Step 5)"},
            {"n": 4, "actor": "system", "action": "Create offer #1 to HOSP002 with the minimal payload", "expect": "transfer_attempts status PENDING, sequence_no 1"},
            {"n": 5, "actor": "HOSP002 staff (authorised)", "action": "Record capacity change: last NICU_INTENSIVE bed now occupied",
             "expect": "HOSP002 NICU_INTENSIVE occupied 9 -> 10 (0 available)"},
            {"n": 6, "actor": "HOSP002 RECEIVER", "action": f"Decline offer #1 with reason '{DEMO_DECLINE_REASON}'",
             "expect": "offer #1 REJECTED, history kept"},
            {"n": 7, "actor": "system", "action": "Escalate to next eligible hospital", "expect": "offer #2 to HOSP003 PENDING, sequence_no 2"},
            {"n": 8, "actor": "HOSP003 RECEIVER", "action": "Accept offer #2 (real user action)",
             "expect": "capacity re-checked; HOSP003 NICU_INTENSIVE reserved 0 -> 1; transfer created; referral CONFIRMED"},
            {"n": 9, "actor": "system", "action": "Grant report access", "expect": "only HOSP003 can retrieve the full synthetic record"},
        ],
        "expected_final_state": {
            "transfer_request_status": "CONFIRMED",
            "attempts": [{"sequence_no": 1, "hospital_id": "HOSP002", "status": "REJECTED", "rejection_reason": DEMO_DECLINE_REASON},
                         {"sequence_no": 2, "hospital_id": "HOSP003", "status": "ACCEPTED"}],
            "capacity": {"HOSP002": {"NICU_INTENSIVE": {"total": 10, "occupied": 10, "reserved": 0}},
                         "HOSP003": {"NICU_INTENSIVE": {"total": 8, "occupied": 5, "reserved": 1}}},
            "transfer": {"receiving_hospital_id": "HOSP003", "status": "ACCEPTED", "reserved_bed_type": "NICU_INTENSIVE"},
        },
        "rules": ["Nothing in this scenario is pre-seeded into transfer_requests or transfer_attempts.",
                  "Acceptance must happen through the real application action, never through seed data."],
    }


def baby_testing_md(babies, expected, dist):
    exp = {e["baby_code"]: e for e in expected}
    L = ["# MedFlow — synthetic baby test guide", "",
         f"> {SYNTHETIC_NOTICE}", "",
         f"Reference date for every age: **{REFERENCE_DATE}**. Generated by `data/generator/build_dataset.py`.", "",
         "## Condition distribution", "",
         f"Status: **{dist['status']}** — {dist['status_reason']}", "",
         "| Category | Count |", "|---|---|"]
    for c in dist["categories"]:
        L.append(f"| {c['label']} | {c['count']} |")
    L += ["", "## Records", "",
          "Expected values are for evaluation only and must never be passed to the AI provider.", "",
          "| Code | Name | Age (d) | GA | BW (g) | Category | Exp. level | Exp. bed | Exp. priority |",
          "|---|---|---|---|---|---|---|---|---|"]
    for b in babies:
        e = exp[b["baby_code"]]
        L.append(f"| {b['baby_code']} | {b['full_name']} | {b['age_days_at_reference']} | "
                 f"{b['gestational_age_weeks']}+{b['gestational_age_days']} | {b['birth_weight_g']} | "
                 f"{e['condition_category']} | {e['required_nicu_level']} | {e['required_bed_type']} | {e['expected_priority']} |")
    L += ["", "## Suggested test cases", "",
          "| Purpose | Code(s) |", "|---|---|",
          "| Primary demo (HOSP002 decline → HOSP003 accept) | 10482 |",
          "| Same-day births, age 0 | 19832, 20417, 26819, 28095, 30258 |",
          "| Lowest acuity / HDU-only (St. Martha's can be eligible) | 22351 |",
          "| Cardiac bed only at Aster CMI | 23904, 24176, 25530, 26819 |",
          "| Surgical bed (KIMS, Aster CMI) | 12754, 14628, 27463, 28095, 29742, 30258, 31674, 32901 |",
          "| No equipment, facilities only | 31674, 32901 |",
          "| Rare specialists (neurosurgeon, metabolic, nephrology) | 14628, 38402, 39175, 21688 |",
          "| Unknown code (must return a clear error) | 99999, 00000, 1048, abcde |", ""]
    return "\n".join(L)


def main():
    dist = json.loads((DATA / "condition_distribution.json").read_text())
    babies, expected = build_babies()
    dump("baby_dataset.json", {"notice": SYNTHETIC_NOTICE, "reference_date": REFERENCE_DATE,
                               "count": len(babies), "babies": babies})
    dump("expected_requirements.json", {
        "notice": "EVALUATION ONLY. Never send to the AI provider. " + SYNTHETIC_NOTICE,
        "reference_date": REFERENCE_DATE, "condition_distribution_status": dist["status"],
        "count": len(expected), "expected_requirements": expected})
    build_hospital_files()
    dump("demo_transfer_scenario.json", build_scenario(babies, expected))
    (DATA / "hospital_seed.sql").write_text(hospital_seed_sql(), encoding="utf-8")
    (DATA / "baby_seed.sql").write_text(baby_seed_sql(babies, expected), encoding="utf-8")
    (DATA / "baby_testing.md").write_text(baby_testing_md(babies, expected, dist), encoding="utf-8")
    print(f"built {len(babies)} babies, {len(HOSPITALS)} hospitals")


if __name__ == "__main__":
    main()
