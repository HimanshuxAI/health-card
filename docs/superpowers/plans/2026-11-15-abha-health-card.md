# Next-Gen ABHA Health Card — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the full demo-grade system from the approved spec: 5 FastAPI microservices + NGINX gateway + Next.js frontend (Editorial/Medical-Journal theme), JWT auth for 3 roles, simulated ABDM/NHCX gateways, encrypted trauma profiles with QR scan flow, live WebSocket SOS + email.

**Architecture:** Five FastAPI services (identity, records, abdm, nhcx, sos), each with its own SQLite database via SQLAlchemy, behind an NGINX gateway that verifies JWTs. Single Next.js App Router frontend. docker-compose orchestrates all 6 containers; `dev.sh` runs everything without Docker.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, PyCryptodome, PyJWT, pytest, NGINX, Next.js 14+, Tailwind, Lucide icons, uvicorn/websockets.

**Spec:** `docs/superpowers/specs/2026-11-15-abha-health-card-design.md`

**Execution mode (decided):** Inline execution, minimal checkpoints, commit after every task. Never ask the user questions during execution; make reasonable choices consistent with the spec.

---

## Phase 0 — Scaffolding

### Task 0.1: Repo skeleton + shared library

**Files:**
- Create: `services/shared/__init__.py`, `services/shared/config.py`, `services/shared/security.py`, `services/shared/db.py`
- Create: `requirements.txt`, `dev.sh`, `docker-compose.yml` (placeholder for now), `gateway/nginx.conf`

- [x] **Step 1: Create directory structure**

```bash
mkdir -p services/shared services/identity/app services/records/app \
  services/abdm/app services/nhcx/app services/sos/app \
  gateway frontend docs/superpowers/plans scripts
```

- [x] **Step 2: Write `services/shared/config.py`**

```python
import os

JWT_SECRET = os.getenv("JWT_SECRET", "demo-secret-change-me")
JWT_ALG = "HS256"
JWT_EXP_HOURS = 24

SHARED_TOKEN = os.getenv("SHARED_TOKEN", "internal-demo-token")
```

- [x] **Step 3: Write `services/shared/security.py`** — JWT create/verify + bcrypt password helpers.

```python
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt

from services.shared.config import JWT_SECRET, JWT_ALG, JWT_EXP_HOURS


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(sub: str, role: str, abha_id: str | None = None) -> str:
    payload = {
        "sub": sub,
        "role": role,
        "abha_id": abha_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXP_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.PyJWTError:
        return None
```

- [x] **Step 4: Write `services/shared/db.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    pass


def make_db(db_path: str):
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine, autoflush=False)
    return engine, Session
```

- [x] **Step 5: Write `requirements.txt`**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
pyjwt==2.10.1
bcrypt==4.2.1
pycryptodome==3.21.0
httpx==0.28.1
pytest==8.3.4
python-multipart==0.0.20
```

- [x] **Step 6: Install deps**

Run: `pip install -r requirements.txt`
Expected: success (may already be installed).

- [x] **Step 7: Commit**

```bash
git add -A && git commit -m "chore: repo skeleton and shared library"
```

---

### Task 0.2: Bootstrap files (dev.sh, compose, nginx, .env.example)

- [x] **Step 1: Write `docker-compose.yml`** — services `gateway`(nginx:alpine, ports 80->80), `identity`,`records`,`abdm`,`nhcx`,`sos` (each `uvicorn app.main:app --host 0.0.0.0 --port 8000` mapped to internal ports 8001-8005, `restart: unless-stopped`, healthcheck curl `/health`), volumes mounting service dirs, env `JWT_SECRET` shared, named volumes for sqlite files NOT used (bind-mount service dirs so DBs persist in repo working tree).

- [x] **Step 2: Write `gateway/nginx.conf`** — server on 80; locations `/api/identity/` -> `http://identity:8000/`, same pattern for records/abdm/nhcx/sos (rewrite strip prefix); `proxy_set_header` standard; simple rate limit zone `limit_req_zone $binary_remote_addr zone=api:10m rate=50r/s;` applied to /api/. JWT verification is done inside each service (keep nginx config simple to avoid auth_request complexity); the gateway adds `X-Request-Start` header used for latency.

- [x] **Step 3: Write `dev.sh`** — starts all 5 uvicorn processes on ports 8001-8005 with trap cleanup, logs to `/tmp/abha-services/`, runs `scripts/seed.py` if first run.

