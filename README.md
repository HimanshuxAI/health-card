# ABHA Health Card

Group SY1512, School of Computing, MIT-ADT University.

An emergency health card that a responder can read from a QR code, a hospital workspace that
turns visits into HL7 FHIR v4 records and itemised bills, and a panic button that reaches
hospital dashboards and the patient's emergency contacts.

The system is built against two Indian health interoperability standards:

- **ABDM** (Ayushman Bharat Digital Mission) for identity, consent artifacts, care contexts and
  FHIR v4 resources.
- **NHCX** (National Health Claims Exchange) for bill submission and claim adjudication.

Both gateways are simulated inside this repository. The endpoints follow the real shapes, but no
government sandbox is called, so the project runs with no external dependency.

---

## Contents

- [Architecture](#architecture)
- [Run it](#run-it)
- [Demo accounts](#demo-accounts)
- [Walkthrough](#walkthrough)
- [Deployment](#deployment)
- [Tests](#tests)
- [Module map](#module-map)
- [Security](#security)
- [Configuration](#configuration)
- [What this build does not do](#what-this-build-does-not-do)
- [Repository layout](#repository-layout)

---

## Architecture

```
                    Next.js frontend  (patient / hospital / admin / public scanner)
                                    |
                            HTTP /api/*
                                    |
                         +----------v-----------+
                         |    API Gateway       |  NGINX: routing, rate limiting, ws upgrade
                         +----------+-----------+
                                    |
     +---------------+--------------+---------------+----------------+
     |               |              |               |                |
+--------+   +---------------+ +-----------+ +--------------+ +--------------+
|Identity|   |Records &      | |ABDM +     | |NHCX Claims   | |SOS &         |
|& Auth  |   |Encryption     | |FHIR Engine| |Hub           | |Notification  |
+--------+   +---------------+ +-----------+ +--------------+ +--------------+
  identity.db    records.db       abdm.db      nhcx.db        sos.db
  users,         profiles,        care         bills,         alerts,
  consents       trauma profiles, contexts,     claims,        websocket
                 records, QR      trace log    adjudication   broadcasts,
                                             state machine   SMTP email
```

Five FastAPI services, each with its own SQLite database, behind one NGINX gateway. The services
talk to each other over HTTP only: the records service asks the identity service to verify a
consent artifact, the claims service asks the ABDM service to build a FHIR claim.

| Concern | Where it lives |
|---|---|
| Identity, roles, consent artifacts | `services/identity` |
| Records, AES-GCM sealed trauma profiles, signed QR tokens | `services/records` |
| FHIR v4 builders, ABDM sandbox, integration trace | `services/abdm` |
| Bills, FHIR claims, adjudication state machine | `services/nhcx` |
| SOS alerts, WebSocket broadcast, SMTP delivery | `services/sos` |

---

## Run it

### With Docker

```bash
docker compose up --build
```

- Gateway and frontend: <http://localhost>
- Frontend directly: <http://localhost:3000>
- Services: identity 8001, records 8002, abdm 8003, nhcx 8004, sos 8005

Seed data is created on first boot: 9 accounts, 6 emergency profiles, 10 records, 5 bills, claims in
three different states and 3 historical alerts.

To reset the demo data:

```bash
docker compose stop identity records abdm nhcx sos
docker compose run --rm --no-deps seed python scripts/seed.py --reset
docker compose up -d
```

### Without Docker

Python 3.13 and Node 22 are required.

```bash
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/seed.py     # creates and seeds the five databases
bash dev.sh                          # starts the services on ports 8001 to 8005

cd frontend
npm install
npm run dev                          # http://localhost:3000
```

---

## Demo accounts

Password for every account: `abha1234`

| Role | Email | What it shows |
|---|---|---|
| Patient | `aarav@abha.dev` | Health card and QR, emergency profile editor, FHIR records, consents, claims |
| Hospital | `city@abha.dev` | Dashboard, patient scanner, record writer, billing, claims, live SOS feed |
| Administrator | `admin@abha.dev` | Service health, ABDM trace, claim adjudication, SOS audit |

---

## Walkthrough

1. Sign in as the patient and open **My Card**. The card shows the ABHA id, blood group, allergy
   badges, emergency contacts and a QR code.
2. Edit the emergency profile. It is re-sealed with AES-128-GCM and the change is visible on the
   next scan.
3. In the hospital workspace, open **Scan Patient** and paste the token from the QR payload. The
   profile decrypts line by line, usually in under five milliseconds.
4. In **New Record**, write a prescription. It is stored as a FHIR `MedicationRequest` and linked
   as an ABDM care context. The bundle renders on the page.
5. In **Billing**, create an itemised bill and push it to NHCX. The claim moves from `SUBMITTED` to
   `ADJUDICATED` to `APPROVED`, with the insurer note and the out-of-pocket amount.
6. Press **Panic** in the patient area. The alert appears in the hospital **SOS Feed** over a
   WebSocket, with a sound, and an email goes to every registered contact.
7. In the administrator area, inspect the ABDM integration trace, adjudicate a pending claim and
   audit the SOS history.

---

## Deployment

### Continuous integration

Every push to `main` runs four jobs on GitHub Actions:

| Job | What it checks |
|---|---|
| Backend tests | `pytest` against an isolated database per service |
| End-to-end smoke test | Starts the five services, seeds them, runs `scripts/e2e.py` |
| Frontend build | Route type generation, `tsc --noEmit`, production build |
| Build images | Builds both container images without pushing |

### Published images

The publish workflow pushes both images to GitHub Container Registry on every push to `main` and
on `v*` tags, for `linux/amd64` and `linux/arm64`.

```bash
docker pull ghcr.io/himanshuxai/health-card-frontend:latest
docker pull ghcr.io/himanshuxai/health-card-services:latest
```

`docker-compose.ghcr.yml` runs the published images. It needs no source tree and keeps the
databases in a named volume, so data survives a container replacement.

```bash
docker compose -f docker-compose.ghcr.yml up -d
```

Pin a build by commit:

```bash
ABHA_TAG=<git-sha> docker compose -f docker-compose.ghcr.yml up -d
```

The seed service runs once on first start. To rebuild the demo data later:

```bash
docker compose -f docker-compose.ghcr.yml stop identity records abdm nhcx sos
docker compose -f docker-compose.ghcr.yml run --rm --no-deps seed python scripts/seed.py --reset
docker compose -f docker-compose.ghcr.yml up -d
```

### Project site

A short description of the system, with the architecture diagram and the run instructions, is
published to GitHub Pages: <https://himanshuxai.github.io/health-card/>

The workflow is `.github/workflows/pages.yml` and it publishes the `site/` directory.

---

## Tests

```bash
.venv/bin/python -m pytest                        # 20 unit and integration tests
.venv/bin/python scripts/e2e.py                   # 16-step live smoke test, services must be running
cd frontend && npx next typegen && npx tsc --noEmit
```

The smoke test covers the whole path: login for all three roles, a consent-gated record read,
emergency token issue and resolve, record creation, FHIR conversion, bill creation, claim
submission, adjudication, an SOS alert and the ABDM trace.

---

## Module map

| Synopsis module | Implementation |
|---|---|
| Hardware and encryption | `services/records/records_app/crypto.py`, AES-128-GCM and HMAC-SHA256, signed QR tokens in `routes_emergency.py` |
| Mobile client and emergency SOS | `frontend/app/patient`, `frontend/app/hospital`, `frontend/app/scan`, `services/sos/sos_app` |
| ABDM and FHIR interoperability | `services/abdm/abdm_app/fhir_builder.py`, sandbox simulator, integration trace log |
| NHCX claims synchronisation | `services/nhcx/nhcx_app/state_machine.py`, bill to FHIR claim, adjudication, out-of-pocket estimate |
| Authentication | `services/identity/identity_app`, bcrypt hashing, JWT with role claims, RBAC per service, ABHA eKYC simulation, consent artifacts |

---

## Security

- Passwords are hashed with bcrypt. JWTs are signed with a shared secret and expire after 24 hours.
- Every service checks the role claims itself. The gateway routes, it does not authorise.
- Trauma profiles are sealed with AES-128-GCM and signed with HMAC-SHA256. A tampered profile
  fails the integrity check before decryption is attempted.
- Consent artifacts gate hospital access to patient records. Revoking one takes effect on the
  next request, and the hospital loses the patient from its list.
- The public scanner resolves a signed token only. It returns no patient identity without one.
- Set `JWT_SECRET` and `SHARED_TOKEN` to real values before any deployment that is reachable by
  other people. The defaults in `docker-compose.yml` are for local use.

---

## Configuration

Copy `.env.example` to `.env` and fill in SMTP credentials to send real alert emails:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASS=<app password>
SOS_FROM_EMAIL=you@gmail.com
```

Without SMTP settings the alert still fires over the WebSocket and the email status reads
`SKIPPED`. The demo does not depend on a mail server.

---

## What this build does not do

- The scanner reads a pasted token. There is no camera decode in the web build.
- Emergency contacts are notified by email. There is no SMS gateway.
- ABDM and NHCX are simulated in-process. No government sandbox is called.
- Each service owns one SQLite file. There are no cross-service transactions and no shared event
  bus beyond the WebSocket broadcast.
- The frontend is a single Next.js application, not a mobile build.

---

## Repository layout

```
frontend/          Next.js 16 App Router frontend, Tailwind v4, editorial theme
site/              Static project site published by GitHub Pages
services/
  shared/          JWT helpers, password hashing, SQLAlchemy base
  identity/        auth, RBAC, eKYC, consents
  records/         profiles, AES-GCM trauma profiles, QR tokens, records
  abdm/            FHIR builders, sandbox simulator, integration trace
  nhcx/            bills, FHIR claims, adjudication state machine
  sos/             alerts, WebSocket broadcast, SMTP mailer
gateway/           NGINX configuration
scripts/           seed.py orchestrator, e2e.py live smoke test
docs/              design specification and implementation plan
```

## Licence

MIT. See [LICENSE](LICENSE).
