---
title: "An ABHA-Integrated Emergency Health Card Prototype: Secure QR Retrieval, FHIR Interoperability, and Claims Synchronization"
authors: "Author One, Author Two, and Author Three"
affiliations: "Author One and Author Two, School of Computing, MIT-ADT University; Author Three, School of Computing, MIT-ADT University"
abstract: "India’s Ayushman Bharat Digital Mission has created the Ayushman Bharat Health Account (ABHA) as a national identity layer for consent-governed health records, yet emergency care still depends on rapidly knowing critical facts while administrative claims often remain disconnected from clinical workflows. This paper presents an implemented emergency health-card prototype that links ABHA identity, a rotating QR token, and a server-side trauma profile protected by AES-128-GCM and HMAC-SHA256. The system uses five FastAPI services behind an NGINX gateway, a role-based Next.js frontend, an HL7 FHIR R4 mapping layer, a locally simulated ABDM integration trace, a locally simulated National Health Claims Exchange (NHCX) claim state machine, and WebSocket plus SMTP notifications. Automated tests verify authentication, consent checks, authenticated encryption, tamper rejection, FHIR construction, claim transitions, and alert dispatch. A 1,000-request local benchmark reported a median wall time of 0.644 ms and a 95th-percentile time of 0.743 ms for emergency-token resolution, excluding QR capture, transport, and network delay. A 16-step end-to-end workflow also completed successfully. The contribution is a reproducible standards-aligned integration framework rather than a clinical or production-system validation. The paper distinguishes implemented controls from simulated gateways, identifies governance and deployment limitations, and outlines pathways toward offline NFC retrieval, stronger break-glass authorization, and real ABDM/NHCX conformance testing."
index_terms: "ABHA, ABDM, authenticated encryption, emergency health card, FHIR, healthcare interoperability, NHCX, rotating QR token"
---

## I. INTRODUCTION

Digital health programs increasingly rely on patient-facing identifiers, standardized clinical records, and consent-controlled information exchange. India’s ABDM was introduced to create a national digital-health infrastructure around ABHA, facility and professional registries, consent management, and health-information exchange [1]. Research assessments argue that enrollment alone does not produce clinical value unless providers, payers, and workflow participants actively use interoperable services [2]. Platform studies similarly show that national digital-health architectures require deliberate alignment of standards, open implementations, local context, and governance rather than simply deploying an identifier and an API [3].

Two separate information failures motivated this work. First, emergency care can require immediate access to a patient’s blood group, severe drug allergies, chronic conditions, medications, and emergency contacts. ABDM-enabled sharing is consent-governed and normally assumes network availability and an authenticated user context; an unconscious patient cannot complete mobile OTP verification, and connectivity may be poor in an accident zone or rural hospital. QR and mobile records can make health information available quickly, but prior studies also report uneven adoption and dependence on devices, network access, and user behavior [13], [14], [15]. A second failure concerns hospital finance. Diagnostic reports and itemized bills are often stored in proprietary hospital systems, causing manual claim preparation and settlement delay. NHCX is designed to move claims through a common provider-payer exchange, but its operational benefits depend on standardized, machine-readable transactions [5], [6]. Thus a useful next-generation health card must integrate three aspects: emergency readability, standardized clinical interoperability, and automated claims synchronization.

Prior work generally studies these components separately. FHIR provides reusable clinical resources and has been reviewed extensively for interoperability challenges [9], [10]. OAuth-based authorization and SMART-on-FHIR demonstrate how scoped tokens can protect application access [12], [22]. QR identity tags have been implemented in healthcare settings [13], while medical QR-code literature is broader than emergency trauma identification [16]. Cryptographic research addresses authenticated communication and privacy-preserving emergency access to health records, but does not itself decide who may initiate access, when access expires, or how misuse is reviewed [17], [19], [20], [21]. A targeted review of this literature did not locate an evaluated end-to-end prototype combining ABHA-linked emergency QR access, FHIR R4 clinical records, NHCX claim synchronization, and WebSocket/SMTP emergency notification. The contribution here is therefore an integrated prototype and reproducible evaluation framework.

The specific objectives are to: (1) construct an ABHA-linked role-based health-card frontend; (2) secure an emergency trauma profile using AES-128-GCM and HMAC-SHA256 and expose it through a rotating, backend-resolved QR token; (3) convert hospital events into FHIR R4 bundles and record a simulated ABDM integration trace; (4) map itemized bills into FHIR Claim resources and implement an explicit NHCX-shaped claim state machine; and (5) deliver GPS-tagged SOS events through WebSocket and email. The paper does not claim live ABDM or NHCX integration, physical NFC support, true zero-connectivity operation, production key management, clinical validation, or improved outcomes. These boundaries are discussed in Section VI.

The remainder is organized as follows. Section II summarizes the relevant standards and prior systems. Section III presents the design. Section IV describes the implementation. Section V reports automated and measured evaluation. Section VI discusses findings and limitations. Section VII concludes.

