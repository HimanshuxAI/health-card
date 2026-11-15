import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

_TEST_DB = os.path.join(tempfile.gettempdir(), "abha_abdm_test.db")
if os.path.exists(_TEST_DB):
    os.remove(_TEST_DB)
os.environ["ABDM_DB"] = _TEST_DB

from fastapi.testclient import TestClient  # noqa: E402

from services.shared import security  # noqa: E402

from abdm_app.main import app  # noqa: E402
from abdm_app import fhir_builder  # noqa: E402

client = TestClient(app)


def _admin():
    token = security.create_token(sub="1", role="admin")
    return {"Authorization": f"Bearer {token}"}


def _hosp():
    token = security.create_token(sub="2", role="hospital")
    return {"Authorization": f"Bearer {token}"}


def test_fhir_builders():
    record = {
        "id": 7,
        "type": "DiagnosticReport",
        "title": "CBC Panel",
        "created_at": "2026-11-15T10:00:00Z",
        "details": {"conclusion": "Normal counts"},
    }
    patient = {"abha_id": "12345678901234", "name": "Aarav Mehta"}
    res = fhir_builder.record_to_fhir(record, patient)
    assert res["resourceType"] == "DiagnosticReport"
    assert res["subject"]["reference"] == "Patient/12345678901234"

    rx = fhir_builder.record_to_fhir({**record, "type": "Prescription"}, patient)
    assert rx["resourceType"] == "MedicationRequest"

    imm = fhir_builder.record_to_fhir({**record, "type": "Immunization"}, patient)
    assert imm["resourceType"] == "Immunization"

    bundle = fhir_builder.build_bundle([res], "b1")
    assert bundle["resourceType"] == "Bundle"
    assert bundle["entry"][0]["resource"]["resourceType"] == "DiagnosticReport"

    try:
        fhir_builder.record_to_fhir({**record, "type": "Nope"}, patient)
        assert False, "should have raised"
    except ValueError:
        pass


def test_sandbox_endpoints_log():
    r = client.post("/sandbox/abha/search", json={"hint": "aarav", "name": "Aarav"}, headers=_hosp())
    assert r.status_code == 200
    body = r.json()
    assert len(body["abha_id"]) == 14

    r2 = client.post(
        "/sandbox/consent/initiate",
        json={"patient_id": 1, "purpose": "CAREMGT"},
        headers=_hosp(),
    )
    assert r2.status_code == 200
    assert r2.json()["consent_request_id"].startswith("CN-")

    r3 = client.post(
        "/sandbox/care-context/link",
        json={"patient_id": 1, "record_ref": "rec-7"},
        headers=_hosp(),
    )
    assert r3.status_code == 200

    # logs exist for admin
    r4 = client.get("/logs", headers=_admin())
    assert r4.status_code == 200
    assert len(r4.json()["logs"]) >= 3

    # logs forbidden for hospital
    r5 = client.get("/logs", headers=_hosp())
    assert r5.status_code == 403


def test_fhir_convert_endpoint():
    r = client.post(
        "/fhir/convert",
        json={
            "record": {"id": 7, "type": "Prescription", "title": "Paracetamol 500mg", "created_at": "2026-11-15T10:00:00Z"},
            "patient": {"abha_id": "12345678901234", "name": "Aarav Mehta"},
            "patient_user_id": 11,
        },
        headers=_hosp(),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["fhir_bundle"]["resourceType"] == "Bundle"
    assert body["care_context_id"]
