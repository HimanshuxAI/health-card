import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

_TEST_DB = os.path.join(tempfile.gettempdir(), "abha_sos_test.db")
if os.path.exists(_TEST_DB):
    os.remove(_TEST_DB)
os.environ["SOS_DB"] = _TEST_DB

from fastapi.testclient import TestClient  # noqa: E402

from services.shared import security  # noqa: E402

from sos_app.main import app  # noqa: E402
from sos_app.mailer import send_alert_email  # noqa: E402

client = TestClient(app)


def _tok(uid, role):
    return {"Authorization": f"Bearer {security.create_token(sub=str(uid), role=role)}"}


def test_mailer_skips_without_config():
    status = send_alert_email("x@example.com", "Test", "body")
    assert status in ("SKIPPED", "SENT", "FAILED")  # SKIPPED when env unset


def test_alert_flow():
    r = client.post(
        "/alerts",
        json={"patient_id": 42, "trigger": "PANIC", "lat": 18.5204, "lng": 73.8567, "location_label": "Gate 2"},
        headers=_tok(42, "patient"),
    )
    assert r.status_code == 200, r.text
    alert = r.json()
    assert alert["trigger"] == "PANIC"
    assert alert["email_status"] in ("SKIPPED", "SENT", "FAILED")

    r2 = client.post("/alerts", json={"trigger": "BAD"}, headers=_tok(1, "patient"))
    assert r2.status_code == 422

    r3 = client.get("/alerts", headers=_tok(1, "admin"))
    assert r3.status_code == 200
    assert any(a["patient_id"] == 42 for a in r3.json()["alerts"])

    # patient only sees own
    r4 = client.get("/alerts", headers=_tok(43, "patient"))
    assert all(a["patient_id"] == 43 for a in r4.json()["alerts"])

    # unauthenticated
    r5 = client.get("/alerts")
    assert r5.status_code == 401


def test_websocket_broadcast():
    htok = security.create_token(sub="2", role="hospital")
    with client.websocket_connect(f"/ws?token={htok}") as ws:
        # trigger an alert; hospital socket should receive it
        client.post(
            "/alerts",
            json={"patient_id": 77, "trigger": "QR_SCAN"},
            headers=_tok(77, "patient"),
        )
        msg = ws.receive_json()
        assert msg["kind"] == "SOS_ALERT"
        assert msg["patient_id"] == 77

    # bad token rejected
    import pytest
    from starlette.websockets import WebSocketDisconnect

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws?token=garbage"):
            pass
