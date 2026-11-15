import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

os.environ.setdefault("NHCX_DELAY", "0.05")

from fastapi.testclient import TestClient  # noqa: E402

from services.shared import security  # noqa: E402

from app.main import app  # noqa: E402
from app.state_machine import can_transition, validate_transition  # noqa: E402

client = TestClient(app)


def _hosp(uid=2):
    return {"Authorization": f"Bearer {security.create_token(sub=str(uid), role='hospital')}"}


def _admin():
    return {"Authorization": f"Bearer {security.create_token(sub='1', role='admin')}"}


def test_state_machine():
    assert can_transition("SUBMITTED", "ADJUDICATED")
    assert can_transition("ADJUDICATED", "APPROVED")
    assert can_transition("ADJUDICATED", "REJECTED")
    assert not can_transition("SUBMITTED", "APPROVED")
    assert not can_transition("APPROVED", "REJECTED")
    try:
        validate_transition("APPROVED", "REJECTED")
        assert False
    except ValueError:
        pass


def test_bill_claim_flow():
    h = _hosp(21)
    r = client.post(
        "/bills",
        json={
            "patient_id": 55,
            "patient_abha_id": "12345678901234",
            "line_items": [{"description": "OPD Consultation", "amount": 800}, {"description": "CBC Test", "amount": 450}],
        },
        headers=h,
    )
    assert r.status_code == 200, r.text
    bill = r.json()
    assert bill["total"] == 1250

    r2 = client.post("/claims", json={"bill_id": bill["id"]}, headers=h)
    assert r2.status_code == 200, r2.text
    claim = r2.json()
    assert claim["status"] == "SUBMITTED"
    assert '"resourceType": "Claim"' in claim["fhir_claim_json"] or '"resourceType":"Claim"' in claim["fhir_claim_json"]

    # duplicate claim -> 409
    r3 = client.post("/claims", json={"bill_id": bill["id"]}, headers=h)
    assert r3.status_code == 409

    # patient cannot adjudicate
    r4 = client.post(f"/claims/{claim['id']}/adjudicate", headers=_hosp(55))
    assert r4.status_code == 403

    # admin adjudicates -> cheap claim approved
    r5 = client.post(f"/claims/{claim['id']}/adjudicate", headers=_admin())
    assert r5.status_code == 200, r5.text
    body = r5.json()
    assert body["status"] == "APPROVED"
    assert body["out_of_pocket"] == 0.0

    # adjudicating again -> 409
    r6 = client.post(f"/claims/{claim['id']}/adjudicate", headers=_admin())
    assert r6.status_code == 409


def test_expensive_claim_rejected():
    h = _hosp(22)
    r = client.post(
        "/bills",
        json={
            "patient_id": 56,
            "patient_abha_id": "99999999999999",
            "line_items": [{"description": "ICU Stay 5 days", "amount": 95000}],
        },
        headers=h,
    )
    bill = r.json()
    r2 = client.post("/claims", json={"bill_id": bill["id"]}, headers=h)
    claim = r2.json()
    r3 = client.post(f"/claims/{claim['id']}/adjudicate", headers=_admin())
    body = r3.json()
    assert body["status"] == "REJECTED"
    assert body["out_of_pocket"] == 95000
