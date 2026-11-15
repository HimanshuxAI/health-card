# Design Doc — Next-Gen ABHA Health Card

Date: 2026-11-15
Project: SY1512 — MIT-ADT University, School of Computing
Goal: Demo-grade full-stack implementation (frontend, backend, database, auth) of the "Next-Gen Hybrid ABHA Health Card" synopsis. Everything must be present, working, and look production-level, without being hardened for real production.

## 1. Confirmed Decisions

| Decision | Choice |
|---|---|
| Platform | Web app only (Next.js). No Flutter, no physical NFC hardware. |
| User roles | 3 roles: Patient, Hospital, Admin — each with own dashboard |
| Scope | Full synopsis scope: emergency QR profile, records, FHIR, NHCX claims, SOS, ABDM integration trace |
| Stack | Next.js + Tailwind (frontend), FastAPI (backend microservices), SQLite (per-service DBs), JWT auth |
| ABDM / NHCX | Simulated gateways built inside our own services — real-shaped endpoints, fully offline |
| Emergency QR | Backend-cached model: QR holds a signed token, scanner fetches the trauma profile from the backend. Trauma profile is AES-128-GCM encrypted at rest. |
| Database | SQLite, one file per microservice. SQLAlchemy ORM so PostgreSQL is a one-line switch later. |
| SOS alerts | Live WebSocket alerts on hospital dashboard + real email via SMTP (Gmail account configured via env vars) |
| Architecture | True microservices (5 services + NGINX gateway) per user decision |
| Theme | Editorial / Medical-Journal (see Section 7) |

## 2. Non-Goals

- Real ABDM Sandbox or NHCX registration — simulated internally.
- Real SMS dispatch — email only.
- Physical NFC / NTAG216 hardware — represented in UI copy, not implemented.
- Production hardening: no multi-node scaling, no external security audit, no CDN, no real OTP.

## 3. Architecture

```
Next.js frontend (single app, role-based areas)
        | HTTPS, all /api/* calls
NGINX API Gateway (routing, JWT signature verification, rate limiting)
        |
  +-----+------------------+-------------------+----------------------+
  |      |                  |                   |                      |
Identity & Auth   Records &        ABDM + FHIR          NHCX Claims
 Service          Encryption        Engine               Hub
 (identity.db)    (records.db)     (abdm.db)            (nhcx.db)
                                       |
                                 SOS & Notification Service
                                 (sos.db)
```

Services (each: own FastAPI app, own SQLite file, own uvicorn process):

1. **identity-service** — JWT issuance, bcrypt password hashing, RBAC, ABHA eKYC simulation, user/consent data.
2. **records-service** — patients, health records, emergency/trauma profiles, AES-128-GCM encryption + HMAC signing, QR token generation and scan resolution.
3. **abdm-service** — care contexts, consent artifacts, HL7 FHIR v4 bundle builder, ABDM sandbox simulator endpoints, integration trace log.
4. **nhcx-service** — bills, FHIR Claim mapping, adjudication state machine (SUBMITTED -> ADJUDICATED -> APPROVED/REJECTED), pre-auth, out-of-pocket estimation.
5. **sos-service** — alerts (trigger: QR_SCAN or PANIC), GPS tag, WebSocket broadcast to dashboards, email dispatch via SMTP.
6. **gateway** — NGINX config routing `/api/identity/*`, `/api/records/*`, `/api/abdm/*`, `/api/nhcx/*`, `/api/sos/*` to services; verifies JWT; CORS for frontend origin.

Reliability for the demo:
- docker-compose starts everything with health checks and dependency ordering; `./dev.sh` starts all services without Docker for development.
- Each service exposes `/health`. Gateway returns clean 503 with a human-readable message if a downstream service is down, so one dead service never breaks the whole demo.
- Internal service-to-service calls go over the compose network; every external-shaped gateway call is logged to `abdm_logs`.

## 4. Data Model (per-service ownership)

**identity.db**
- users: id, name, email, password_hash, role (patient|hospital|admin), abha_id (14-digit), phone, hospital_name (for hospital role)
- consent_artifacts: id, patient_id, hospital_id, scope, granted_at, expires_at, status (ACTIVE|REVOKED)

**records.db**
- patients: id, user_id, blood_group, allergies (JSON), chronic_conditions (JSON), medications (JSON), emergency_contacts (JSON [{name, phone, relation}])
- health_records: id, patient_id, type (Prescription|DiagnosticReport|Immunization), title, fhir_json (text), created_by (hospital user), created_at
- trauma_profiles: id, patient_id, encrypted_blob (AES-128-GCM), hmac_sha256, nonce, updated_at
- qr_tokens: id, patient_id, token (random 32-byte, HMAC-signed), created_at, active

**abdm.db**
- care_contexts: id, patient_id, record_ref, status (LINKED|CONSENT_PENDING|ACTIVE)
- abdm_logs: id, ts, direction (OUT|IN), endpoint, payload_snippet, status_code, latency_ms

**nhcx.db**
- bills: id, hospital_id, patient_id, line_items (JSON [{description, amount}]), total, created_at
- claims: id, bill_id, fhir_claim_json, status (SUBMITTED|ADJUDICATED|APPROVED|REJECTED), insurer_note, out_of_pocket, adjudicated_at