## II. BACKGROUND AND RELATED WORK

### A. ABDM, ABHA, and Consent-Centered Interoperability

ABDM provides an account-based digital-health foundation with ABHA identifiers and consent-aware workflows. Sharma et al. describe ABDM as a public digital infrastructure intended to support consent-governed interoperability across health systems [1]. Mishra et al. assess the mission’s implementation and emphasize that technical registries and accounts must be translated into meaningful provider use [2]. Mantri et al. argue that layered platform design and implementation choices determine whether national systems are usable across heterogeneous institutions [3]. The ABDM FHIR Implementation Guide builds these ideas on FHIR R4 resources and profiles, version 6.5.0 at the time of reference [4]. ABHA V3 APIs define account creation, session-token handling, and QR-related capabilities for integrators [7]. This project links patients to a simulated ABHA identity and uses locally generated traces, but it does not call the live ABDM registry or sandbox.

ABDM Scan and Share is a provider-oriented QR workflow for demographic sharing and registration; it is not a patient-carried emergency trauma card [8]. This distinction matters: the present prototype uses a rotating token to expose a minimum emergency profile and keeps full records behind authenticated and consent-checked APIs.

### B. FHIR and Claims Interoperability

FHIR R4 defines resources such as Patient, DiagnosticReport, MedicationRequest, and Claim, along with guidance for security and consent [9]. A systematic review of FHIR implementations finds continued challenges in semantic consistency, migration, and context-specific adaptation [10]. Kapitan et al. emphasize that open standards need usable implementations and adaptation to local workflows [11]. The SMART-on-FHIR model combines FHIR APIs with OAuth-style authorization to enable substitutable applications [12]; the present prototype uses bearer JWTs and role claims instead of the full SMART authorization stack, while retaining the idea that resource access is policy-controlled [22].

NHCX documentation specifies a provider-payer claim exchange using standardized FHIR-based transactions, protected message handling, asynchronous receipts, and callback-based status updates [5], [6]. The prototype does not connect to NHCX endpoints. Instead, it mirrors the principal clinical-to-claim path by converting bills to FHIR Claim resources and enforcing explicit state transitions inside its own NHCX Claims Hub service.

### C. Emergency Health Cards and QR Access

QR tags have been proposed and implemented as medical identity carriers. Uzun and Bilgin report a QR Code Identity Tag system for healthcare, demonstrating feasibility for quick identification [13]. Vella et al. find that smartphone-based emergency medical identification is available but underused in injured-patient care, indicating that technical presence does not guarantee adoption [14]. Bouri and Ravi examine mobile personal health records in emergencies and note potential benefits alongside power, connectivity, usability, and data-availability risks [15]. A systematic scoping review of medical QR applications shows that emergency identification is only one use case, with many applications oriented toward education, monitoring, and routine workflows [16].

These studies support using a QR link as an entry point, but they do not justify placing a complete medical profile in plaintext inside the QR code. The present design encodes an opaque token and keeps profile fields encrypted in the backend. The token still represents a capability if leaked, so rotation, active/inactive checks, and minimum disclosure are necessary; stronger break-glass governance remains an open issue.

### D. Security and Notification Architecture

Health-system security research repeatedly identifies access control, secure storage, auditing, and human factors as persistent challenges [18], [19]. Emergency access is especially difficult because the patient may not participate in authorization. Aljumah et al. study emergency access to encrypted personal health records hosted on untrusted infrastructure and highlight privacy-preserving mechanisms for scenarios in which the patient cannot authenticate [17]. Shamir’s threshold-sharing construction provides a theoretical basis for distributing emergency decryption authority among multiple parties, but it does not by itself resolve key rotation, revocation, recovery, or accountability [20]. Needham and Schroeder’s authenticated encryption work remains relevant to designing challenge-response and integrity-preserving communication [21]. The prototype applies AES-128-GCM and HMAC-SHA256 but leaves threshold key management as future work.

Notification also requires caution. RFC 6455 defines persistent bidirectional WebSocket communication, which can be used for low-latency dashboard alerts, but must be secured and tested for reconnect and ordering behavior [23]. SMTP defines asynchronous mail transport and store-and-forward behavior; it is a useful fallback but not a guaranteed immediate alert channel [24]. NIST’s current digital-identity guidance supports risk-based decisions about authenticators, federation, and lifecycle assurance, and is relevant to future emergency-actor identity design [25].

## III. SYSTEM DESIGN

### A. Design Goals and Scope

The prototype was guided by five goals. First, emergency information should be readable through a single QR scan without requiring the responder to log in. Second, trauma data should be encrypted and integrity-checked rather than exposed as plaintext in the card artwork. Third, clinical events should be represented as FHIR R4 resources and linked to care contexts. Fourth, billing should be convertible into claim resources with an auditable status path. Fifth, critical events should reach hospital staff and emergency contacts through complementary channels. A sixth engineering goal was independent service evolution, so each capability can be tested and replaced without monolithic coupling.

