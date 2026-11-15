"""Local minimal FHIR v4 record builders used by the records service.

The ABDM service owns the rich bundle builder; these produce the
per-record resource stored on each HealthRecord row.
"""

from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_record_fhir(rtype: str, title: str, details: dict, patient_name: str, patient_abha: str) -> str:
    import json

    subject = {"reference": f"Patient/{patient_abha}", "display": patient_name}
    if rtype == "DiagnosticReport":
        resource = {
            "resourceType": "DiagnosticReport",
            "status": "final",
            "code": {"text": title},
            "subject": subject,
            "effectiveDateTime": _now(),
            "conclusion": details.get("conclusion", ""),
            "result": [
                {"display": d.get("name", ""), "valueQuantity": {"value": d.get("value")}}
                for d in details.get("observations", [])
            ],
        }
    elif rtype == "Immunization":
        resource = {
            "resourceType": "Immunization",
            "status": "completed",
            "vaccineCode": {"text": title},
            "patient": subject,
            "occurrenceDateTime": _now(),
        }
    else:  # Prescription / MedicationRequest
        resource = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "medicationCodeableConcept": {"text": title},
            "subject": subject,
            "authoredOn": _now(),
            "dosageInstruction": [{"text": details.get("dosage", "As directed")}],
        }
    return json.dumps(resource)
