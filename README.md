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

## Live demo

The project site, with the architecture diagram and the run instructions, is published at
https://himanshuxai.github.io/health-card/

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
3. In the hospital workspace, open **Scan Patient** and scan the card with the camera, or paste
   the token from the QR payload. The profile decrypts line by line, usually in under five
   milliseconds.
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
| Frontend build | Unit tests, route type generation, `tsc --noEmit`, production build |
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

### Deploying to a server, automatically

`.github/workflows/deploy.yml` deploys to any Docker host over SSH after the images for a commit
have been published. Every push to `main` is then deployed on its own, pinned to that commit.

One-time setup on the host, which needs Docker and Docker Compose:

```bash
sudo useradd -m -s /bin/bash deploy
echo "deploy ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/deploy
mkdir -p /srv/health-card/gateway
```

Then add the repository secrets: `DEPLOY_HOST`, `DEPLOY_SSH_KEY`, and the optional variables
`DEPLOY_USER`, `DEPLOY_PORT` and `DEPLOY_PATH`. The workflow copies the compose file and the
gateway configuration to the host, pulls the images for that commit and starts the stack.

If the secrets are not set the workflow reports that it has nothing to do and exits, so the
repository stays usable without a host.

### The whole stack in one container

Some hosts give a single service and a single volume rather than a compose file. For those,
`deploy/allinone/Dockerfile` packs the five services, the frontend and the gateway into one image,
with the SQLite files on one mounted volume.

It is published to GHCR as `ghcr.io/<owner>/health-card-allinone` on every push to `main`.

```bash
docker build -f deploy/allinone/Dockerfile -t health-card-allinone .
docker run -p 8080:80 -v health-card-data:/data health-card-allinone
```

Then open `http://localhost:8080`. The smoke test can be pointed at it, which also works against a
deployed instance:

```bash
E2E_BASE=http://localhost:8080 .venv/bin/python scripts/e2e.py
```

Supervisord runs the seed once at startup and then the five services, the frontend and nginx. The
seed is idempotent, so a restart re-uses the database on the volume instead of replacing it, and a
card that was already printed keeps working.

### Render: free, and no card

Render's Free instance is the easiest free host for this app, and the only one that asks for no
payment method. `render.yaml` in the repository root describes everything, so a deploy is:
**New → Blueprint → point at this repository**.

What the Free plan gives and costs, in full:

| | |
|---|---|
| Compute | 0.1 CPU, 512 MB RAM. The container measures 321 MB, so it fits. |
| Card | Not required |
| Persistent disk | **Not available on Free.** Disks are paid-only. |
| Idle | Spins down after 15 minutes without a request, wakes in about a minute |
| Hours | 750 instance hours a month; spun-down time does not count |

The URL stays valid while the service is asleep, so a scanned card still resolves — the first
request after a quiet spell just waits for the wake-up.

The filesystem is wiped whenever the service spins down, restarts, or redeploys, and the seed then
runs again. That is the reason the seeded demo card token is *derived* rather than random
(`services/records/records_app/demo.py`): the same card comes back every time, so a printed code
keeps working. Records, bills and claims created through the interface are not kept — this is a
demo host, not somewhere to store data. A token a patient issues with **Regenerate card** is still
random, and is lost when the service restarts.

### Northflank: a free host that keeps a volume

Northflank keeps a persistent volume on its free tier, but creating a service **requires a card on
file**, whatever the pricing page implies, so it is only worth using if you are willing to add one.
When you are, it is the better deployment: the volume means data survives, and it does not sleep.

Northflank's free Sandbox tier is the one free tier left that suits this app: two services, one
database, persistent volumes, and compute that does not sleep. Its docs say it is not meant for
production, so treat it as a demo host.

1. Create an account at `app.northflank.com`. The free Sandbox does not ask for a card.
2. Create a project, then a service, and choose **Deploy from an external registry** with the
   image `ghcr.io/<owner>/health-card-allinone:latest`.
3. Set the public port to `80`.
4. Add a volume mounted at `/data`, so the five SQLite files survive a restart.
5. Give it 1 vCPU and 1 GB. At Northflank's rates that is about $18 a month of usage, which the
   $20 monthly free allowance covers.

The service comes back with an HTTPS address on `code.run`. Set `E2E_BASE` to that address and run
the smoke test against the live deployment:

```bash
E2E_BASE=https://<name>.code.run .venv/bin/python scripts/e2e.py
```

A GHCR package is private by default, and Northflank cannot pull a private image without a
credential. Either make the `health-card-allinone` package public under the repository's package
settings, or add a registry credential in Northflank for `ghcr.io` using a GitHub token with
`read:packages`.

### A permanent public address, for free

The stack listens on port 80. Publishing that port on a stable address needs something in front
of it. There are three ways, in order of cost.