**sos.db**
- alerts: id, patient_id, trigger (QR_SCAN|PANIC), lat, lng, notified_contacts (JSON), email_status, created_at

## 5. Auth Flow

1. POST /api/identity/login (email + password) -> JWT containing sub, role, abha_id, exp (24h).
2. Frontend stores token in memory + localStorage; attaches Authorization header to all requests.
3. NGINX verifies JWT signature on every /api route before proxying (shared secret via env var).
4. Each service re-checks role claims for its own routes (defense in depth; also works when called directly).
5. ABHA eKYC flow: patient enters/links a demo 14-digit ABHA number; identity-service validates format + simulated registry lookup; UI shows a "eKYC verified" confirmation step with timestamp and mock transaction id.
6. Roles: patient (own data only), hospital (records/bills for consented patients), admin (global oversight). Seed accounts exist for all three roles.

## 6. Key Flows

**Emergency scan (public, no login):**
1. Patient's health card shows a QR encoding `SCAN_URL#token`.
2. Anyone opens /scan (public page), enters/scans token or opens the QR link.
3. records-service resolves token -> validates HMAC -> decrypts AES-128-GCM trauma profile -> returns profile.
4. Page renders blood group, allergies, chronic conditions, medications, emergency contacts, with an elapsed-time badge (server-timed, target under 800 ms).
5. Optional "Dispatch SOS" button -> sos-service creates alert, broadcasts over WebSocket to hospital dashboards, sends email to emergency contacts.

**Hospital record + bill flow:**
1. Hospital scans/looks up patient -> writes prescription or diagnostic report -> abdm-service converts to HL7 FHIR v4 JSON, links care context.
2. Hospital creates itemized bill -> "Push to NHCX" -> nhcx-service builds FHIR Claim -> simulated adjudication (2-4 s scripted delay for demo drama) -> status + out-of-pocket estimate shown to patient and hospital.

**SOS flow:** PANIC button on patient card, or SOS dispatch from scan page -> alert row -> WebSocket push -> hospital dashboard toast with sound and red pulse -> SMTP email to contacts.

## 7. Frontend Design Rules (Editorial / Medical-Journal)

Hard rules to avoid the generic AI-generated look:
- No purple/violet gradients, no glassmorphism, no glow shadows, no generic SaaS card grids with rounded-2xl shadows.
- Palette: warm paper background (#F5F2EA), ink black (#1C1917), muted stone text (#78716C), one medical accent (deep green #166534) plus clinical red (#B91C1C) reserved strictly for SOS/emergency.
- Typography: serif display (e.g., Libre Baskerville or Source Serif 4) for headings and big numbers; clean humanist sans (e.g., Inter) for body; monospace for IDs, tokens, and timing badges.
- Hairline rules (1px #1C1917) and section rules instead of card shadows. Layout uses asymmetrical editorial grids, not centered-card grids.
- Icons: Lucide icons only, small and sparse. No emoji anywhere in the product UI.
- Numbers displayed large in serif with small uppercase labels — the signature look of the dashboards.
- Motion: restrained. Decrypt animation = typed lines + counting timer, not confetti.

Pages (Next.js App Router):
- / — landing: editorial hero explaining the project, links to login and /scan.
- /login, /register (role select)
- /patient — card, records, emergency profile, consents, billing/claims
- /hospital — dashboard, scan patient, new record, billing, claims, SOS feed
- /admin — overview, ABDM trace, claims oversight, SOS audit
- /scan — public emergency scanner (no auth)

## 8. Seed Data

`seed.py` in each service (or one orchestrating script) creates on first run:
- Admin: admin@abha.dev; Hospital: city@abha.dev; Patients: aarav@abha.dev, diya@abha.dev (password: abha1234, shown on login page for demo convenience).
- 2 hospitals, 6 patients with varied blood groups/conditions, ~20 health records, 8 bills, 5 claims in different statuses, 3 historical SOS alerts, populated ABDM trace log.

## 9. Error Handling

- Every API error returns {detail, code} JSON; frontend shows inline banners styled to the theme.
- Gateway 503 fallback page explains which service is down.
- SOS email failure is logged and surfaced as status (EMAIL_FAILED) without blocking the alert.
- WebSocket reconnection on the hospital SOS feed with backoff.

## 10. Testing

- pytest per service: auth (login/RBAC), records (encrypt/decrypt round-trip, HMAC tamper rejection), FHIR builder (valid bundle shape), NHCX state machine, token scan resolution.
- One end-to-end script (requests-based) exercising login -> record -> bill -> claim -> SOS -> scan.
- Frontend: manual demo script; no Playwright (out of demo scope).

## 11. Deliverables / Repo Layout

```
health_card/
  frontend/          # Next.js app
  services/
    identity/  records/  abdm/  nhcx/  sos/
    shared/    # common JWT utils, config
  gateway/nginx.conf
  docker-compose.yml
  dev.sh
  seed scripts
  docs/superpowers/specs/  # this doc + plans
```

## 12. Risks

- Gmail SMTP needs an app password; env vars optional — if unset, email is skipped and status shows EMAIL_SKIPPED (demo still works).
- Six processes can confuse a live demo machine: mitigated by docker-compose one-command start and gateway 503 fallback.
- Camera QR scanning in browser requires HTTPS or localhost; the scanner page therefore also accepts manual token paste as primary path.
