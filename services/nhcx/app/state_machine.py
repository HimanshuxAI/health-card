"""NHCX claim state machine + FHIR Claim builder."""

import json
from datetime import datetime, timezone

from app.models import Bill

TRANSITIONS: dict[str, list[str]] = {
    "SUBMITTED": ["ADJUDICATED"],
    "ADJUDICATED": ["APPROVED", "REJECTED"],
    "APPROVED": [],
    "REJECTED": [],
}


def can_transition(current: str, nxt: str) -> bool:
    return nxt in TRANSITIONS.get(current, [])


def validate_transition(current: str, nxt: str) -> None:
    if not can_transition(current, nxt):
        raise ValueError(f"Invalid claim transition: {current} -> {nxt}")


def build_fhir_claim(bill: Bill, claim_id: int) -> dict:
    items = json.loads(bill.line_items)
    return {
        "resourceType": "Claim",
        "id": f"claim-{claim_id}",
        "status": "active",
        "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/claim-type", "code": "institutional"}]},
        "use": "claim",
        "patient": {"reference": f"Patient/{bill.patient_abha_id or bill.patient_id}", "display": ""},
        "billablePeriod": {"start": bill.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if bill.created_at else _now()},
        "insurer": {"display": "NHCX Simulated Insurer"},
        "provider": {"reference": f"Organization/hospital-{bill.hospital_id}"},
        "item": [
            {
                "sequence": i + 1,
                "productOrService": {"text": it.get("description", "")},
                "net": {"value": float(it.get("amount", 0)), "currency": "INR"},
            }
            for i, it in enumerate(items)
        ],
        "total": {"value": float(bill.total), "currency": "INR"},
    }


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