- [x] **Step 4: Write `.env.example`** — `JWT_SECRET`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SOS_FROM_EMAIL`.

- [x] **Step 5: Commit**

```bash
git add -A && git commit -m "chore: compose, nginx gateway, dev script, env example"
```

---

## Phase 1 — Identity Service

### Task 1.1: Models + app scaffold

**Files:** `services/identity/app/__init__.py`, `models.py`, `main.py`, `schemas.py`, `routes/` (auth.py, users.py, ekyc.py), `tests/test_identity.py`

- [x] **Step 1: Models** — `User` (id, name, email unique, password_hash, role, abha_id nullable 14-digit string, phone, hospital_name nullable), `ConsentArtifact` (id, patient_id FK users.id, hospital_id FK users.id, scope str, granted_at, expires_at, status ACTIVE|REVOKED).

- [x] **Step 2: Schemas** — `RegisterIn(name,email,password,role,abha_id=None,phone=None,hospital_name=None)`, `LoginIn(email,password)`, `TokenOut(access_token,token_type,role,abha_id)`, `EkycIn(abha_id)`, `EkycOut(verified,abha_id,txn_id,name_masked,ts)`.

- [x] **Step 3: main.py** — FastAPI app, `Base.metadata.create_all` on startup with `identity.db`, CORS allow all for demo, prefix `/api/identity`. Include router `health.py` returning `{"status":"ok"}` at `/health`.

- [x] **Step 4: Routes auth.py** — POST `/register` (reject duplicate email -> 409 `{detail:"Email already registered"}`), POST `/login` (401 on bad creds), dependency `get_current_user` reading `Authorization: Bearer` header, decode via shared security lib, 401 if invalid; `require_role(*roles)` factory dependency.

- [x] **Step 5: Routes ekyc.py** — POST `/ekyc/verify` requires JWT; validates abha_id is 14 digits (regex `^\d{14}$`, 422 otherwise); simulated registry: name derived from user's own record, txn_id = uuid4 hex, latency ~ random 80-200ms via no-op; returns EkycOut. Log nothing here (ABDM service owns trace logging).

- [x] **Step 6: Tests (`tests/test_identity.py`)** — use `TestClient`: register -> 200 + token; duplicate register -> 409; login good -> 200 token with role claim; login bad -> 401; protected endpoint without token -> 401; ekyc good 14-digit -> verified true; ekyc bad format -> 422.

- [x] **Step 7: Run tests, then commit**

```bash
cd services/identity && python -m pytest tests/ -q
git add -A && git commit -m "feat(identity): auth, RBAC, eKYC simulation with tests"
```

---

## Phase 2 — Records Service

### Task 2.1: Models + encryption core

**Files:** `services/records/app/models.py`, `crypto.py`, `main.py`, `routes/{records,emergency}.py`, `tests/test_crypto.py`, `tests/test_records.py`

- [x] **Step 1: Models** — PatientProfile(id, user_id unique, blood_group, allergies JSON, chronic_conditions JSON, medications JSON, emergency_contacts JSON), HealthRecord(id, patient_id, type, title, fhir_json TEXT, created_by, created_at), TraumaProfile(id, patient_id, encrypted_blob BLOB(hex str), nonce str, hmac_sha256 str, updated_at), QrToken(id, patient_id, token unique, created_at, active bool).

- [x] **Step 2: `crypto.py`** — AES-128-GCM wrapper:

```python
import hmac, hashlib, json, os
from Crypto.Cipher import AES

KEY = os.getenv("TRAMA_KEY", "abha-demo-key-16b")[:16].encode()  # 16 bytes

def seal(payload: dict) -> tuple[str, str, str]:
    nonce = os.urandom(12)
    cipher = AES.new(KEY, AES.MODE_GCM, nonce=nonce)
    ct, tag = cipher.encrypt_and_digest(json.dumps(payload).encode())
    blob = (cipher.nonce if False else b"") + ct  # ct only; nonce stored separately
    data = blob + tag
    sig = hmac.new(KEY, data, hashlib.sha256).hexdigest()
    return data.hex(), nonce.hex(), sig