The design deliberately separates minimum emergency disclosure from longitudinal records. The QR profile contains only fields needed during immediate care; diagnosis history, FHIR bundles, claims, and administrative functions require authenticated role-appropriate access. The system treats the emergency token as a capability: possession of an active token is sufficient to read the sealed profile, so token rotation and integrity checking are integral to the design.

### B. Overall Architecture

Fig. 1 shows the architecture. A Next.js App Router frontend exposes patient, hospital, admin, and public-scanner areas. All service calls pass through an NGINX gateway, which routes `/api/<service>/<path>` to the corresponding FastAPI service and applies rate limiting. Five services own their own SQLite databases: identity, records, ABDM/FHIR, NHCX, and SOS. The gateway isolates transport concerns, while each service independently enforces role claims and database boundaries.

The ABDM and NHCX boundaries are locally simulated. The ABDM service generates FHIR resources, links care contexts, and records integration logs, but no request reaches the national sandbox. The NHCX service transforms itemized bills into FHIR Claim resources and manages adjudication states, but no real insurer callback is used. This separation lets the local implementation exercise workflow shapes without conflating local behavior with national-gateway certification.

![Fig. 1. Implemented ABHA health-card architecture, including service ownership and local simulation boundaries.](docs/paper/figures/architecture.png)

### C. Identity, Consent, and Role-Based Access

The identity service stores users, hashed passwords, roles, and consent artifacts. Patients, hospitals, and admins have distinct capabilities. Passwords are bcrypt-hashed. Login returns a JWT with subject, role, ABHA identifier, and expiry. The gateway can route authenticated traffic, but each service also validates bearer tokens, which provides defense in depth and keeps services independently callable.

Consent artifacts connect patient and hospital identities with scope, grant time, expiry, and status. A hospital can access a patient record only if the corresponding artifact is active, or through an authenticated emergency path. A hospital-facing patient list is therefore derived from active consent grants. Consent revocation is intended to make later administrative access fail, although network failures between services may require explicit resilience handling in production.

### D. Emergency Profile and QR Token Design

Each patient can define a trauma profile containing blood group, drug allergies, chronic conditions, medications, and emergency contacts. When the profile changes, the records service seals the JSON object into a compact binary structure. The seal operation uses AES-128-GCM with a fresh 12-byte nonce and stores ciphertext concatenated with the 16-byte authentication tag. An HMAC-SHA256 signature is then calculated over the encrypted data and tag. On retrieval, the service verifies HMAC-SHA256 before attempting AES-GCM decryption, ensuring that modified ciphertext or an invalid signature does not proceed to decryption.

The QR code does not contain patient identity or trauma fields. The patient requests a new token, which creates a random 32-byte hexadecimal value and deactivates prior tokens. The public `/emergency/resolve/{token}` route checks token existence and active status, verifies HMAC, decrypts AES-GCM, and returns only the minimum trauma profile with a server-measured elapsed time. The response time reported by the service therefore includes token lookup, integrity validation, decryption, and serialization, but not QR capture, TLS, network transit, or browser rendering.

![Fig. 2. Emergency QR-token retrieval and optional SOS workflow, including integrity and disclosure control points.](docs/paper/figures/emergency_flow.png)

If a responder chooses to dispatch SOS, the SOS service creates an alert, stores a GPS tag and trigger type, broadcasts the alert over WebSocket to connected hospital dashboards, and attempts SMTP email delivery to registered contacts. Missing or failing SMTP configuration produces an explicit email status rather than interrupting the WebSocket alert.

### E. Clinical Records and FHIR Mapping

Hospital users can create prescription or diagnostic entries for consented patients. The ABDM/FHIR service maps a prescription into a FHIR MedicationRequest-oriented bundle and a diagnostic report into a FHIR DiagnosticReport-oriented bundle. A patient reference uses the ABHA identifier, and the resulting bundle is associated with a care context. Each simulated gateway interaction writes a trace log containing timestamp, direction, endpoint, payload snippet, status, and latency. This trace supports auditability of the prototype’s integration workflow, although it is not equivalent to a national-gateway audit log.

### F. Claims Synchronization and State Machine

Fig. 3 shows the claim workflow. Hospital staff create an itemized bill, consisting of description and amount line items. A claim is created by mapping the bill into a FHIR Claim resource and marking it `SUBMITTED`. An admin can then adjudicate. The state machine permits only defined transitions: `SUBMITTED` to `ADJUDICATED`, then either `APPROVED` or `REJECTED`. Invalid transitions raise errors. The demo policy approves a claim under a configurable threshold and rejects high-value claims, producing an insurer note and an out-of-pocket estimate. This local policy is illustrative and is not an insurance rule, actuarial policy, or NHCX adjudication.

