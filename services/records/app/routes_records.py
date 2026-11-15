import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app import models
from app.deps import get_db, get_current_user, UserClaim
from app.fhir_local import build_record_fhir

router = APIRouter()
IDENTITY_URL = os.getenv("IDENTITY_URL", "http://127.0.0.1:8001")


def _check_consent(patient_id: int, hospital_id: int, auth_header: str | None) -> dict:
    """Ask identity-service whether this hospital may access this patient."""
    try:
        r = httpx.get(
            f"{IDENTITY_URL}/consents/check",
            params={"patient_id": patient_id, "hospital_id": hospital_id},
            headers={"Authorization": auth_header or ""},
            timeout=3,
        )
        if r.status_code == 200:
            return r.json()
        if r.status_code == 403:
            raise HTTPException(status_code=403, detail="No active consent for this patient")
    except httpx.HTTPError:
        pass
    raise HTTPException(status_code=503, detail="Identity service unreachable — cannot verify consent")


@router.post("/records")
def create_record(
    body: dict,
    request: Request,
    user: UserClaim = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "hospital":
        raise HTTPException(status_code=403, detail="Only hospitals create records")
    patient_id = int(body.get("patient_id", 0))
    rtype = body.get("type", "")
    title = body.get("title", "")
    details = body.get("details", {})
    if not patient_id or rtype not in ("Prescription", "DiagnosticReport", "Immunization"):
        raise HTTPException(status_code=422, detail="patient_id and valid type required")

    consent = _check_consent(patient_id, user.id, request.headers.get("authorization"))
    patient_abha = consent.get("patient_abha_id") or f"{patient_id:014d}"
    fhir = build_record_fhir(rtype, title, details, consent.get("patient_name", ""), patient_abha)

    rec = models.HealthRecord(
        patient_id=patient_id, type=rtype, title=title, fhir_json=fhir, created_by=user.id
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {
        "id": rec.id,
        "patient_id": rec.patient_id,
        "type": rec.type,
        "title": rec.title,
        "fhir_json": rec.fhir_json,
        "created_at": rec.created_at.isoformat(),
    }


@router.get("/records/summary")
def records_summary(user: UserClaim = Depends(get_current_user), db: Session = Depends(get_db)):
    """Counts for dashboards. Hospitals see everything; patients see their own."""
    q = db.query(models.HealthRecord)
    if user.role == "patient":
        q = q.filter_by(patient_id=user.id)
    rows = q.all()
    by_type: dict[str, int] = {}
    for r in rows:
        by_type[r.type] = by_type.get(r.type, 0) + 1
    return {"total": len(rows), "by_type": by_type, "patients": len({r.patient_id for r in rows})}


@router.get("/records")
def list_records(
    request: Request,
    patient_id: int | None = None,
    user: UserClaim = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role == "patient":
        target = user.id
    elif user.role == "hospital":
        if not patient_id:
            raise HTTPException(status_code=422, detail="patient_id required")
        _check_consent(patient_id, user.id, request.headers.get("authorization"))
        target = patient_id
    else:  # admin sees all (optionally filtered)
        target = patient_id
    q = db.query(models.HealthRecord)
    if target:
        q = q.filter_by(patient_id=target)
    rows = q.order_by(models.HealthRecord.created_at.desc()).limit(200).all()
    return {
        "records": [
            {
                "id": r.id,
                "patient_id": r.patient_id,
                "type": r.type,
                "title": r.title,
                "fhir_json": r.fhir_json,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]
    }
