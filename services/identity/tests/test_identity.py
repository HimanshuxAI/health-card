import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

# Isolated test database so runs are repeatable.
_TEST_DB = os.path.join(tempfile.gettempdir(), "abha_identity_test.db")
if os.path.exists(_TEST_DB):
    os.remove(_TEST_DB)
os.environ["IDENTITY_DB"] = _TEST_DB

from fastapi.testclient import TestClient  # noqa: E402

from identity_app.main import app  # noqa: E402

client = TestClient(app)


def test_register_login_me_flow():
    email = "testreg@example.com"
    r = client.post(
        "/register",
        json={"name": "Test User", "email": email, "password": "pw123456", "role": "patient"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["role"] == "patient"
    token = body["access_token"]

    # duplicate register -> 409
    r2 = client.post(
        "/register",
        json={"name": "Test User", "email": email, "password": "pw123456", "role": "patient"},
    )
    assert r2.status_code == 409

    # login good
    r3 = client.post("/login", json={"email": email, "password": "pw123456"})
    assert r3.status_code == 200
    token3 = r3.json()["access_token"]

    # login bad
    r4 = client.post("/login", json={"email": email, "password": "wrong"})
    assert r4.status_code == 401

    # /me without token -> 401
    r5 = client.get("/me")
    assert r5.status_code == 401

    # /me with token
    r6 = client.get("/me", headers={"Authorization": f"Bearer {token3}"})
    assert r6.status_code == 200
    assert r6.json()["email"] == email

    # hospital register without hospital_name -> 422
    r7 = client.post(
        "/register",
        json={"name": "H", "email": "h@example.com", "password": "pw123456", "role": "hospital"},
    )
    assert r7.status_code == 422


def test_ekyc():
    email = "ekyc@example.com"
    r = client.post(
        "/register",
        json={"name": "Ekyc Person", "email": email, "password": "pw123456", "role": "patient"},
    )
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r2 = client.post("/ekyc/verify", json={"abha_id": "12345678901234"}, headers=headers)
    assert r2.status_code == 200
    body = r2.json()
    assert body["verified"] is True
    assert body["txn_id"]

    r3 = client.post("/ekyc/verify", json={"abha_id": "123"}, headers=headers)
    assert r3.status_code == 422

    r4 = client.post("/ekyc/verify", json={"abha_id": "12345678901234"})
    assert r4.status_code == 401


def test_consent_flow():
    rp = client.post(
        "/register",
        json={"name": "Pat Consent", "email": "pc@example.com", "password": "pw123456", "role": "patient"},
    )
    rh = client.post(
        "/register",
        json={
            "name": "Hosp Consent",
            "email": "hc@example.com",
            "password": "pw123456",
            "role": "hospital",
            "hospital_name": "City Hospital",
        },
    )
    ptok = rp.json()["access_token"]
    pid = rp.json()["user_id"]
    htok = rh.json()["access_token"]
    hid = rh.json()["user_id"]

    # hospital cannot read without consent -> 403
    r = client.get(
        "/consents/check", params={"patient_id": pid, "hospital_id": hid}, headers={"Authorization": f"Bearer {htok}"}
    )
    assert r.status_code == 403

    # patient grants
    r2 = client.post("/consents", json={"patient_id": pid, "hospital_id": hid}, headers={"Authorization": f"Bearer {ptok}"})
    assert r2.status_code == 200

    # now check passes
    r3 = client.get(
        "/consents/check", params={"patient_id": pid, "hospital_id": hid}, headers={"Authorization": f"Bearer {htok}"}
    )
    assert r3.status_code == 200
    assert r3.json()["granted"] is True

    # revoke
    cid = r2.json()["id"]
    r4 = client.post(f"/consents/{cid}/revoke", headers={"Authorization": f"Bearer {ptok}"})
    assert r4.status_code == 200

    r5 = client.get(
        "/consents/check", params={"patient_id": pid, "hospital_id": hid}, headers={"Authorization": f"Bearer {htok}"}
    )
    assert r5.status_code == 403