The prototype’s local state machine therefore verifies the sequencing of a claims workflow, but not the NHCX protocol’s message security, webhook semantics, idempotency, or certificate trust. Those require future sandbox conformance testing.

![Fig. 3. Hospital-record-to-FHIR-to-claim workflow, including the locally implemented NHCX-shaped state machine.](docs/paper/figures/claim_flow.png)

### G. Requirements-to-Evidence Traceability

Table I maps the design goals to implemented artifacts and the evaluation evidence reported in Section V.

**Table I. Requirements-to-implementation-to-evidence traceability.**

| Requirement | Impl. mechanism | Evidence |
|---|---|---|
| ABHA-linked role-based frontend | Patient, hospital, admin, and scanner areas; JWT claims | 3 identity tests and end-to-end logins |
| Minimum emergency disclosure | Encrypted trauma profile with five selected fields | Emergency-resolution workflow and profile assertions |
| Integrity before decryption | HMAC-SHA256 then AES-128-GCM verification | Four encryption tests, including tamper cases |
| Rotating emergency access | Random 32-byte token and deactivation of old tokens | New-token workflow and old-token 410 result |
| FHIR clinical interoperability | MedicationRequest and DiagnosticReport bundle builders | Three ABDM/FHIR tests and live conversion |
| Claims synchronization | Bill-to-Claim mapping and transition state machine | Three NHCX tests and claim adjudication |
| Emergency notification | WebSocket broadcast and SMTP fallback | Three SOS tests and live alert dispatch |

## IV. IMPLEMENTATION

### A. Service Ownership and Technology

The backend comprises five FastAPI applications, each owning a SQLite database: `identity.db`, `records.db`, `abdm.db`, `nhcx.db`, and `sos.db`. SQLite keeps the prototype self-contained, while SQLAlchemy abstracts database access and allows a future PostgreSQL migration with configuration changes. Shared helpers handle JWT decoding, bcrypt hashing, database engines, and configuration. NGINX provides routing and rate limiting. The frontend uses Next.js App Router, Tailwind CSS, and role-specific pages; the public scanner is intentionally unauthenticated, while clinical and administrative areas require bearer tokens.

Table II summarizes responsibilities and principal data. Each database owns exactly one bounded context, avoiding cross-service table writes.

**Table II. Service responsibilities and data ownership.**

| Service | Responsibilities | Owned data |
|---|---|---|
| Identity | Registration, login, RBAC, simulated eKYC, consents | Users, password hashes, ABHA identifiers, consent artifacts |
| Records | Trauma profiles, AES-GCM sealing, QR tokens, health records | Patient profiles, sealed profiles, QR tokens, health records |
| ABDM/FHIR | FHIR conversion, care contexts, simulated gateway trace | Care contexts, integration logs, converted bundles |
| NHCX | Itemized bills, FHIR Claim conversion, adjudication | Bills, claim resources, status, notes, out-of-pocket values |
| SOS | Panic and scan-triggered alerts, WebSocket, email | Alerts, GPS tags, contacts notified, email status |

### B. Frontend Roles and User Workflows

The patient page presents the health card, QR token, emergency-profile editor, record timeline, consents, and claims. The hospital page adds scan-patient input, record writing, billing, claims, and a live SOS feed. The admin page exposes service health, ABDM integration traces, claim adjudication, and SOS audit information. The scanner page accepts a token from the QR link or manual entry and renders the resolved profile with an elapsed-time badge.

This design keeps the emergency flow usable even when the responder does not have hospital credentials. It also makes the administrative audit visible without granting admins direct emergency-profile control.

### C. Data and Security Controls

The encrypted trauma profile consists of a hexadecimal ciphertext-plus-tag blob, nonce, HMAC-SHA256 signature, and timestamp. The seal/unseal pair is the primary confidentiality and integrity boundary. QR tokens are random, stored separately, and marked active or inactive. JWTs carry role claims but do not embed profile content. Internal service calls use a shared internal token for the SOS-to-records contact lookup. SMTP credentials are optional; if absent, the system records `EMAIL_SKIPPED`.

Table III lists principal controls and validation.

**Table III. Security controls and validation.**

| Control | Purpose | Validation |
|---|---|---|
| bcrypt password hashing | Prevent password retrieval from identity database | Identity service tests passed |
| JWT and role claims | Authenticate and constrain API access | Identity and cross-service tests passed |
| AES-128-GCM | Confidentiality of emergency profile | Seal/unseal round-trip passed |
| HMAC-SHA256 | Detect tampering before decryption | Tampered signature and ciphertext rejected |
| Rotating QR token | Limit replay of a lost or leaked card | Old token returned inactive status |
| Consent artifacts | Gate hospital access to longitudinal data | Missing-consent access was not allowed in test path |
| Internal token | Restrict service-to-service contact retrieval | Internal endpoint requires shared token |
| WebSocket authentication | Restrict hospital alert feed | Hospital/admin role required |

### D. Representative API Flow

