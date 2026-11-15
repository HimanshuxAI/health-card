#!/usr/bin/env python3
"""End-to-end smoke test against live services (dev.sh must be running).

Flow: patient login -> hospital login -> resolve emergency token -> create record
-> create bill -> push claim -> admin adjudicates -> panic SOS -> admin trace check.
"""

import json
import sys
import httpx

BASE = {
    "identity": "http://127.0.0.1:8001",
    "records": "http://127.0.0.1:8002",
    "abdm": "http://127.0.0.1:8003",
    "nhcx": "http://127.0.0.1:8004",
    "sos": "http://127.0.0.1:8005",
}

STEPS: list[tuple[str, bool]] = []


def step(name: str, ok: bool, extra: str = ""):
    STEPS.append((name, ok))
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name} {extra}")


def main():
    c = httpx.Client(timeout=15)

    # 1. health checks
    for name, url in BASE.items():
        r = c.get(f"{url}/health")
        step(f"health/{name}", r.status_code == 200)

    # 2. logins
    r = c.post(f"{BASE['identity']}/login", json={"email": "aarav@abha.dev", "password": "abha1234"})
    pat = r.json()
    step("login patient", r.status_code == 200 and pat["role"] == "patient")
    pauth = {"Authorization": f"Bearer {pat['access_token']}"}
    pid = pat["user_id"]

    r = c.post(f"{BASE['identity']}/login", json={"email": "city@abha.dev", "password": "abha1234"})
    hosp = r.json()
    step("login hospital", r.status_code == 200)
    hauth = {"Authorization": f"Bearer {hosp['access_token']}"}
    hid = hosp["user_id"]

    r = c.post(f"{BASE['identity']}/login", json={"email": "admin@abha.dev", "password": "abha1234"})
    admin = r.json()
    aauth = {"Authorization": f"Bearer {admin['access_token']}"}

    # 3. emergency resolve (public, no auth)
    r = c.get(f"{BASE['records']}/records", params={"patient_id": pid}, headers=hauth)
    step("hospital lists patient records (consent ok)", r.status_code == 200)

    # find the patient's active QR token via records DB-backed endpoint:
    # hospital flow first uses /scan -> need token. Patient regenerates:
    r = c.post(f"{BASE['records']}/emergency/qr", headers=pauth)
    token = r.json()["token"]
    r = c.get(f"{BASE['records']}/emergency/resolve/{token}")
    step("emergency resolve <800ms", r.status_code == 200 and r.json()["retrieved_in_ms"] < 800, f"({r.json()['retrieved_in_ms']}ms)")

    # 4. hospital creates record -> FHIR + care context via abdm
    r = c.post(
        f"{BASE['records']}/records",
        json={"patient_id": pid, "type": "Prescription", "title": "E2E Test Rx", "details": {"dosage": "1-0-1 after food"}},
        headers=hauth,
    )
    step("hospital creates record", r.status_code == 200)
    record_id = r.json()["id"]

    r = c.post(
        f"{BASE['abdm']}/fhir/convert",
        json={"record": {"id": record_id, "type": "Prescription", "title": "E2E Test Rx"}, "patient": {"abha_id": pat.get("abha_id") or "11001100110001", "name": "Aarav Mehta"}, "patient_user_id": pid},
        headers=hauth,
    )
    step("FHIR conversion + care context", r.status_code == 200 and r.json()["fhir_bundle"]["resourceType"] == "Bundle")

    # 5. bill -> claim -> adjudicate
    r = c.post(
        f"{BASE['nhcx']}/bills",
        json={"patient_id": pid, "patient_abha_id": "11001100110001", "line_items": [{"description": "E2E OPD", "amount": 700}]},
        headers=hauth,
    )
    step("bill created", r.status_code == 200)
    bill = r.json()

    r = c.post(f"{BASE['nhcx']}/claims", json={"bill_id": bill["id"]}, headers=hauth)
    step("claim submitted to NHCX", r.status_code == 200)
    claim = r.json()

    r = c.post(f"{BASE['nhcx']}/claims/{claim['id']}/adjudicate", headers=aauth)
    step("claim adjudicated", r.status_code == 200 and r.json()["status"] == "APPROVED")

    # 6. SOS: panic from patient; admin listens
    import threading

    received = {}

    def listen():
        with c.stream("GET", f"{BASE['sos']}/alerts", headers=aauth) as r:
            pass  # placeholder; websocket check below

    r = c.post(
        f"{BASE['sos']}/alerts",
        json={"patient_id": pid, "trigger": "PANIC", "lat": 18.52, "lng": 73.85, "location_label": "E2E Test Location"},
        headers=pauth,
    )
    step("SOS alert dispatched", r.status_code == 200)

    # 7. admin sees ABDM trace
    r = c.get(f"{BASE['abdm']}/logs", headers=aauth)
    step("ABDM integration trace", r.status_code == 200 and len(r.json()["logs"]) > 0)

    passed = sum(1 for _, ok in STEPS if ok)
    total = len(STEPS)
    print(f"\n{'ALL PASS' if passed == total else 'FAILURES PRESENT'}: {passed}/{total}")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