def unseal(data_hex: str, nonce_hex: str, sig: str) -> dict | None:
    data = bytes.fromhex(data_hex)
    expected = hmac.new(KEY, data, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None
    ct, tag = data[:-16], data[-16:]
    cipher = AES.new(KEY, AES.MODE_GCM, nonce=bytes.fromhex(nonce_hex))
    try:
        pt = cipher.decrypt_and_verify(ct, tag)
    except ValueError:
        return None
    return json.loads(pt)
```

- [x] **Step 3: Tests for crypto** — round-trip returns original dict; tampered sig -> None; tampered ciphertext -> None. Run, expect pass.

- [x] **Step 4: Routes emergency.py** — POST `/emergency/profile` (patient role) saves/updates sealed trauma profile from profile fields; POST `/emergency/qr` (patient) creates QrToken, returns `token` + `scan_url` = `{BASE_URL}/scan?t={token}`; GET `/emergency/resolve/{token}` (PUBLIC) -> validates token active, loads sealed profile, decrypts server-side, measures elapsed ms internally, returns `{profile, retrieved_in_ms}` or 404/410 (inactive); POST `/sos/dispatch` handled by sos-service (records-service only exposes profile fetch for it internally: GET `/internal/profile/{patient_id}` guarded by X-Internal-Token header == SHARED_TOKEN).

- [x] **Step 5: Routes records.py** — CRUD health records (hospital role creates for consented patients — check consent via identity DB read is NOT direct; records-service queries identity-service via httpx `/api/identity/consents/check?patient_id=&hospital_id=`; for demo resilience, if identity unreachable, allow with warning flag). GET list for patient (own) with `?fhir=true` returning raw FHIR JSON view.

- [x] **Step 6: Tests** — patient flow: update profile, create QR, resolve token returns profile with retrieved_in_ms < 800 typically; inactive token -> 410; tamper test not possible via API (server-side only). Records: hospital cannot read patient without consent -> 403; with consent -> 200.

- [x] **Step 7: Run tests + commit**

```bash
cd services/records && python -m pytest tests/ -q
git add -A && git commit -m "feat(records): AES-GCM trauma profiles, QR tokens, records CRUD"
```

---

## Phase 3 — ABDM + FHIR Service

### Task 3.1: FHIR builder + sandbox simulator + trace log

**Files:** `services/abdm/app/{models.py,fhir_builder.py,sandbox.py,main.py,routes/{care_contexts,consent,fhir}.py}`, `tests/test_fhir.py`, `tests/test_abdm.py`

- [x] **Step 1: Models** — CareContext(id, patient_id, record_ref, status LINKED|CONSENT_PENDING|ACTIVE), AbdmLog(id, ts, direction, endpoint, payload_snippet, status_code, latency_ms).

- [x] **Step 2: `fhir_builder.py`** — functions `build_diagnostic_report(record_row, patient_row)`, `build_prescription(...)` returning valid-ish FHIR v4 JSON (resourceType DiagnosticReport / MedicationRequest, subject reference `Patient/{abha_id}`, effectiveDateTime ISO). Pure functions, fully tested.

- [x] **Step 3: `sandbox.py`** — simulated ABDM gateway: `/api/abdm/sandbox/abha/search` (POST, returns mock 14-digit ID), `/api/abdm/sandbox/consent/initiate` -> consent artifact id, `/api/abdm/sandbox/care-context/link` -> links context; every call writes an AbdmLog row with direction IN, endpoint, payload snippet (first 120 chars), status 200, latency measured.

- [x] **Step 4: Routes** — GET `/api/abdm/logs` (admin only) with pagination; POST `/api/abdm/fhir/convert` (hospital) record_id -> FHIR JSON + auto care context LINKED.

- [x] **Step 5: Tests** — fhir_builder produces resourceType + subject; sandbox consent initiate creates log row; convert endpoint returns FHIR and creates care context.

- [x] **Step 6: Commit**

```bash
cd services/abdm && python -m pytest tests/ -q
git add -A && git commit -m "feat(abdm): FHIR builder, sandbox simulator, integration trace"
```

---

## Phase 4 — NHCX Claims Service

### Task 4.1: Bills + claims state machine

**Files:** `services/nhcx/app/{models.py,state_machine.py,main.py,routes/{bills,claims}.py}`, `tests/test_nhcx.py`

- [x] **Step 1: Models** — Bill(id, hospital_id, patient_id, line_items JSON, total float, created_at), Claim(id, bill_id, fhir_claim_json TEXT, status SUBMITTED|ADJUDICATED|APPROVED|REJECTED, insurer_note, out_of_pocket float, adjudicated_at).

- [x] **Step 2: `state_machine.py`** — transitions dict: SUBMITTED->ADJUDICATED->APPROVED|REJECTED; `can_transition(cur, nxt)` returns bool; invalid -> raises ValueError. Claim→FHIR Claim JSON builder (resourceType Claim, item[] from bill line items, total).

- [x] **Step 3: Routes** — POST `/api/nhcx/bills` (hospital), POST `/api/nhcx/claims` (hospital; builds FHIR claim from bill, status SUBMITTED; internally calls abdm-service `/api/abdm/sandbox/nhcx-forward` to write a trace log), POST `/api/nhcx/claims/{id}/adjudicate` (admin) -> after 2-4s simulated processing (asyncio.sleep, configurable `NHCX_DELAY=3`) sets ADJUCATED then APPROVED (insurer_note: approved amount, out_of_pocket computed as total - approved unless rejected) — approved when total < 50000 else REJECTED with note "insufficient coverage for itemized claim". GET lists for patient/hospital/admin.

- [x] **Step 4: Tests** — create bill -> create claim (status SUBMITTED, has fhir_claim_json with resourceType Claim); adjudicate cheap -> APPROVED with out_of_pocket; expensive (>50000) -> REJECTED; invalid transition rejected.

- [x] **Step 5: Commit**

```bash
cd services/nhcx && python -m pytest tests/ -q
git add -A && git commit -m "feat(nhcx): bills, FHIR claims, adjudication state machine"
```

---

## Phase 5 — SOS Service

### Task 5.1: Alerts + WebSocket + email

**Files:** `services/sos/app/{models.py,mailer.py,ws.py,main.py,routes/alerts.py}`, `tests/test_sos.py`

- [x] **Step 1: Models** — Alert(id, patient_id, trigger, lat, lng, notified_contacts JSON, email_status, created_at).

- [x] **Step 2: `ws.py`** — `ConnectionManager` with `connect(websocket)`, `disconnect`, `broadcast(json)`; endpoint `/api/sos/ws` (token query param validated, hospital|admin roles).

- [x] **Step 3: `mailer.py`** — smtplib SMTP if `SMTP_USER`/`SMTP_PASS` set; else return "EMAIL_SKIPPED". Compose plain-text alert email (patient name, location coords, trigger, timestamp). Failures -> "EMAIL_FAILED" logged, never raise.

- [x] **Step 4: Routes alerts.py** — POST `/api/sos/alerts` (any authenticated user; body: patient_id, trigger, lat, lng) -> fetch emergency contacts from records-service internal endpoint (X-Internal-Token) -> create alert, broadcast to WS clients, send emails -> return alert JSON. GET `/api/sos/alerts` (admin: all; hospital: all; patient: own).

- [x] **Step 5: Tests** — create alert (SMTP unset -> EMAIL_SKIPPED), GET list auth; WS broadcast test via TestClient websocket_connect.

- [x] **Step 6: Commit**

```bash
cd services/sos && python -m pytest tests/ -q
git add -A && git commit -m "feat(sos): alerts, websocket broadcast, SMTP email"
```

---

## Phase 6 — Seed Data

**Files:** `scripts/seed.py`, `scripts/e2e.py`

- [x] **Step 1: seed.py** — against each service DB directly (imports models): admin@abha.dev / city@abha.dev / aarav@abha.dev / diya@abha.dev (password abha1234), 2 hospitals, 6 patients with varied blood groups/conditions, ~20 records, 8 bills, 5 claims across statuses, 3 SOS alerts, ABDM trace rows. Idempotent: skip if admin exists.

- [x] **Step 2: e2e.py** — httpx script: login patient -> hospital scans QR -> hospital creates record -> bill -> claim -> admin adjudicates -> patient panic SOS -> assert all statuses. Print PASS summary.

- [x] **Step 3: Run e2e with dev.sh up; fix any wiring issues**

- [x] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: seed data and end-to-end smoke script"
```

---

## Phase 7 — Frontend

### Task 7.1: Next.js scaffold + design system

**Files:** `frontend/` (create-next-app), `tailwind.config.ts`, `app/globals.css`, `components/ui/*`

- [x] **Step 1:** `npx create-next-app@latest frontend --ts --tailwind --app --no-src-dir --import-alias "@/*" --eslint` inside repo root.

- [x] **Step 2: globals.css** — CSS vars: `--paper:#F5F2EA; --ink:#1C1917; --stone:#78716C; --green:#166534; --red:#B91C1C; --line:#1C1917`. Fonts via next/font: `Source_Serif_4` (display), `Inter` (body), `JetBrains_Mono` (mono). Utility classes: `.rule` (1px ink border), `.stat-display` (serif, large, tight), `.label-caps` (uppercase, tracking, stone), `.badge` (1px ink border, mono 10px). NO gradients/glassmorphism anywhere.

- [x] **Step 3: `lib/api.ts`** — `API_BASE` (env NEXT_PUBLIC_API_BASE default http://localhost:80/api), `apiFetch(path, opts)` attaches Bearer token from localStorage, JSON handling, throws `{detail}`.

- [x] **Step 4: `lib/auth.tsx`** — AuthProvider context: token, user, role, login(), logout(), guard components.

- [x] **Step 5: Components** — `TopNav` (editorial rule-based nav, no emoji), `Stat` (big serif number + caps label), `Panel` (bordered section w/ caps title), `Badge`, `Button` (ink solid / outline), `EmptyState`.

- [x] **Step 6: Commit**

```bash
git add -A && git commit -m "feat(frontend): scaffold, editorial design system, auth lib"
```

### Task 7.2: Landing, auth pages

- [x] **Step 1: `/` landing** — editorial hero (serif headline "Your health record, readable in an emergency", stat strip, hairline rules, links to /login and /scan; copy references ABDM/NHCX without emoji).
- [x] **Step 2: `/login`** — email+password, demo credentials table shown; redirect by role.
- [x] **Step 3: `/register`** — role select (patient/hospital), fields per role; hospital requires hospital_name.
- [x] **Step 4: Commit** `feat(frontend): landing and auth pages`

### Task 7.3: Patient area

- [x] **Step 1: `/patient` layout + My Card** — black hero card (name, ABHA mono, QR image from backend scan_url rendered client-side via QR lib `qrcode.react`), blood group + allergy pills, SOS PANIC button (confirm -> POST /api/sos/alerts trigger PANIC, geolocation via browser API).
- [x] **Step 2: Emergency Profile editor** — blood group select, dynamic lists (allergies/conditions/meds/contacts), save -> POST /api/records/emergency/profile; then regenerate QR token.
- [x] **Step 3: Records timeline** — list w/ type badges, "View FHIR" toggle showing raw JSON in `<pre>` mono block.
- [x] **Step 4: Consent manager** — active consent cards, revoke button.
- [x] **Step 5: Billing & Claims** — bills list, claim status timeline pills (SUBMITTED->ADJUDICATED->APPROVED/REJECTED) with out-of-pocket.
- [x] **Step 6: Commit** `feat(frontend): patient area`

### Task 7.4: Hospital area

- [x] **Step 1: Dashboard** — stat row (patients today, claims pending, SOS active, mean retrieval ms), blood index panel, recent activity rules list.
- [x] **Step 2: Scan Patient** — input for scan token/ABHA (paste path primary; note about camera), on resolve -> typed decrypt animation showing profile lines + server-timed `retrieved_in_ms` badge; "Dispatch SOS" button.
- [x] **Step 3: New Record** — form (patient select via consented list, type, title, fields), submit -> POST convert -> success shows FHIR JSON snippet.
- [x] **Step 4: Billing** — create itemized bill (dynamic line items), "Push to NHCX" -> creates claim, shows status.
- [x] **Step 5: Claims workspace** — table w/ status pills.
- [x] **Step 6: Live SOS feed** — WebSocket client (ws://localhost:80/api/sos/ws) with reconnect; incoming alert -> red pulse panel + Web Audio beep; list of today's alerts.
- [x] **Step 7: Commit** `feat(frontend): hospital area`

### Task 7.5: Admin area

- [x] **Step 1: Overview** — users table, counts, health of 5 services (poll /health).
- [x] **Step 2: ABDM trace** — log table (ts, direction, endpoint, latency_ms, status), filterable.
- [x] **Step 3: Claims oversight** — pending claims with Adjudicate button (shows 2-4s processing state), approve/reject result.
- [x] **Step 4: SOS audit** — all alerts with email status.
- [x] **Step 5: Commit** `feat(frontend): admin area`

### Task 7.6: Public /scan page

- [x] **Step 1: /scan** — no auth; token input (prefilled from `?t=` query), Resolve -> typed decrypt animation + `retrieved_in_ms` badge, profile display, Dispatch SOS button (contact list shown, lat/lng from browser).
- [x] **Step 2: Commit** `feat(frontend): public emergency scanner`

---

## Phase 8 — Final wiring + docs

- [x] **Step 1: docker-compose up full-stack verification** — gateway routes work, seed runs, frontend talks through gateway.
- [x] **Step 2: README.md** — architecture diagram (ASCII), quickstart (docker-compose up OR dev.sh), demo credentials, demo script (5 steps from spec), tech stack, module map matching synopsis.
- [x] **Step 3: Final e2e run + full pytest across services.**
- [x] **Step 4: Commit + push.**

```bash
git add -A && git commit -m "docs: readme, final wiring" && git push
```