The emergency sequence is compact:

1. The patient saves or updates a trauma profile, which triggers re-sealing.
2. The patient requests a QR token, which invalidates prior tokens.
3. The responder scans or opens the link, supplying only the token.
4. The records service verifies active state, checks HMAC, decrypts AES-GCM, and returns the minimum profile.
5. Optionally, the responder posts an SOS alert; the SOS service fetches contacts, broadcasts over WebSocket, and attempts email.

The claim sequence is similarly bounded:

1. A hospital creates an itemized bill.
2. The NHCX service builds a FHIR Claim resource and sets status to `SUBMITTED`.
3. An admin adjudicates.
4. The state machine transitions through `ADJUDICATED` to `APPROVED` or `REJECTED`, records the note, and computes the out-of-pocket amount.

### E. Reproduction Environment

The paper uses a self-contained source tree with `requirements.txt`, per-service tests, seed scripts, and `scripts/e2e.py`. Docker Compose can start all services and the frontend, while `dev.sh` starts the five backend processes locally. The tests and benchmark described below were run on an Apple silicon macOS 26.7.2 host using Python 3.13.12 and isolated temporary database files. Timing values are local measurements and should not be interpreted as production-network performance.

## V. EXPERIMENTAL EVALUATION

### A. Evaluation Design

The evaluation used three complementary methods: automated service tests, a live 16-step workflow, and a repeated emergency-token benchmark. Automated tests examine discrete controls. The live workflow verifies cross-service integration. The benchmark quantifies the server-side retrieval path under repeated in-process requests. No human-subject study, field deployment, or clinical-outcome evaluation was performed.

### B. Functional Correctness

The service test suites contained 19 tests across identity, records, ABDM/FHIR, NHCX, and SOS. All 19 passed. They included identity login and RBAC checks, emergency profile save and QR rotation, old-token invalidation, AES-GCM round trips, tampered-signature and tampered-ciphertext rejection, FHIR resource construction, ABDM trace behavior, NHCX state transitions, and SOS alert/WebSocket behavior.

The live workflow then completed all 16 steps. It checked five service health endpoints, patient, hospital, and admin logins, consented record listing, emergency profile generation and resolution, hospital record creation, FHIR conversion with care context, bill creation, claim submission, claim adjudication, SOS dispatch, and ABDM trace retrieval. The emergency resolution reported 0 ms by the service’s integer timer, and the workflow asserted success below the 800-ms design threshold.

### C. Emergency Retrieval Latency

A benchmark of 1,000 measured requests was executed after 50 warmup requests against an isolated temporary records database. The measured wall time was the time from request dispatch to completed response inside the TestClient process. Because the service reports elapsed time as an integer, many high-speed local calls round to 0 ms. The wall-time statistics therefore provide finer resolution. The distribution was: minimum 0.612 ms, median 0.644 ms, mean 0.661 ms, 95th percentile 0.743 ms, and maximum 1.908 ms. All 1,000 requests returned HTTP 200 and produced the expected blood-group and allergy fields.

A simple decomposition of the measured retrieval path is:

T_local = T_route + T_tok + T_HMAC + T_AES + T_ser   (1)

where `T_route` includes routing to the resolver, `T_token` includes token lookup and active-state checking, `T_HMAC` includes signature verification, `T_AES` includes authenticated decryption, and `T_serialize` includes response serialization. The measured quantity is local and excludes QR acquisition, TLS, networking, browser rendering, and user interpretation.

### D. Security Validation

The cryptographic tests first verified that sealing and unsealing recover the original profile. Then they altered the HMAC signature and separately flipped a ciphertext byte; both tampered inputs were rejected without returning profile data. A further test confirmed that the stored signature equals the HMAC of the ciphertext-plus-tag data. Identity tests confirmed that missing or invalid bearer tokens fail and that login checks role claims. Consent tests confirmed that a hospital cannot list a patient’s records in the tested missing-consent path. The QR rotation test confirmed that an old token returned HTTP 410 after a new token was issued.

### E. Claims and Notification Validation

NHCX tests verified that a bill creates a FHIR Claim resource, that valid adjudication transitions complete, and that invalid transitions fail. The live workflow created a 700-unit test bill, submitted it, and approved it through admin adjudication. SOS tests verified alert creation and WebSocket delivery behavior; the live workflow dispatched a PANIC alert successfully. SMTP delivery status was recorded rather than asserted as delivered, because email may be skipped or fail without affecting the WebSocket path.

### F. Quantitative Summary

Table IV summarizes the principal measured and observed outcomes.

**Table IV. Measured evaluation results.**

