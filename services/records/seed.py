"""Seed the records service: emergency profiles, trauma profiles, health records, QR token."""

import json
import os
import secrets
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # repo root

from records_app import models
from records_app.main import engine, SessionLocal
from records_app.crypto import seal
from services.shared.db import Base

# Where the identity service keeps its database. The environment variable wins
# so the same seed works when the service runs from a container image with the
# database on a mounted volume.
IDENTITY_DB = Path(
    os.getenv("IDENTITY_DB", str(Path(__file__).parent.parent / "identity" / "identity.db"))
)

PROFILES = {
    "aarav@abha.dev": {
        "full_name": "Aarav Mehta",
        "blood_group": "O+",
        "allergies": ["Penicillin", "Peanuts"],
        "chronic_conditions": ["Asthma"],
        "medications": ["Salbutamol inhaler", "Montelukast 10mg"],
        "emergency_contacts": [
            {"name": "Meera Mehta", "phone": "+91-90000-00021", "relation": "Mother", "email": "meera@example.com"},
            {"name": "Vikram Mehta", "phone": "+91-90000-00022", "relation": "Father", "email": "vikram@example.com"},
        ],
    },
    "diya@abha.dev": {
        "full_name": "Diya Sharma",
        "blood_group": "A+",
        "allergies": ["Sulfa drugs"],
        "chronic_conditions": ["Type 1 Diabetes"],
        "medications": ["Insulin (basal-bolus)"],
        "emergency_contacts": [{"name": "Raj Sharma", "phone": "+91-90000-00023", "relation": "Father", "email": "raj@example.com"}],
    },
    "rohan@abha.dev": {"full_name": "Rohan Verma", "blood_group": "B+", "allergies": [], "chronic_conditions": [], "medications": [], "emergency_contacts": []},
    "isha@abha.dev": {
        "full_name": "Isha Patil",
        "blood_group": "AB+",
        "allergies": ["Latex"],
        "chronic_conditions": ["Epilepsy"],
        "medications": ["Levetiracetam 500mg"],
        "emergency_contacts": [{"name": "Sunita Patil", "phone": "+91-90000-00024", "relation": "Mother", "email": "sunita@example.com"}],
    },
    "kabir@abha.dev": {"full_name": "Kabir Nair", "blood_group": "O-", "allergies": ["Aspirin"], "chronic_conditions": [], "medications": [], "emergency_contacts": []},
    "anaya@abha.dev": {
        "full_name": "Anaya Gupta",
        "blood_group": "B-",
        "allergies": [],
        "chronic_conditions": ["Hypothyroidism"],
        "medications": ["Levothyroxine 50mcg"],
        "emergency_contacts": [],
    },
}

RECORDS = [
    ("aarav@abha.dev", "city@abha.dev", "Prescription", "Paracetamol 500mg + Salbutamol nebulisation", {"dosage": "TDS x 3 days, nebulise BD"}),
    ("aarav@abha.dev", "city@abha.dev", "DiagnosticReport", "CBC + Serum IgE panel", {"conclusion": "Eosinophilia noted; allergic profile elevated"}),
    ("diya@abha.dev", "city@abha.dev", "Prescription", "Insulin Glargine 10U OD", {"dosage": "10 units subcutaneous at bedtime"}),
    ("diya@abha.dev", "city@abha.dev", "DiagnosticReport", "HbA1c", {"conclusion": "7.8% — suboptimal control"}),
    ("rohan@abha.dev", "city@abha.dev", "Immunization", "Hepatitis B booster", {}),
    ("isha@abha.dev", "city@abha.dev", "Prescription", "Levetiracetam 500mg BD", {"dosage": "Twice daily after food"}),
    ("isha@abha.dev", "sunrise@abha.dev", "DiagnosticReport", "EEG Routine", {"conclusion": "Normal awake-sleep EEG"}),
    ("kabir@abha.dev", "city@abha.dev", "DiagnosticReport", "Lipid Profile", {"conclusion": "Within normal limits"}),
    ("anaya@abha.dev", "city@abha.dev", "Prescription", "Levothyroxine 50mcg OD", {"dosage": "Once daily, empty stomach"}),
    ("anaya@abha.dev", "city@abha.dev", "DiagnosticReport", "TSH Reflex", {"conclusion": "TSH 4.9 — borderline"}),
]


def _identity_user_ids() -> dict[str, int]:
    con = sqlite3.connect(IDENTITY_DB)
    rows = con.execute("SELECT email, id, abha_id FROM users WHERE role IN ('patient','hospital')").fetchall()
    con.close()
    return {r[0]: {"id": r[1], "abha_id": r[2]} for r in rows}


def seed():
    Base.metadata.create_all(bind=engine)
    users = _identity_user_ids()
    if not users:
        print("records: identity not seeded yet — run identity seed first")
        return
    db = SessionLocal()
    if db.query(models.TraumaProfile).first():
        print("records: already seeded")
        return

    for email, p in PROFILES.items():
        uid = users[email]["id"]
        prof = models.PatientProfile(
            user_id=uid,
            full_name=p["full_name"],
            blood_group=p["blood_group"],
            allergies=json.dumps(p["allergies"]),
            chronic_conditions=json.dumps(p["chronic_conditions"]),
            medications=json.dumps(p["medications"]),
            emergency_contacts=json.dumps(p["emergency_contacts"]),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(prof)
        data_hex, nonce_hex, sig = seal(
            {
                "full_name": p["full_name"],
                "abha_id": users[email]["abha_id"],
                "blood_group": p["blood_group"],
                "allergies": p["allergies"],
                "chronic_conditions": p["chronic_conditions"],
                "medications": p["medications"],
                "emergency_contacts": p["emergency_contacts"],
            }
        )
        db.add(
            models.TraumaProfile(
                patient_id=uid, encrypted_blob=data_hex, nonce=nonce_hex, hmac_sha256=sig, updated_at=datetime.now(timezone.utc)
            )
        )
        db.add(models.QrToken(patient_id=uid, token=secrets.token_hex(16), active=True))

    for patient_email, hospital_email, rtype, title, details in RECORDS:
        uid = users[patient_email]["id"]
        hid = users[hospital_email]["id"]
        from records_app.fhir_local import build_record_fhir

        fhir = build_record_fhir(rtype, title, details, PROFILES.get(patient_email, {}).get("full_name", ""), users[patient_email]["abha_id"] or "")
        db.add(models.HealthRecord(patient_id=uid, type=rtype, title=title, fhir_json=fhir, created_by=hid))

    db.commit()
    print("records: seeded", len(PROFILES), "profiles and", len(RECORDS), "records")


if __name__ == "__main__":
    seed()
