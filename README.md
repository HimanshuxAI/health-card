# ABHA Health Card — Next-Gen Hybrid Offline-Capable Health Management

**Ayushman Bharat Digital Mission (ABDM) + National Health Claims Exchange (NHCX)**
Group SY1512 — School of Computing, MIT-ADT University

A hybrid digital health card: an emergency trauma profile that a responder can read from a
QR code in under a second, a hospital workspace that turns visits into HL7 FHIR v4 records
and pushes itemized bills through a simulated NHCX gateway, and a live SOS pipeline that
hits hospital dashboards and emails emergency contacts in real time.

---

## Architecture

```
                    Next.js frontend  (patient / hospital / admin / public scanner)
                                    |
                            HTTPS  /api/*
                                    |
                         +----------v-----------+
                         |    API Gateway       |  NGINX: routing, rate limiting
                         +----------+-----------+
                                    |
     +---------------+--------------+---------------+----------------+
     |               |              |               |                |
+--------+   +---------------+ +-----------+ +--------------+ +--------------+
|Identity|   |Records &      | |ABDM +     | |NHCX Claims   | |SOS &         |
|& Auth  |   |Encryption     | |FHIR Engine| |Hub           | |Notification  |
+--------+   +---------------+ +-----------+ +--------------+ +--------------+
  auth.db      records.db       abdm.db      nhcx.db        sos.db
  users,       profiles,        care         bills,         alerts,
  consents     trauma profiles, contexts,     claims,        websocket
               records, QR      trace log    adjudication   broadcasts,
                                             state machine   SMTP email
```

Five FastAPI microservices, each owning its own SQLite database, behind an NGINX gateway.
ABDM and NHCX gateways are **simulated inside our own services** with real-shaped
endpoints — the demo runs fully offline and never depends on government sandbox uptime.

---

## Quick start

### Option A — everything with Docker (recommended for the demo)

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- API gateway: http://localhost (routes `/api/*`)
- Services: identity 8001 · records 8002 · abdm 8003 · nhcx 8004 · sos 8005

Seed data runs automatically on first boot.

### Option B — no Docker

```bash
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/seed.py     # creates and seeds the five databases
bash dev.sh                          # starts all five services on 8001-8005

cd frontend
npm install
npm run dev                          # http://localhost:3000
```

The Next dev server proxies `/api/*` to the services through `next.config.ts` rewrites.

### Tests

```bash
.venv/bin/python -m pytest services/*/tests -q     # 19 unit/integration tests
.venv/bin/python scripts/e2e.py                    # 16-step live smoke test (services must be running)
```

---

## Demo credentials

Password for every account: `abha1234`

| Role | Email | What it shows |
|---|---|---|
| Patient | `aarav@abha.dev` | Health card + QR, emergency profile editor, FHIR records, consents, claims |
| Hospital | `city@abha.dev` | Dashboard, patient scanner, record writer, billing, claims, live SOS feed |
| Admin | `admin@abha.dev` | System overview, ABDM integration trace, claim adjudication, SOS audit |

---

## Five-minute demo script

1. **Patient** — sign in as Aarav. Open *My Card*: the black health card shows ABHA ID,
   blood group `O+`, allergy badges, emergency contacts and a live QR code. Add a drug
   allergy in *Emergency Profile*; the trauma profile is re-sealed with AES-128-GCM.
2. **Hospital** — sign in as City Hospital. Open *Scan Patient*, paste the token from the
   QR (or open the QR link directly). The profile decrypts line by line with the server
   timing badge — typically under 5 ms.
3. **Records** — in *New Record*, write a prescription. It is stored as a FHIR
   `MedicationRequest` and linked as an ABDM care context; the FHIR bundle renders live.
4. **Billing** — create an itemized bill, then *Push to NHCX*. The claim moves
   `SUBMITTED → ADJUDICATED → APPROVED` with the insurer note and out-of-pocket estimate.
5. **SOS** — press *Panic* in the patient tab. The alert appears instantly in the hospital
   *SOS Feed* over WebSocket (with a beep), and an email goes to every registered contact.
6. **Admin** — show the ABDM integration trace (every simulated gateway call, latency and
   status), adjudicate a pending claim, and audit the SOS history.

---

## Module map (matches the project synopsis)

| Synopsis module | Implementation |
|---|---|
| Hardware & Encryption Module | `services/records/app/crypto.py` — AES-128-GCM + HMAC-SHA256, signed QR tokens (`services/records/app/routes_emergency.py`) |
| Mobile Client & Emergency SOS | `frontend/app/patient`, `frontend/app/hospital`, `frontend/app/scan` + `services/sos` (WebSocket broadcast, GPS tag, SMTP email) |
| ABDM & FHIR Interoperability Engine | `services/abdm/app/fhir_builder.py` (HL7 FHIR v4), sandbox simulator, integration trace log |
| NHCX Claims Synchronization Hub | `services/nhcx/app/state_machine.py` — bill → FHIR `Claim`, adjudication state machine, out-of-pocket estimation |
| Authentication | `services/identity` — bcrypt hashing, JWT with role claims, RBAC per service, ABHA eKYC simulation, consent artifacts |

---

## Security notes

- Passwords hashed with bcrypt; JWTs signed with a shared secret, 24 h expiry.
- Every service re-checks role claims independently of the gateway.
- Trauma profiles are AES-128-GCM encrypted at rest and HMAC-signed; tampering fails the
  integrity check before decryption is attempted.
- Consent artifacts gate hospital access to patient records; revoking is immediate.
- The public scanner resolves an HMAC-signed token only — no patient identity is exposed
  without the token.

---

## Configuration

Copy `.env.example` to `.env` and fill in SMTP credentials to enable real alert emails:

```
SMTP_HOST=smtp.gmail.com
SMTP_USER=you@gmail.com
SMTP_PASS=<gmail app password>
SOS_FROM_EMAIL=you@gmail.com
```

Without SMTP settings, alerts still fire over WebSocket and the email status shows
`SKIPPED` — the demo never breaks because of a mail outage.

---

## Repository layout

```
frontend/          Next.js 16 App Router frontend (Tailwind v4, editorial theme)
services/
  shared/          JWT helpers, password hashing, SQLAlchemy base
  identity/        auth, RBAC, eKYC, consents
  records/         profiles, AES-GCM trauma profiles, QR tokens, records
  abdm/            FHIR builders, sandbox simulator, integration trace
  nhcx/            bills, FHIR claims, adjudication state machine
  sos/             alerts, websocket broadcast, SMTP mailer
gateway/           NGINX configuration
scripts/           seed.py (orchestrator), e2e.py (live smoke test)
docs/              design spec and implementation plan
```