| Evaluation item | Outcome | Context |
|---|---|---|
| Service unit/integration tests | 19/19 passed | Identity, records, ABDM/FHIR, NHCX, SOS |
| End-to-end workflow | 16/16 steps passed | Five live local services on ports 8001-8005 |
| Emergency requests benchmarked | 1,000 measured + 50 warmup | Isolated temporary records database |
| HTTP status distribution | 1,000 x HTTP 200 | Expected profile fields asserted each request |
| Median wall time | 0.644 ms | Local in-process retrieval, no network |
| Mean wall time | 0.661 ms | Same local protocol |
| 95th percentile wall time | 0.743 ms | Same local protocol |
| Minimum/maximum wall time | 0.612/1.908 ms | Same local protocol |
| Service-reported resolution median | 0 ms | Integer timer truncated sub-millisecond values |
| Emergency design threshold | < 800 ms | Met for all benchmark and live workflow cases |

### G. Threats to Validity

The benchmark is not representative of field conditions. QR scanning, device startup, TLS handshake, network loss, and human reaction dominate an emergency response. The TestClient also bypasses NGINX, so the benchmark isolates service logic rather than gateway latency. SQLite differs from PostgreSQL in concurrency behavior. The state-machine decision uses a local threshold and should not be read as a payer policy. Finally, tests use deterministic synthetic users and profiles; they do not establish usability, clinician comprehension, or clinical safety.

## VI. DISCUSSION

### A. What the Prototype Demonstrates

The results support three claims within their tested boundaries. First, it is feasible to combine a minimum-disclosure emergency QR flow, ABHA-linked identity, FHIR R4 record construction, and claims synchronization in one microservice system. Second, authenticated encryption can protect trauma fields at rest while allowing sub-millisecond local retrieval in an in-process test. Third, the workflow is reproducible: all service tests and all end-to-end steps passed on a clean local run.

The integration is more distinctive than any single technology. FHIR, ABDM, NHCX, QR access, and notification mechanisms are individually known. The prototype shows how they can be arranged so that an emergency flow and an administrative flow use the same patient identity, records, service boundaries, and audit traces without assuming live national connectivity.

### B. Comparison with Related Approaches

Table V contrasts the prototype with representative related approaches. The comparison is qualitative and is not a benchmark of those systems.

**Table V. Comparison with representative related approaches.**

| Aspect | Related approaches | Proposed prototype |
|---|---|---|
| Emergency entry | QR identification or mobile records [13]-[15] | Rotating token linked to encrypted minimum profile |
| Data exposure | Often identity or selected mobile record fields | Five emergency fields decrypted only after integrity check |
| Identity context | May not be tied to national health account | ABHA identifier in JWT and simulated eKYC |
| Clinical interoperability | Usually not complete FHIR workflow | FHIR R4 MedicationRequest/DiagnosticReport bundles |
| Claims synchronization | Typically absent from emergency-card work | FHIR Claim and explicit local NHCX state machine |
| Notification | Device-dependent or unspecified | WebSocket plus SMTP fallback |
| Evaluation focus | Feasibility/adoption barriers [14]-[16] | Tests, live workflow, repeated local retrieval benchmark |

The prototype therefore extends prior QR-card feasibility work by coupling emergency access to the patient identity, clinical interoperability, and claims layers, while retaining the prior literature’s cautions about adoption, usability, and availability.

Compared with generic mobile personal health records in emergencies [15], it separates emergency retrieval from full longitudinal records and uses a rotating token. Compared with SMART-on-FHIR application authorization [12], the prototype uses a simpler bearer-token and role-claim model suitable for a local prototype, but future production integration should evaluate SMART-style scopes and consent-aware authorization. Compared with NHCX documentation [5], [6], the local implementation mirrors claim resource construction and transition states but lacks the exchange’s real message-protection and callback behavior. Compared with emergency cryptographic systems [17], the prototype achieves authenticated encryption but not a fully governed break-glass protocol.

### C. Governance and Security Gaps

Encryption ensures that a passive observer cannot read the trauma profile from stored ciphertext, but it does not answer who may scan, when, why, or what happens afterward. Emergency QR access requires explicit break-glass rules, actor accountability, minimum-data justification, expiry, post-access review, and misuse handling. The current public endpoint records a token’s active state but does not yet require responder identification or dual-control authorization. NIST digital-identity guidance can inform these choices, but emergency assurance must be balanced with availability [25].

Key management also remains a limitation. The trauma key is currently configured from an environment variable for the prototype. Production deployment requires managed key storage, rotation, separation of duties, cryptographic agility, and recovery procedures. Threshold schemes could distribute emergency decryption capability, but they introduce participant selection, reconstruction delay, revocation, and audit challenges that must be engineered, not assumed [20].

QR capability leakage is another concern. A scanned token grants access to the emergency profile while active. Rotation limits the lifetime of a leaked token, but the system still needs detection of anomalous scanning, rate limits, audit records, and user notification. The public endpoint also must avoid revealing whether an unknown token exists for a different patient in ways that help enumeration.

### D. Claims and Notification Boundaries

