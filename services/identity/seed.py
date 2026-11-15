"""Seed the identity service database with demo accounts."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # repo root (services.shared)

from app import models
from app.main import engine, SessionLocal
from services.shared.db import Base
from services.shared import security

ACCOUNTS = [
    # (name, email, password, role, abha_id, phone, hospital_name)
    ("System Admin", "admin@abha.dev", "abha1234", "admin", None, "+91-90000-00001", None),
    ("City Hospital", "city@abha.dev", "abha1234", "hospital", None, "+91-90000-00002", "City Hospital"),
    ("Sunrise Clinic", "sunrise@abha.dev", "abha1234", "hospital", None, "+91-90000-00003", "Sunrise Clinic"),
    ("Aarav Mehta", "aarav@abha.dev", "abha1234", "patient", "11001100110001", "+91-90000-00011", None),
    ("Diya Sharma", "diya@abha.dev", "abha1234", "patient", "22002200220002", "+91-90000-00012", None),
    ("Rohan Verma", "rohan@abha.dev", "abha1234", "patient", "33003300330003", "+91-90000-00013", None),
    ("Isha Patil", "isha@abha.dev", "abha1234", "patient", "44004400440004", "+91-90000-00014", None),
    ("Kabir Nair", "kabir@abha.dev", "abha1234", "patient", "55005500550005", "+91-90000-00015", None),
    ("Anaya Gupta", "anaya@abha.dev", "abha1234", "patient", "66006600660006", "+91-90000-00016", None),
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(models.User).filter_by(email="admin@abha.dev").first():
        print("identity: already seeded")
        return
    ids = {}
    for name, email, pw, role, abha, phone, hosp in ACCOUNTS:
        u = models.User(
            name=name,
            email=email,
            password_hash=security.hash_password(pw),
            role=role,
            abha_id=abha,
            phone=phone,
            hospital_name=hosp,
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        ids[email] = u.id

    city_id = ids["city@abha.dev"]
    sunrise_id = ids["sunrise@abha.dev"]
    # Every patient grants City Hospital standing consent; two grant Sunrise too.
    for email in ["aarav@abha.dev", "diya@abha.dev", "rohan@abha.dev", "isha@abha.dev"]:
        db.add(models.ConsentArtifact(patient_id=ids[email], hospital_id=city_id))
    db.add(models.ConsentArtifact(patient_id=ids["aarav@abha.dev"], hospital_id=sunrise_id))
    db.commit()
    print("identity: seeded", len(ACCOUNTS), "users")


if __name__ == "__main__":
    seed()
