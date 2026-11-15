import json
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.websockets import WebSocket
from sqlalchemy.orm import Session

from sos_app import models
from sos_app.deps import get_db, get_current_user, UserClaim
from sos_app.mailer import send_alert_email
from sos_app.ws import manager

router = APIRouter()
RECORDS_URL = os.getenv("RECORDS_URL", "http://127.0.0.1:8002")
SHARED_TOKEN = os.getenv("SHARED_TOKEN", "internal-demo-token")


def _alert_out(a: models.Alert) -> dict:
    return {
        "id": a.id,
        "patient_id": a.patient_id,
        "patient_name": a.patient_name,
        "trigger": a.trigger,
        "lat": a.lat,
        "lng": a.lng,
        "location_label": a.location_label,
        "notified_contacts": json.loads(a.notified_contacts),
        "email_status": a.email_status,
        "created_at": a.created_at.isoformat(),
    }


@router.post("/alerts")
async def create_alert(body: dict, user: UserClaim = Depends(get_current_user), db: Session = Depends(get_db)):
    patient_id = int(body.get("patient_id", 0)) or user.id
    trigger = body.get("trigger", "PANIC")
    if trigger not in ("PANIC", "QR_SCAN"):
        raise HTTPException(status_code=422, detail="trigger must be PANIC or QR_SCAN")

    # Fetch emergency contacts from the records service (best-effort).
    contacts: list[dict] = []
    patient_name = body.get("patient_name", f"Patient {patient_id}")
    try:
        r = httpx.get(
            f"{RECORDS_URL}/internal/profile/{patient_id}",
            headers={"X-Internal-Token": SHARED_TOKEN},
            timeout=3,
        )
        if r.status_code == 200:
            profile = r.json()
            contacts = profile.get("emergency_contacts", [])
            if profile.get("full_name"):
                patient_name = profile["full_name"]
    except httpx.HTTPError:
        pass

    lat = body.get("lat")
    lng = body.get("lng")
    alert = models.Alert(
        patient_id=patient_id,
        patient_name=patient_name,
        trigger=trigger,
        lat=float(lat) if lat is not None else None,
        lng=float(lng) if lng is not None else None,
        location_label=body.get("location_label", ""),
        notified_contacts=json.dumps(contacts),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    # Email emergency contacts (never blocks the alert).
    statuses = []
    loc = f"lat {lat}, lng {lng}" if lat is not None else "location unavailable"
    body_text = (
        f"EMERGENCY ALERT\n\nPatient: {patient_name}\nTrigger: {trigger}\n"
        f"Location: {loc}\nTime: {alert.created_at.isoformat()}\n\n"
        f"Open the ABHA Health Card app for the full emergency profile."
    )
    for c in contacts:
        to = c.get("email", "")
        if to:
            statuses.append(send_alert_email(to, f"ABHA SOS: {patient_name}", body_text))
    alert.email_status = ",".join(statuses) if statuses else "SKIPPED"
    db.commit()
    db.refresh(alert)

    # Broadcast to every connected dashboard over WebSocket (after final state).
    payload = _alert_out(alert)
    payload["kind"] = "SOS_ALERT"
    await manager.broadcast(payload)

    return _alert_out(alert)


@router.get("/alerts")
def list_alerts(user: UserClaim = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(models.Alert)
    if user.role == "patient":
        q = q.filter_by(patient_id=user.id)
    rows = q.order_by(models.Alert.created_at.desc()).limit(200).all()
    return {"alerts": [_alert_out(a) for a in rows]}


@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket, token: str = ""):
    from services.shared import security

    payload = security.decode_token(token)
    if not payload or payload.get("role") not in ("hospital", "admin"):
        await websocket.close(code=4401)
        return
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive; incoming messages are ignored pings.
            await websocket.receive_text()
    except Exception:
        manager.disconnect(websocket)
