"""Seed the ABDM service: care contexts and integration trace logs."""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # repo root

from abdm_app import models
from abdm_app.main import engine, SessionLocal
from services.shared.db import Base

TRACE = [
    ("OUT", "/v1/registration/health-id/generate", '{"name": "Aarav Mehta"}', 200, 141),
    ("IN", "/v1/hip/link/care-context", '{"careContexts": [{"reference": "rec-1"}]}', 200, 96),
    ("OUT", "/v1/consent-requests/init", '{"purpose": "CAREMGT"}', 200, 187),
    ("IN", "/v1/consents/hiu/notify", '{"consentStatus": "GRANTED"}', 200, 88),
    ("IN", "/v1/links/context/confirm", '{"status": "ACTIVE"}', 200, 104),
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(models.AbdmLog).first():
        print("abdm: already seeded")
        return
    base = datetime.now(timezone.utc) - timedelta(hours=6)
    for i, (direction, endpoint, payload, status, latency) in enumerate(TRACE):
        db.add(
            models.AbdmLog(
                direction=direction,
                endpoint=endpoint,
                payload_snippet=payload,
                status_code=status,
                latency_ms=latency,
                ts=base + timedelta(minutes=7 * i),
            )
        )
    db.commit()
    print("abdm: seeded", len(TRACE), "trace logs")


if __name__ == "__main__":
    seed()
