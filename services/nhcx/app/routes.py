import asyncio
import os
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.deps import get_db, get_current_user, UserClaim
from app.state_machine import build_fhir_claim, can_transition

router = APIRouter()
ABDM_URL = os.getenv("ABDM_URL", "http://127.0.0.1:8003")
NHCX_DELAY = float(os.getenv("NHCX_DELAY", "3"))


@router.post("/bills")
def create_bill(body: dict, user: UserClaim = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "hospital":
        raise HTTPException(status_code=403, detail="Only hospitals create bills")
    items = body.get("line_items", [])
    if not items:
        raise HTTPException(status_code=422, detail="At least one line item required")
    total = sum(float(i.get("amount", 0)) for i in items)
    bill = models.Bill(
        hospital_id=user.id,
        patient_id=int(body.get("patient_id", 0)),
        patient_abha_id=str(body.get("patient_abha_id", "")),
        line_items=str(items).replace("'", '"'),  # normalize JSON-ish
        total=total,
    )
    bill.line_items = __import__("json").dumps(items)
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return _bill_out(bill)


@router.get("/bills")
def list_bills(user: UserClaim = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(models.Bill)
    if user.role == "hospital":
        q = q.filter_by(hospital_id=user.id)
    elif user.role == "patient":
        q = q.filter_by(patient_id=user.id)
    rows = q.order_by(models.Bill.created_at.desc()).limit(200).all()
    return {"bills": [_bill_out(b) for b in rows]}


def _bill_out(b: models.Bill) -> dict:
    return {
        "id": b.id,
        "hospital_id": b.hospital_id,
        "patient_id": b.patient_id,
        "patient_abha_id": b.patient_abha_id,
        "line_items": __import__("json").loads(b.line_items),
        "total": b.total,
        "created_at": b.created_at.isoformat(),
    }


@router.post("/claims")
async def create_claim(body: dict, user: UserClaim = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "hospital":
        raise HTTPException(status_code=403, detail="Only hospitals submit claims")
    bill = db.get(models.Bill, int(body.get("bill_id", 0)))
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    existing = db.query(models.Claim).filter_by(bill_id=bill.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="A claim already exists for this bill")

    claim = models.Claim(bill_id=bill.id, status="SUBMITTED")
    db.add(claim)
    db.commit()
    db.refresh(claim)

    # Attach the FHIR Claim resource now that we have an id.
    claim.fhir_claim_json = __import__("json").dumps(build_fhir_claim(bill, claim.id))
    db.commit()

    # Trace the outbound NHCX submission in the ABDM audit log (best-effort).
    try:
        httpx.post(
            f"{ABDM_URL}/sandbox/nhcx-forward",
            json={"claim_id": claim.id, "bill_id": bill.id, "total": bill.total, "status": "SUBMITTED"},
            headers={"Authorization": f"Bearer {os.getenv('INTERNAL_JWT', '')}"},
            timeout=2,
        )
    except httpx.HTTPError:
        pass

    return _claim_out(claim, db)


@router.get("/claims")
def list_claims(user: UserClaim = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(models.Claim)
    rows = q.order_by(models.Claim.created_at.desc()).limit(200).all()
    visible = []
    for c in rows:
        bill = db.get(models.Bill, c.bill_id)
        if user.role == "hospital" and bill.hospital_id != user.id:
            continue
        if user.role == "patient" and bill.patient_id != user.id:
            continue
        visible.append(_claim_out(c, db))
    return {"claims": visible}


@router.post("/claims/{claim_id}/adjudicate")
async def adjudicate(claim_id: int, user: UserClaim = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only NHCX oversight (admin) can adjudicate")
    claim = db.get(models.Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if not can_transition(claim.status, "ADJUDICATED"):
        raise HTTPException(status_code=409, detail=f"Claim in terminal state: {claim.status}")

    # Simulated insurer processing delay for demo drama.
    await asyncio.sleep(NHCX_DELAY)

    bill = db.get(models.Bill, claim.bill_id)
    claim.status = "ADJUDICATED"
    if bill.total <= 50000:
        claim.status = "APPROVED"
        claim.approved_amount = bill.total
        claim.out_of_pocket = 0.0
        claim.insurer_note = "Claim approved in full. No out-of-pocket expense."
    else:
        claim.status = "REJECTED"
        claim.approved_amount = 0.0
        claim.out_of_pocket = bill.total
        claim.insurer_note = "Rejected: exceeds coverage limit for itemized claim."
    claim.adjudicated_at = datetime.utcnow()
    db.commit()
    db.refresh(claim)

    try:
        httpx.post(
            f"{ABDM_URL}/sandbox/nhcx-forward",
            json={"claim_id": claim.id, "status": claim.status, "note": claim.insurer_note},
            timeout=2,
        )
    except httpx.HTTPError:
        pass

    return _claim_out(claim, db)


def _claim_out(c: models.Claim, db: Session) -> dict:
    bill = db.get(models.Bill, c.bill_id)
    return {
        "id": c.id,
        "bill_id": c.bill_id,
        "patient_id": bill.patient_id if bill else 0,
        "total": bill.total if bill else 0.0,
        "fhir_claim_json": c.fhir_claim_json,
        "status": c.status,
        "insurer_note": c.insurer_note,
        "approved_amount": c.approved_amount,
        "out_of_pocket": c.out_of_pocket,
        "adjudicated_at": c.adjudicated_at.isoformat() if c.adjudicated_at else None,
        "created_at": c.created_at.isoformat(),
    }
