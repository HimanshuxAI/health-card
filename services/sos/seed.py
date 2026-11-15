"""Seed the SOS service: historical alerts."""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # repo root

from app import models
from app.main import engine, SessionLocal
from services.shared.db import Base

ALERTS = [
    (4, "Aarav Mehta", "PANIC", 18.5204, 73.8567, "JM Road, Pune", [{"name": "Meera Mehta", "phone": "+91-90000-00021", "relation": "Mother"}], "SKIPPED", 5),
    (5, "Diya Sharma", "QR_SCAN", 18.5293, 73.8743, "Emergency Ward, City Hospital", [{"name": "Raj Sharma", "phone": "+91-90000-00023", "relation": "Father"}], "SKIPPED", 26),
    (4, "Aarav Mehta", "QR_SCAN", 12.9716, 77.5946, "OPD, City Hospital", [{"name": "Meera Mehta", "phone": "+91-90000-00021", "relation": "Mother"}], "SKIPPED", 47),
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(models.Alert).first():
        print("sos: already seeded")
        return
    for pid, name, trigger, lat, lng, label, contacts, email_status, hours_ago in ALERTS:
        db.add(
            models.Alert(
                patient_id=pid,
                patient_name=name,
                trigger=trigger,
                lat=lat,
                lng=lng,
                location_label=label,
                notified_contacts=json.dumps(contacts),
                email_status=email_status,
                created_at=datetime.utcnow() - timedelta(hours=hours_ago),
            )
        )
    db.commit()
    print("sos: seeded", len(ALERTS), "alerts")


if __name__ == "__main__":
    seed()