The simulated NHCX service validates workflow sequencing and FHIR-shaped claim creation, but real NHCX conformance requires protected exchange, certificates, asynchronous receipts, callbacks, idempotency, retries, and reconciliation. Likewise, WebSocket alerts can arrive rapidly when connected, but they need explicit tests for reconnect, ordering, duplicate suppression, and authorization. SMTP is asynchronous and should be treated as fallback, not as a real-time clinical notification guarantee [23], [24].

### E. Limitations and Future Work

The implemented scope is intentionally narrower than the original synopsis. The project does not implement physical NTAG216 NFC storage or local decryption. It uses a backend-resolved QR token, so complete zero-connectivity operation is not achieved. It does not send SMS; it uses WebSocket and optional SMTP. It does not register with live ABDM or NHCX sandboxes. It uses SQLite rather than a production database cluster, a local demonstration key rather than a managed key vault, and no external security audit.

Future work should address: (1) NFC or partially cached offline profiles with explicit staleness indicators and safer break-glass decryption; (2) real ABDM FHIR IG and NHCX conformance testing against current versions; (3) managed key rotation and threshold-based recovery; (4) responder identity, access logging, and post-event review; (5) simulated degraded-network tests, including stale profiles, replay, and partial disclosure; (6) alert reliability tests with reconnect and acknowledgement escalation; and (7) prospective usability studies with emergency clinicians and representative patients.

## VII. CONCLUSION

This paper presented an implemented ABHA-linked emergency health-card prototype that connects secure emergency retrieval, FHIR R4 interoperability, claims synchronization, and emergency notification. The system uses independent FastAPI services, explicit consent artifacts, AES-128-GCM and HMAC-SHA256 protection, rotating QR tokens, locally simulated ABDM and NHCX boundaries, and WebSocket plus SMTP alerts. Nineteen service tests and a sixteen-step live workflow passed. In a 1,000-request local benchmark, emergency-token retrieval had a median wall time of 0.644 ms and a 95th-percentile wall time of 0.743 ms. The work demonstrates technical feasibility and reproducible integration, while explicitly excluding clinical effectiveness, live national-gateway certification, offline NFC capability, and production deployment. The principal research contribution is the tested integration framework and the evaluation boundaries needed before such a system can move toward real emergency and payer workflows.

## APPENDIX

### A. Endpoint Map

**Table VI. Endpoint map.**

| Area | Endpoint | Purpose |
|---|---|---|
| Identity | `POST /login` | Obtain bearer JWT and role |
| Identity | `GET /patients` | List consent-visible patients |
| Records | `PUT /emergency/profile` | Save and re-seal trauma profile |
| Records | `POST /emergency/qr` | Create new QR token |
| Records | `GET /emergency/resolve/{token}` | Resolve emergency profile publicly |
| Records | `POST /records` | Add clinical record |
| ABDM/FHIR | `POST /fhir/convert` | Convert record and link care context |
| ABDM/FHIR | `GET /logs` | Retrieve integration trace |
| NHCX | `POST /bills` | Create itemized bill |
| NHCX | `POST /claims` | Submit FHIR Claim |
| NHCX | `POST /claims/{id}/adjudicate` | Apply state transition |
| SOS | `POST /alerts` | Create GPS-tagged alert |
| SOS | `GET /alerts/ws` | Receive hospital alert stream |

### B. Reproduction Outline

The service tests can be run with Python 3.13 by installing `requirements.txt` and executing `pytest services/*/tests -q`. The live workflow is `scripts/e2e.py` after starting the five services on ports 8001-8005. The emergency benchmark uses an isolated temporary records database, 50 warmup requests, and 1,000 measured requests through the `/emergency/resolve/{token}` route. All timing values in this paper are local and exclude QR acquisition and transport.

## ACKNOWLEDGMENT

The authors thank the School of Computing, MIT-ADT University, for project supervision and the ABHA Health Card team for implementation support.

## REFERENCES