#### Tailscale Funnel — free, stable address

[Funnel][funnel] publishes a local port at `https://<machine>.<tailnet>.ts.net`. It is free on
Tailscale's Personal plan, the name does not change when the machine restarts, and with `--bg` it
resumes by itself after a reboot. It is the cheapest way to get a fixed address.

One-time setup, in the browser:

1. Install [Tailscale for macOS][tsmac]. Use the App Store build or the Standalone variant; the
   sandboxed variants can forward a port, which is all this needs.
2. Sign in. This creates a free Personal tailnet.
3. Publish the gateway:

```bash
bash scripts/funnel.sh
```

Tailscale shows a page to approve Funnel and enables MagicDNS and HTTPS certificates for the
tailnet as part of it. The script writes the address to
`~/.local/state/health-card/public-url.txt` and leaves a marker so the watchdog keeps Funnel
running rather than falling back to a quick tunnel. Check it any time with:

```bash
tailscale funnel status
```

A Funnel address survives a reboot, so a QR code on a printed card keeps pointing at the running
scanner.

#### Cloudflare named tunnel — needs a domain

A named tunnel also keeps its address, but it can only use a hostname on a domain you own and have
added to Cloudflare. There is no way to get a stable name on `trycloudflare.com`.

```bash
cloudflared tunnel login
cloudflared tunnel create abha
cloudflared tunnel route dns abha health.example.com
```

`scripts/tunnel.sh` uses that tunnel when `~/.cloudflared/config.yml` exists.

#### Cloudflare quick tunnel — no account, changing address

With nothing else configured, `scripts/tunnel.sh` opens a quick tunnel. It needs no account, but
Cloudflare hands out a random address that changes on every restart, so it is only suitable for a
temporary look.

[funnel]: https://tailscale.com/kb/1223/funnel
[tsmac]: https://tailscale.com/download/mac

### Keeping a deployment up on a Mac

`scripts/install-mac-service.sh` installs two launchd agents:

| Agent | What it does |
|---|---|
| `com.abha.healthcard.keepalive` | Checks every service of the stack and starts the ones that stopped, keeps the public address running — Tailscale Funnel when it is configured, a quick tunnel otherwise — and writes that address to `~/.local/state/health-card/public-url.txt` |
| `com.abha.healthcard.caffeinate` | Stops the Mac from sleeping while it serves the app |

```bash
bash scripts/install-mac-service.sh
launchctl list | grep com.abha.healthcard
```

The agents start at login. macOS does not let a launchd job read anything inside `~/Documents`,
so the installer copies the files the watchdog needs into `~/.local/share/health-card`.

The watchdog looks at every service, not only at the gateway. The gateway can keep answering
while the service behind it is gone, so a check that only looks at the gateway misses a stack
that is half up.

### Project site

A short description of the system, with the architecture diagram and the run instructions, is
published to GitHub Pages: <https://himanshuxai.github.io/health-card/>

The workflow is `.github/workflows/pages.yml` and it publishes the `site/` directory.

---

## Tests

```bash
.venv/bin/python -m pytest                        # 22 unit and integration tests
.venv/bin/python scripts/e2e.py                   # 18-step live smoke test, services must be running
cd frontend && npm test                           # 17 frontend tests (vitest)
cd frontend && npx next typegen && npx tsc --noEmit
```

The smoke test covers the whole path: login for all three roles, a consent-gated record read,
an emergency card read that leaves the token in place and its resolve, record creation, FHIR
conversion, bill creation, claim submission, adjudication, an SOS alert and the ABDM trace.

The frontend tests cover the QR path: the token helpers, the camera component, and a check that
the code printed on the card keeps its four-module quiet zone and decodes back to the scan
address with a standard decoder. One test also covers a browser that has stopped handing out
animation frames, which used to stall the camera scan.

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

- Camera scanning runs in the browser with `getUserMedia` and `jsQR`. Browsers only hand over a
  camera on a secure origin, so it works over HTTPS and on `localhost` and not over plain HTTP
  on a LAN address. The token can always be pasted instead.
- The QR code on the card points at the address the card is shown on. A card printed from a
  `localhost` session opens the scanner on that machine only.
- Emergency contacts are notified by email. There is no SMS gateway.
- ABDM and NHCX are simulated in-process. No government sandbox is called.
- Each service owns one SQLite file. There are no cross-service transactions and no shared event
  bus beyond the WebSocket broadcast.
- The frontend is a single Next.js application, not a mobile build.
- A hosted deployment needs a machine that stays on. The repository ships the images, the compose
  file and a GitHub Actions workflow that deploys over SSH, but it cannot host the stack itself:
  GitHub Pages serves static files only, and an Actions runner is temporary.

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
