import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from abdm_app import models
from abdm_app.deps import get_db, get_current_user, UserClaim

router = APIRouter()


def _log(db: Session, endpoint: str, payload: str, status_code: int = 200):
    db.add(
        models.AbdmLog(
            direction="IN",
            endpoint=endpoint,
            payload_snippet=payload[:120],
            status_code=status_code,
            latency_ms=max(1, int(time.perf_counter() % 1 * 1000)),
        )
    )
    db.commit()


@router.post("/sandbox/abha/search")
def abha_search(body: dict, user: UserClaim = Depends(get_current_user), db: Session = Depends(get_db)):
    """Simulated ABHA registry search: given name/phone hints, returns a 14-digit ID."""
    started = time.perf_counter()
    seed = body.get("hint", "0")
    abha = str(abs(hash(str(seed) + "abha")))[:14].zfill(14)
    _log(db, "/sandbox/abha/search", str(body), 200)
    return {
        "abha_id": abha,
        "name_masked": (body.get("name", "R")[0] + "****"),
        "txn_id": f"SBX-{abs(hash(abha)) % 10**8:08d}",
        "latency_ms": int((time.perf_counter() - started) * 1000),
    }


@router.post("/sandbox/consent/initiate")
def consent_initiate(
    body: dict,
    user: UserClaim = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Simulated HIU consent request initiation."""
    started = time.perf_counter()
    consent_id = f"CN-{abs(hash(str(body))) % 10**8:08d}"
    _log(db, "/sandbox/consent/initiate", str(body), 200)
    return {
        "consent_request_id": consent_id,
        "status": "PENDING",
        "purpose": body.get("purpose", "CAREMGT"),
        "hi_types": body.get("hi_types", ["OPConsultation", "DiagnosticReport"]),
        "expires_at": "2030-01-01T00:00:00Z",
        "latency_ms": int((time.perf_counter() - started) * 1000),
    }


@router.post("/sandbox/care-context/link")
def care_context_link(
    body: dict,
    user: UserClaim = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    started = time.perf_counter()
    ctx = models.CareContext(
        patient_id=int(body.get("patient_id", 0)),
        record_ref=body.get("record_ref", ""),
        status="LINKED",
    )
    db.add(ctx)
    db.commit()
    db.refresh(ctx)
    _log(db, "/sandbox/care-context/link", str(body), 200)
    return {
        "care_context_id": ctx.id,
        "status": ctx.status,
        "linked_at": ctx.linked_at.isoformat(),
        "latency_ms": int((time.perf_counter() - started) * 1000),
    }


@router.post("/sandbox/nhcx-forward")
def nhcx_forward(body: dict, user: UserClaim = Depends(get_current_user), db: Session = Depends(get_db)):
    """Trace a NHCX-bound claim payload into the ABDM log for the audit trail."""
    _log(db, "/sandbox/nhcx-forward", str(body), 200)
    return {"forwarded": True}


@router.post("/fhir/convert")
def fhir_convert(
    body: dict,
    user: UserClaim = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Convert a hospital record dict into FHIR + a linked care context.

    Body: record {id,type,title,created_at,details,hospital_name}, patient {abha_id,name}
    """
    from abdm_app import fhir_builder

    if user.role not in ("hospital", "admin"):
        raise HTTPException(status_code=403, detail="Only hospitals convert records")
    record = body.get("record", {})
    patient = body.get("patient", {})
    try:
        resource = fhir_builder.record_to_fhir(record, patient)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    bundle = fhir_builder.build_bundle([resource], f"bundle-record-{record.get('id', 0)}")
    ctx = models.CareContext(patient_id=int(body.get("patient_user_id", 0)), record_ref=str(record.get("id", "")))
    db.add(ctx)
    db.commit()
    _log(db, "/fhir/convert", fhir_builder.dumps(bundle), 200)
    return {"fhir_bundle": bundle, "care_context_id": ctx.id}


@router.get("/logs")
def get_logs(
    limit: int = 100,
    user: UserClaim = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    rows = db.query(models.AbdmLog).order_by(models.AbdmLog.ts.desc()).limit(limit).all()
    return {
        "logs": [
            {
                "id": l.id,
                "ts": l.ts.isoformat(),
                "direction": l.direction,
                "endpoint": l.endpoint,
                "payload_snippet": l.payload_snippet,
                "status_code": l.status_code,
                "latency_ms": l.latency_ms,
            }
            for l in rows
        ]
    }


@router.get("/care-contexts")
def list_care_contexts(user: UserClaim = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    rows = db.query(models.CareContext).order_by(models.CareContext.linked_at.desc()).limit(200).all()
    return {
        "care_contexts": [
            {"id": c.id, "patient_id": c.patient_id, "record_ref": c.record_ref, "status": c.status, "linked_at": c.linked_at.isoformat()}
            for c in rows
        ]
    }