[1] R. S. Sharma, A. Rohatgi, S. Jain, and D. Singh, “The Ayushman Bharat Digital Mission (ABDM): making of India’s Digital Health Story,” CSI Transactions on ICT, vol. 11, no. 1, pp. 3-9, 2023.  
[2] U. S. Mishra, S. Yadav, and W. Joe, “The Ayushman Bharat Digital Mission of India: An assessment,” Health Systems & Reform, vol. 10, no. 2, article 2392290, 2024.  
[3] M. Mantri, G. Sunder, S. Kadam, and A. Abhyankar, “A perspective on digital health platform design and its implementation at national level,” Frontiers in Digital Health, vol. 6, article 1260855, 2024.  
[4] National Resource Center for EHR Standards, FHIR Implementation Guide for ABDM, version 6.5.0, May 2025. [Online]. Available: https://www.nrces.in/ndhm/fhir/r4/index.html  
[5] National Health Authority, NHCX Developer Documentation: Claim Settlement, version 1, updated Oct. 2026. [Online]. Available: https://docs.abdm.gov.in/docs/nhcx/v1  
[6] National Health Authority, NHCX Implementation Guide for Payers, 2026-27. [Online]. Available: https://abdm.gov.in/strapicms/uploads/NHCX_Implementation_Guide_for_Payers_2026_1_66f3fbcee1.pdf  
[7] National Health Authority, Integrator Guide ABDM ABHA V3 APIs, version 1.2, Oct. 2024. [Online]. Available: https://sandboxcms.abdm.gov.in/uploads/ABDM_ABHA_V3_AP_Is_SOP_V1_1_4_faef8099bd.pdf  
[8] National Health Authority, Sandbox Documentation: ABDM Scan and Share, version 1.0, Aug. 2024. [Online]. Available: https://sandboxcms.abdm.gov.in/uploads/Scan_and_share_Document_Updated_1_0_22_Aug_2024_c1b570cbf6.pdf  
[9] Health Level Seven International, HL7 FHIR Release 4, version 4.0.1, 2019. [Online]. Available: https://hl7.org/fhir/R4/  
[10] M. Ayaz, M. F. Pasha, M. Y. Alzahrani, R. Budiarto, and D. Stiawan, “The Fast Healthcare Interoperability Resources (FHIR) standard: Systematic literature review of implementations, applications, challenges and opportunities,” JMIR Medical Informatics, vol. 9, no. 7, article e21929, 2021.  
[11] D. Kapitan, F. Heddema, A. Dekker, M. Sieswerda, B.-J. Verhoeff, and M. Berg, “Data interoperability in context: The importance of open-source implementations when choosing open standards,” Journal of Medical Internet Research, vol. 27, article e66616, 2025.  
[12] J. C. Mandel, D. A. Kreda, K. D. Mandl, I. S. Kohane, and R. B. Ramoni, “SMART on FHIR: A standards-based, interoperable apps platform for electronic health records,” Journal of the American Medical Informatics Association, vol. 23, no. 5, pp. 899-908, 2016.  
[13] V. Uzun and S. Bilgin, “Evaluation and implementation of QR Code Identity Tag system for Healthcare in Turkey,” SpringerPlus, vol. 5, no. 1, article 1454, 2016.  
[14] M. A. Vella, H. Li, P. M. Reilly, and S. S. Raza, “Unlocked yet untapped: The ubiquitous smartphone and utilization of emergency medical identification technology in the care of the injured patient,” Surgery Open Science, vol. 2, no. 3, pp. 122-126, 2020.  
[15] N. Bouri and S. Ravi, “Going mobile: How mobile personal health records can improve health care during emergencies,” JMIR mHealth and uHealth, vol. 2, no. 1, article e8, 2014.  
[16] A. Faggiano, F. Fioretti, S. Nodari, and S. Carugo, “Quick response code applications in medical and cardiology settings: A systematic scoping review,” European Heart Journal - Digital Health, vol. 2, no. 2, pp. 336-341, 2021.  
[17] F. Aljumah, R. H. M. Leung, M. Pourzandi, and M. Debbabi, “Emergency mobile access to personal health records stored on an untrusted cloud,” in Health Information Science, Lecture Notes in Computer Science, vol. 7798, Berlin, Germany: Springer, 2013, pp. 30-41.  
[18] F. Jin, B. Wang, X. Liao, K. Wang, W. Huang, and T. Wang, “Exploring data security risks associated with trauma medical data within hospitals in China: A qualitative study,” BMJ Open, vol. 15, no. 2, article e085221, 2025.  
[19] P. Shojaei, E. Vlahu-Gjorgievska, and Y.-W. Chow, “Security and privacy of technologies in health information systems: A systematic literature review,” Computers, vol. 13, no. 2, article 41, 2024.  
[20] A. Shamir, “How to share a secret,” Communications of the ACM, vol. 22, no. 11, pp. 612-613, 1979.  
[21] R. M. Needham and M. D. Schroeder, “Using encryption for authentication in large networks of computers,” Communications of the ACM, vol. 21, no. 12, pp. 993-999, 1978.  
[22] D. Hardt, Ed., “The OAuth 2.0 Authorization Framework,” RFC 6749, Internet Engineering Task Force, Oct. 2012. [Online]. Available: https://www.rfc-editor.org/info/rfc6749/  
[23] I. Fette and A. Melnikov, “The WebSocket Protocol,” RFC 6455, Internet Engineering Task Force, Dec. 2011. [Online]. Available: https://www.rfc-editor.org/info/rfc6455/  
[24] J. Klensin, “Simple Mail Transfer Protocol,” RFC 5321, Internet Engineering Task Force, Oct. 2008. [Online]. Available: https://www.rfc-editor.org/info/rfc5321/  
[25] D. Temoshok, D. Proud-Madruga, Y.-Y. Choong, R. Galluzzo, S. Gupta, C. LaSalle, N. Lefkovitz, and A. Regenscheid, Digital Identity Guidelines, NIST Special Publication 800-63-4, Aug. 2025.
