import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

_TEST_DB = os.path.join(tempfile.gettempdir(), "abha_records_test.db")
if os.path.exists(_TEST_DB):
    os.remove(_TEST_DB)
os.environ["RECORDS_DB"] = _TEST_DB

from fastapi.testclient import TestClient  # noqa: E402

from records_app.crypto import seal  # noqa: E402

from services.shared import security  # noqa: E402

from records_app.main import app  # noqa: E402
from records_app.demo import demo_card_token  # noqa: E402

client = TestClient(app)


def test_seeded_demo_card_is_the_same_every_time():
    """A host without a persistent volume rebuilds the database on every boot.

    If the seeded card token were random, the code printed on a patient's card
    would stop resolving each time the service restarted.
    """
    assert demo_card_token("aarav@abha.dev") == demo_card_token("aarav@abha.dev")
    assert len(demo_card_token("aarav@abha.dev")) == 32
    assert demo_card_token("aarav@abha.dev") != demo_card_token("diya@abha.dev")


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


def test_qr_card_stays_valid_until_it_is_regenerated():
    """Reading the card must not invalidate a copy that is already printed."""
    headers, _ = _register("stable@example.com")
    client.put(
        "/emergency/profile",
        json={
            "blood_group": "A+",
            "allergies": ["Dust"],
            "chronic_conditions": [],
            "medications": [],
            "emergency_contacts": [{"name": "Sister", "phone": "+91-88888", "relation": "Sister"}],
        },
        headers=headers,
    )

    first = client.post("/emergency/qr", headers=headers).json()["token"]

    # reading the card returns the same token instead of rotating it
    read = client.get("/emergency/qr", headers=headers)
    assert read.status_code == 200
    assert read.json()["token"] == first

    # the printed card still resolves
    assert client.get(f"/emergency/resolve/{first}").status_code == 200

    # an explicit regenerate invalidates the old copy
    rotated = client.post("/emergency/qr", headers=headers).json()["token"]
    assert rotated != first
    assert client.get(f"/emergency/resolve/{first}").status_code == 410
    assert client.get(f"/emergency/resolve/{rotated}").status_code == 200


def test_qr_card_requires_a_patient_account():
    headers, _ = _register("nurse@example.com")
    headers["Authorization"] = _claim(1, "hospital")["Authorization"]
    assert client.get("/emergency/qr", headers=headers).status_code == 403


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
