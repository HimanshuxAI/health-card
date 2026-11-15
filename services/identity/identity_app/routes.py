import re
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from identity_app import models, schemas
from identity_app.deps import get_db, get_current_user
from services.shared import security

router = APIRouter()

ABHA_RE = re.compile(r"^\d{14}$")


@router.post("/register", response_model=schemas.TokenOut)
def register(body: schemas.RegisterIn, db: Session = Depends(get_db)):
    if db.query(models.User).filter_by(email=body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    if body.role == "hospital" and not body.hospital_name:
        raise HTTPException(status_code=422, detail="hospital_name is required for hospital accounts")
    if body.abha_id and not ABHA_RE.match(body.abha_id):
        raise HTTPException(status_code=422, detail="ABHA ID must be exactly 14 digits")
    if body.abha_id and db.query(models.User).filter_by(abha_id=body.abha_id).first():
        raise HTTPException(status_code=409, detail="ABHA ID already linked to another account")

    user = models.User(
        name=body.name,
        email=body.email,
        password_hash=security.hash_password(body.password),
        role=body.role,
        abha_id=body.abha_id,
        phone=body.phone,
        hospital_name=body.hospital_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = security.create_token(sub=str(user.id), role=user.role, abha_id=user.abha_id)
    return schemas.TokenOut(
        access_token=token, role=user.role, abha_id=user.abha_id, name=user.name, user_id=user.id
    )


@router.post("/login", response_model=schemas.TokenOut)
def login(body: schemas.LoginIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(email=body.email).first()
    if not user or not security.verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = security.create_token(sub=str(user.id), role=user.role, abha_id=user.abha_id)
    return schemas.TokenOut(
        access_token=token, role=user.role, abha_id=user.abha_id, name=user.name, user_id=user.id
    )


@router.get("/me")
def me(user: models.User = Depends(get_current_user)):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "abha_id": user.abha_id,
        "phone": user.phone,
        "hospital_name": user.hospital_name,
    }


@router.post("/ekyc/verify", response_model=schemas.EkycOut)
def ekyc_verify(
    body: schemas.EkycIn,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not ABHA_RE.match(body.abha_id):
        raise HTTPException(status_code=422, detail="ABHA ID must be exactly 14 digits")

    # Simulated ABDM registry lookup: derive a masked holder name deterministically.
    holder = user.name
    if not holder:
        holder = "REGISTRY HOLDER"
    parts = holder.split()
    masked = " ".join(p[0] + "****" for p in parts) if parts else "R****"

    # If the ABHA id is already linked to another account, surface that holder.
    existing = db.query(models.User).filter_by(abha_id=body.abha_id).first()
    if existing and existing.id != user.id:
        holder = existing.name
        parts = holder.split()
        masked = " ".join(p[0] + "****" for p in parts) if parts else "R****"

    # Link to the requesting user if free.
    if not user.abha_id:
        user.abha_id = body.abha_id
        db.commit()

    return schemas.EkycOut(
        verified=True,
        abha_id=body.abha_id,
        txn_id=uuid.uuid4().hex,
        name_masked=masked,
        ts=datetime.now(timezone.utc),
    )


@router.post("/consents", response_model=schemas.ConsentOut)
def grant_consent(
    body: schemas.ConsentIn,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = db.get(models.User, body.patient_id)
    hospital = db.get(models.User, body.hospital_id)
    if not patient or patient.role != "patient":
        raise HTTPException(status_code=404, detail="Patient not found")
    if not hospital or hospital.role != "hospital":
        raise HTTPException(status_code=404, detail="Hospital not found")
    # Only the patient (or admin) may grant.
    if user.role == "patient" and user.id != patient.id:
        raise HTTPException(status_code=403, detail="Patients may only grant their own consent")
    existing = (
        db.query(models.ConsentArtifact)
        .filter_by(patient_id=body.patient_id, hospital_id=body.hospital_id, status="ACTIVE")
        .first()
    )
    if existing:
        return existing
    artifact = models.ConsentArtifact(
        patient_id=body.patient_id,
        hospital_id=body.hospital_id,
        scope=body.scope,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


@router.post("/consents/{consent_id}/revoke", response_model=schemas.ConsentOut)
def revoke_consent(consent_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    artifact = db.get(models.ConsentArtifact, consent_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Consent not found")
    if user.role == "patient" and user.id != artifact.patient_id:
        raise HTTPException(status_code=403, detail="Not your consent")
    artifact.status = "REVOKED"
    db.commit()
    db.refresh(artifact)
    return artifact


@router.get("/consents")
def list_consents(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(models.ConsentArtifact).filter_by(status="ACTIVE")
    if user.role == "patient":
        q = q.filter_by(patient_id=user.id)
    elif user.role == "hospital":
        q = q.filter_by(hospital_id=user.id)
    rows = [
        {
            "id": c.id,
            "patient_id": c.patient_id,
            "hospital_id": c.hospital_id,
            "scope": c.scope,
            "status": c.status,
            "granted_at": c.granted_at.isoformat(),
        }
        for c in q.all()
    ]
    return {"consents": rows}


@router.get("/consents/check")
def check_consent(
    patient_id: int,
    hospital_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Internal-style check used by the records service before hospital access."""
    active = (
        db.query(models.ConsentArtifact)
        .filter_by(patient_id=patient_id, hospital_id=hospital_id, status="ACTIVE")
        .first()
    )
    if not active:
        raise HTTPException(status_code=403, detail="No active consent for this patient")
    patient = db.get(models.User, patient_id)
    hospital = db.get(models.User, hospital_id)
    return {
        "granted": True,
        "patient_name": patient.name if patient else None,
        "patient_abha_id": patient.abha_id if patient else None,
        "hospital_name": hospital.name if hospital else None,
        "scope": active.scope,
    }
