"""Seed the NHCX service: bills and claims in varied states."""

import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # repo root

from nhcx_app import models
from nhcx_app.main import engine, SessionLocal
from nhcx_app.state_machine import build_fhir_claim
from services.shared.db import Base

# Where the identity service keeps its database. The environment variable wins
# so the same seed works when the service runs from a container image with the
# database on a mounted volume.
IDENTITY_DB = Path(
    os.getenv("IDENTITY_DB", str(Path(__file__).parent.parent / "identity" / "identity.db"))
)

BILLS = [
    # patient_email, hospital_email, items, claim_status (None = no claim)
    ("aarav@abha.dev", "city@abha.dev", [("OPD Consultation", 600), ("CBC + IgE Panel", 1150), ("Nebulisation x2", 800)], "APPROVED"),
    ("diya@abha.dev", "city@abha.dev", [("Endocrinologist consult", 1200), ("HbA1c", 500)], "ADJUDICATED"),
    ("isha@abha.dev", "city@abha.dev", [("Neurologist consult", 1500), ("EEG", 2500)], "SUBMITTED"),
    ("kabir@abha.dev", "city@abha.dev", [("OPD Consultation", 500)], None),
    ("anaya@abha.dev", "sunrise@abha.dev", [("TSH Reflex", 450), ("Physician consult", 700)], None),
]


def _users():
    con = sqlite3.connect(IDENTITY_DB)
    rows = con.execute("SELECT email, id, abha_id FROM users WHERE role IN ('patient','hospital')").fetchall()
    con.close()
    return {r[0]: {"id": r[1], "abha_id": r[2]} for r in rows}


def seed():
    Base.metadata.create_all(bind=engine)
    users = _users()
    if not users:
        print("nhcx: identity not seeded yet")
        return
    db = SessionLocal()
    if db.query(models.Bill).first():
        print("nhcx: already seeded")
        return

    for patient_email, hospital_email, items, status in BILLS:
        p, h = users[patient_email], users[hospital_email]
        total = sum(a for _, a in items)
        bill = models.Bill(
            hospital_id=h["id"],
            patient_id=p["id"],
            patient_abha_id=p["abha_id"] or "",
            line_items=json.dumps([{"description": d, "amount": a} for d, a in items]),
            total=float(total),
            created_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        db.add(bill)
        db.commit()
        db.refresh(bill)
        if status:
            claim = models.Claim(bill_id=bill.id, status=status)
            if status in ("APPROVED", "ADJUDICATED"):
                claim.approved_amount = total if status == "APPROVED" else total * 0.6
                claim.out_of_pocket = 0.0 if status == "APPROVED" else total * 0.4
                claim.insurer_note = (
                    "Claim approved in full. No out-of-pocket expense."
                    if status == "APPROVED"
                    else "Partially approved: 60% of itemized amount covered."
                )
            claim.adjudicated_at = datetime.now(timezone.utc) - timedelta(hours=5)
            db.add(claim)
            db.commit()
            db.refresh(claim)
            claim.fhir_claim_json = json.dumps(build_fhir_claim(bill, claim.id))
            db.commit()
    print("nhcx: seeded", len(BILLS), "bills")


if __name__ == "__main__":
    seed()
