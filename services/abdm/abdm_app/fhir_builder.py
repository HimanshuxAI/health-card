"""HL7 FHIR v4 bundle builders for the ABDM interoperability engine."""

import json
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _subject(abha_id: str, name: str) -> dict:
    return {"reference": f"Patient/{abha_id}", "display": name}


def build_diagnostic_report(record: dict, patient: dict) -> dict:
    return {
        "resourceType": "DiagnosticReport",
        "id": f"report-{record['id']}",
        "status": "final",
        "code": {"text": record["title"]},
        "subject": _subject(patient["abha_id"], patient["name"]),
        "effectiveDateTime": record.get("created_at", _now()),
        "performer": [{"display": record.get("hospital_name", "City Hospital")}],
        "conclusion": record.get("details", {}).get("conclusion", ""),
    }


def build_prescription(record: dict, patient: dict) -> dict:
    return {
        "resourceType": "MedicationRequest",
        "id": f"rx-{record['id']}",
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {"text": record["title"]},
        "subject": _subject(patient["abha_id"], patient["name"]),
        "authoredOn": record.get("created_at", _now()),
        "requester": {"display": record.get("hospital_name", "City Hospital")},
        "dosageInstruction": [{"text": record.get("details", {}).get("dosage", "As directed")}],
    }


def build_immunization(record: dict, patient: dict) -> dict:
    return {
        "resourceType": "Immunization",
        "id": f"imm-{record['id']}",
        "status": "completed",
        "vaccineCode": {"text": record["title"]},
        "patient": _subject(patient["abha_id"], patient["name"]),
        "occurrenceDateTime": record.get("created_at", _now()),
    }


def build_bundle(resources: list[dict], bundle_id: str) -> dict:
    return {
        "resourceType": "Bundle",
        "id": bundle_id,
        "type": "document",
        "timestamp": _now(),
        "entry": [{"resource": r} for r in resources],
    }


def record_to_fhir(record: dict, patient: dict) -> dict:
    builders = {
        "DiagnosticReport": build_diagnostic_report,
        "Prescription": build_prescription,
        "Immunization": build_immunization,
    }
    b = builders.get(record.get("type"))
    if not b:
        raise ValueError(f"Unsupported record type: {record.get('type')}")
    return b(record, patient)


def dumps(obj: dict) -> str:
    return json.dumps(obj)
