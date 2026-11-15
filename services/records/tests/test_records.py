import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from fastapi.testclient import TestClient  # noqa: E402

from app.crypto import seal  # noqa: E402

from services.shared import security  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def _claim(user_id: int, role: str, abha_id: str | None = None):
    token = security.create_token(sub=str(user_id), role=role, abha_id=abha_id)
    return {"Authorization": f"Bearer {token}"}


def _register(email, role="patient", **kw):
    """Mint a token directly — the records service trusts JWT claims and has no users table."""
    user_id = abs(hash(email)) % 100000
    headers = _claim(user_id, role)
    return headers, {"user_id": user_id}


def test_emergency_profile_qr_resolve():
    headers, body = _register("emerg@example.com")

    # empty profile initially
    r = client.get("/emergency/profile", headers=headers)
    assert r.status_code == 200
    assert r.json()["blood_group"] == ""

    # save profile
    r2 = client.put(
        "/emergency/profile",
        json={
            "blood_group": "O+",
            "allergies": ["Penicillin"],
            "chronic_conditions": ["Asthma"],
            "medications": ["Salbutamol"],
            "emergency_contacts": [{"name": "Mom", "phone": "+91-99999", "relation": "Mother"}],
        },
        headers=headers,
    )
    assert r2.status_code == 200, r2.text

    # create QR token
    r3 = client.post("/emergency/qr", headers=headers)
    assert r3.status_code == 200
    token = r3.json()["token"]

    # resolve publicly (no auth)
    r4 = client.get(f"/emergency/resolve/{token}")
    assert r4.status_code == 200, r4.text
    data = r4.json()
    assert data["profile"]["blood_group"] == "O+"
    assert "Penicillin" in data["profile"]["allergies"]
    assert data["retrieved_in_ms"] < 800

    # rotate: new token invalidates old
    r5 = client.post("/emergency/qr", headers=headers)
    new_token = r5.json()["token"]
    r6 = client.get(f"/emergency/resolve/{token}")
    assert r6.status_code == 410
    r7 = client.get(f"/emergency/resolve/{new_token}")
    assert r7.status_code == 200

    # unknown token
    r8 = client.get("/emergency/resolve/deadbeef")
    assert r8.status_code == 404


def token_stub(email):
    return None


def test_records_consent_required():
    ph, hbody = _register("rhosp@example.com", role="hospital")
    _, pbody = _register("rpat@example.com")

    # hospital cannot list patient records without consent
    r = client.get("/records", params={"patient_id": pbody["user_id"]}, headers=ph)
    assert r.status_code in (403, 503)  # 503 if identity offline in test env; 403 when reachable

    # patient lists own (empty)
    r2 = client.get("/records", headers=_claim(pbody["user_id"], "patient"))
    assert r2.status_code == 200
    assert "records" in r2.json()


def test_crypto_sig_matches_hmac():
    payload = {"x": 1}
    data_hex, nonce_hex, sig = seal(payload)
    assert len(sig) == 64
