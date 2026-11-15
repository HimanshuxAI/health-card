import json
import secrets
import time
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.deps import get_db, get_current_user, UserClaim
from services.shared.config import SHARED_TOKEN
from app.crypto import seal, unseal

router = APIRouter()


def _profile_dict(p: models.PatientProfile | None, patient_name: str = "", abha_id: str | None = None) -> dict:
    if not p:
        return {
            "full_name": patient_name,
            "abha_id": abha_id,
            "blood_group": "",
            "allergies": [],
            "chronic_conditions": [],
            "medications": [],
            "emergency_contacts": [],
        }
    return {
        "full_name": patient_name or p.full_name,
        "abha_id": abha_id,
        "blood_group": p.blood_group,
        "allergies": json.loads(p.allergies),
        "chronic_conditions": json.loads(p.chronic_conditions),
        "medications": json.loads(p.medications),
        "emergency_contacts": json.loads(p.emergency_contacts),
    }


@router.put("/emergency/profile")
def save_emergency_profile(
    body: dict,
    user: UserClaim = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Patient saves their emergency (trauma) profile. Fields: blood_group,
    allergies, chronic_conditions, medications, emergency_contacts."""
    if user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patients own an emergency profile")
    p = db.query(models.PatientProfile).filter_by(user_id=user.id).first()
    if not p:
        p = models.PatientProfile(user_id=user.id)
        db.add(p)
    p.full_name = body.get("full_name", user.name)
    p.blood_group = body.get("blood_group", "")
    p.allergies = json.dumps(body.get("allergies", []))
    p.chronic_conditions = json.dumps(body.get("chronic_conditions", []))
    p.medications = json.dumps(body.get("medications", []))
    p.emergency_contacts = json.dumps(body.get("emergency_contacts", []))
    p.updated_at = datetime.utcnow()
    db.commit()

    # Re-seal the trauma profile every time the profile changes.
    data_hex, nonce_hex, sig = seal(_profile_dict(p, user.name, user.abha_id))
    tp = db.query(models.TraumaProfile).filter_by(patient_id=user.id).first()
    if not tp:
        tp = models.TraumaProfile(patient_id=user.id)
        db.add(tp)
    tp.encrypted_blob = data_hex
    tp.nonce = nonce_hex
    tp.hmac_sha256 = sig
    tp.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "updated_at": tp.updated_at.isoformat()}


@router.get("/emergency/profile")
def get_emergency_profile(user: UserClaim = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patients own an emergency profile")
    p = db.query(models.PatientProfile).filter_by(user_id=user.id).first()
    return _profile_dict(p, user.name, user.abha_id)


@router.post("/emergency/qr")
def create_qr_token(user: UserClaim = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patients generate emergency QR tokens")
    # deactivate old tokens
    db.query(models.QrToken).filter_by(patient_id=user.id).update({"active": False})
    token = secrets.token_hex(16)
    db.add(models.QrToken(patient_id=user.id, token=token))
    db.commit()
    return {"token": token, "scan_path": f"/scan?t={token}"}


@router.get("/emergency/resolve/{token}")
def resolve_token(token: str, db: Session = Depends(get_db)):
    """PUBLIC endpoint: resolve an emergency QR token to the decrypted trauma profile."""
    import time

    started = time.perf_counter()
    qt = db.query(models.QrToken).filter_by(token=token).first()
    if not qt:
        raise HTTPException(status_code=404, detail="Unknown emergency token")
    if not qt.active:
        raise HTTPException(status_code=410, detail="This emergency card has been replaced")

    tp = db.query(models.TraumaProfile).filter_by(patient_id=qt.patient_id).first()
    if not tp:
        raise HTTPException(status_code=404, detail="No emergency profile on file")
    profile = unseal(tp.encrypted_blob, tp.nonce, tp.hmac_sha256)
    if profile is None:
        raise HTTPException(status_code=500, detail="Trauma profile failed integrity check")

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return {"profile": profile, "retrieved_in_ms": elapsed_ms, "resolved_at": datetime.utcnow().isoformat()}


@router.get("/internal/profile/{patient_id}")
def internal_profile(
    patient_id: int,
    x_internal_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Internal endpoint for SOS service to fetch emergency contacts."""
    if x_internal_token != SHARED_TOKEN:
        raise HTTPException(status_code=403, detail="Internal only")
    p = db.query(models.PatientProfile).filter_by(user_id=patient_id).first()
    profile = _profile_dict(p, abha_id=None)
    return profile
