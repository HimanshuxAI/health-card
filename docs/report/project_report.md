---
title: "ABHA Health Card: Secure Emergency Retrieval, FHIR Interoperability, and Claims Synchronization"
student_name: "[Student Name]"
prn: "[PRN/Enrollment No.]"
guide: "[Guide Name]"
department: "Department of Computer Science and Engineering"
university: "MIT Art, Design and Technology University"
campus: "MIT School of Computing, Rajbaug Campus, Loni-Kalbhor, Pune 412201"
academic_year: "2026-27"
group: "SY1512"
---

# COVER PAGE

A PROJECT REPORT ON

ABHA HEALTH CARD: SECURE EMERGENCY RETRIEVAL, FHIR INTEROPERABILITY, AND CLAIMS SYNCHRONIZATION

SUBMITTED TO

MIT SCHOOL OF COMPUTING, LONI, PUNE IN PARTIAL FULFILLMENT OF THE REQUIREMENTS FOR THE AWARD OF THE DEGREE

BACHELOR OF TECHNOLOGY

(Computer Science and Engineering)

BY

[Student Name] [PRN/Enrollment No.: -----]

Under the guidance of

[Guide Name]

DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING

MIT School of Computing

MIT Art, Design and Technology University

Rajbaug Campus, Loni-Kalbhor, Pune 412201

2026-27

# CERTIFICATE

This is to certify that the project report entitled "ABHA Health Card: Secure Emergency Retrieval, FHIR Interoperability, and Claims Synchronization" submitted by [Student Name] [PRN/Enrollment No.: -----] is a bonafide work carried out under the supervision of [Guide Name] and is submitted towards the partial fulfillment of the requirement of MIT ADT University, Pune for the award of the degree of Bachelor of Technology (Computer Science and Engineering).

Prof. [Guide Name] Dr. [Head of Department]

Guide Head of Department

Prof. Suresh Kapare Dr. Ganesh Pathak

Chief Coordinator-PBL Dean

Seal/Stamp of the College

Place: PUNE

Date:

# COMPANY CERTIFICATE

This is to certify that the Project report entitled "ABHA Health Card: Secure Emergency Retrieval, FHIR Interoperability, and Claims Synchronization" submitted by [Student Name] [Exam No.: -----] is a bonafide work carried out under the supervision of [Industry Mentor] and has been completed successfully.

[Industry Mentor Name]

[Designation]

External Guide

Seal/Stamp of the Company/College

Place: Pune

Date:

# DECLARATION

We, the team members of Group SY1512, hereby declare that the project work incorporated in the present project entitled "ABHA Health Card: Secure Emergency Retrieval, FHIR Interoperability, and Claims Synchronization" is original work. This work (in part or in full) has not been submitted to any University for the award of a Degree or a Diploma. We have properly acknowledged the material collected from secondary sources wherever required. We solely own the responsibility for the originality of the entire content.

Date: 17/11/2026

Member 1: __________________ [Name, PRN]

Member 2: __________________ [Name, PRN]

Member 3: __________________ [Name, PRN]

Name and Signature of Guide

Seal/Stamp of the College

Place: Pune

Date: 17/11/2026

# EXAMINER'S APPROVAL CERTIFICATE

The project report entitled "ABHA Health Card: Secure Emergency Retrieval, FHIR Interoperability, and Claims Synchronization" submitted by Student 1 (MITU2026BTCS00xx), Student 2 (MITU2026BTCS01xx), Student 3 (MITU2026BTCS00xx) in partial fulfillment for the award of the degree of Bachelor of Technology (Computer Science and Engineering) during the academic year 2026-27, of MIT-ADT University, MIT School of Computing, Pune, is hereby approved.

Examiners:

1.

2.

# ACKNOWLEDGEMENT

The completion of this project report would not have been possible without the support of several people. I express my sincere gratitude to [Guide Name], Guide, Department of Computer Science and Engineering, MIT School of Computing, for continuous guidance, technical suggestions, and patience throughout the project. I also thank the Head of Department, the project coordinator, and the faculty members for their feedback during reviews.

I thank the industry mentor for sharing practical constraints around hospital workflows, claims handling, and patient privacy. The discussions helped shape the scope of the prototype and prevented the design from drifting into unsupported claims.

Finally, I thank my teammates in Group SY1512, my family, and my friends for their encouragement during implementation and testing.

[Student Name], [PRN]

# ABSTRACT

India's Ayushman Bharat Digital Mission has created the Ayushman Bharat Health Account as a national identity layer for consent-governed health records, yet emergency care still depends on rapidly knowing critical facts while administrative claims often remain disconnected from clinical workflows. This project implements an ABHA-linked emergency health card prototype that combines a rotating QR token, a server-side trauma profile protected by AES-128-GCM and HMAC-SHA256, five FastAPI services behind an NGINX gateway, a role-based Next.js frontend, HL7 FHIR R4 mapping, a locally simulated ABDM integration trace, a locally simulated National Health Claims Exchange claim state machine, and WebSocket plus SMTP notifications. Automated tests verify authentication, consent checks, authenticated encryption, tamper rejection, FHIR construction, claim transitions, and alert dispatch. A 1,000-request local benchmark reports a median wall time of 0.644 ms and a 95th-percentile time of 0.743 ms for emergency-token resolution, excluding QR capture, transport, and network delay. A 16-step end-to-end workflow completes successfully. The contribution is a reproducible standards-aligned integration framework rather than a clinical or production-system validation. The report distinguishes implemented controls from simulated gateways and identifies governance, deployment, and evaluation limitations.

# CONTENTS

[TOC]

# LIST OF FIGURES

Figure 2.1 Implemented ABHA health-card architecture

Figure 2.2 Emergency QR-token retrieval and SOS workflow

Figure 2.3 Hospital-record to FHIR to claim workflow

# LIST OF TABLES

Table 1.1 Existing systems and limitations

Table 2.1 Service responsibilities and data ownership

Table 3.1 Literature survey

Table 4.1 Project phase estimates

Table 5.1 Functional requirements

Table 5.2 Non-functional requirements

Table 5.3 Data model summary

Table 6.1 Security controls and validation

Table 8.1 Unit and integration test inventory

Table 8.2 End-to-end workflow steps

Table 8.3 Benchmark results

Table 9.1 Implemented scope versus original synopsis

Table A.1 Endpoint map

Table B.1 Data dictionary

Table E.1 Test case summary
# CHAPTER 1: INTRODUCTION

## 1.1 Background

Digital health programs depend on patient-facing identifiers, standardized clinical records, and consent-controlled information exchange. India's Ayushman Bharat Digital Mission was introduced to create national digital-health infrastructure around the Ayushman Bharat Health Account, facility and professional registries, consent management, and health-information exchange. Research assessments argue that enrollment alone does not produce clinical value unless providers, payers, and workflow participants actively use interoperable services. Platform studies similarly show that national digital-health architectures require deliberate alignment of standards, open implementations, local context, and governance rather than simply deploying an identifier and an API.

Two separate information failures motivated this work. First, emergency care requires immediate access to a patient's blood group, severe drug allergies, chronic conditions, medications, and emergency contacts. ABDM-enabled sharing is consent-governed and normally assumes network availability and an authenticated user context. An unconscious patient cannot complete mobile OTP verification, and connectivity may be poor in an accident zone or rural hospital. QR and mobile records can make health information available quickly, but prior studies report uneven adoption and dependence on devices, network access, and user behavior. Second, hospital finance suffers from proprietary storage of diagnostic reports and itemized bills, causing manual claim preparation and settlement delay. NHCX is designed to move claims through a common provider-payer exchange, but its operational benefits depend on standardized, machine-readable transactions. A useful health card must therefore integrate emergency readability, standardized clinical interoperability, and automated claims synchronization.

## 1.2 Problem Statement

Emergency responders need a minimum patient profile within seconds, while longitudinal records and billing data must remain protected behind authenticated and consent-checked APIs. Existing systems often treat these needs separately. QR identification tags may expose too much or too little information. Mobile personal health records depend on device availability and user interaction. Claims workflows usually sit outside emergency care systems. The project addresses this gap by building an integrated prototype in which one patient identity flows through emergency retrieval, clinical record creation, FHIR conversion, claim submission, adjudication, and emergency notification.

## 1.3 Existing Work

A review of related systems shows that individual components are available, but evaluated end-to-end integration is rare. QR identification systems demonstrate feasibility for quick identification. Smartphone-based emergency medical identification is available but underused. Mobile personal health records offer potential benefits alongside power, connectivity, usability, and data-availability risks. FHIR provides reusable clinical resources, while SMART-on-FHIR demonstrates scoped authorization. NHCX documentation specifies standardized claim exchange. Cryptographic research addresses emergency access to encrypted health records but does not resolve actor identity, expiry, and misuse review. The project therefore contributes an integrated prototype and reproducible evaluation framework.

Table: Existing systems and limitations

| System or approach | Strength | Limitation addressed by this project |
| QR identity tag | Fast identification | No encrypted trauma profile or token rotation |
| Mobile personal health record | Patient-controlled data | Requires device interaction and connectivity |
| FHIR-based interoperability | Standard resources | Usually no emergency QR path |
| NHCX claims exchange | Standardized payer flow | Usually separate from clinical workflow |
| Encrypted health record research | Privacy protection | No end-to-end implementation and audit |

## 1.4 Motivation

The project began with a practical question: how can a patient carry a small, readable artifact that helps during an emergency without exposing the complete medical record? The answer had to respect ABDM identity concepts, avoid plaintext medical data in the card artwork, and still support hospital workflows after the emergency. The team also wanted to demonstrate that claims can be generated from the same clinical events rather than re-entered manually. These motivations shaped the prototype into a system with clear service boundaries and measurable behavior.

## 1.5 Objectives

The specific objectives were to:

1. Construct an ABHA-linked role-based health-card frontend for patient, hospital, and admin users.
2. Secure an emergency trauma profile using AES-128-GCM and HMAC-SHA256 and expose it through a rotating, backend-resolved QR token.
3. Convert hospital events into FHIR R4 bundles and record a simulated ABDM integration trace.
4. Map itemized bills into FHIR Claim resources and implement an explicit NHCX-shaped claim state machine.
5. Deliver GPS-tagged SOS events through WebSocket and email.
6. Provide reproducible tests and a local benchmark for emergency retrieval.

## 1.6 Scope

The implemented scope includes identity and role-based access, consent artifacts, emergency profile sealing, QR token rotation, public emergency resolution, clinical record creation, FHIR conversion, care contexts, bill creation, claim submission and adjudication, SOS alerts, WebSocket broadcast, SMTP fallback, an admin audit view, and deployment artifacts. The project does not implement physical NFC storage, complete offline decryption, live ABDM or NHCX integration, SMS delivery, production key management, or clinical validation. These boundaries are reported as limitations rather than hidden gaps.

# CHAPTER 2: CONCEPTS AND METHODS

## 2.1 System Architecture

![Figure 2.1: Implemented ABHA health-card architecture](docs/paper/figures/architecture.png)

The prototype uses a Next.js frontend, an NGINX gateway, and five FastAPI services. Each service owns one SQLite database. The gateway routes requests and applies rate limiting, while each service validates bearer tokens independently. This arrangement keeps transport concerns separate from business rules and allows services to be tested in isolation.

Figure 2.1 shows the architecture. Patient, hospital, and admin areas in the frontend call the gateway. The gateway forwards traffic to identity, records, ABDM/FHIR, NHCX, and SOS services. Service-to-service calls use HTTP and a shared internal token where needed.

## 2.2 Identity and Consent

The identity service stores users, bcrypt-hashed passwords, roles, ABHA identifiers, and consent artifacts. Login returns a JWT containing subject, role, ABHA identifier, and expiry. Consent artifacts connect patient and hospital identities with scope, grant time, expiry, and status. A hospital can access a patient's records only when the corresponding artifact is active, or through an authenticated emergency path. Consent revocation takes effect on the next request.

## 2.3 Emergency Profile and QR Token

![Figure 2.2: Emergency QR-token retrieval and SOS workflow](docs/paper/figures/emergency_flow.png)

Each patient can define a trauma profile containing blood group, drug allergies, chronic conditions, medications, and emergency contacts. When the profile changes, the records service seals the JSON object. The seal uses AES-128-GCM with a fresh 12-byte nonce and stores ciphertext concatenated with the 16-byte authentication tag. An HMAC-SHA256 signature is calculated over the encrypted data and tag. On retrieval, the service verifies HMAC-SHA256 before attempting AES-GCM decryption.

The QR code contains an opaque token, not patient data. The patient can read the current token without rotating it, which keeps printed cards valid. A deliberate regeneration request creates a random 32-byte hexadecimal token and deactivates prior tokens. The public emergency resolution route checks token existence and active status, verifies HMAC, decrypts AES-GCM, and returns only the minimum trauma profile with a server-measured elapsed time.

## 2.4 FHIR and Clinical Records

Hospital users can create prescription or diagnostic entries for consented patients. The ABDM/FHIR service maps a prescription into a FHIR MedicationRequest-oriented bundle and a diagnostic report into a FHIR DiagnosticReport-oriented bundle. A patient reference uses the ABHA identifier, and the resulting bundle is associated with a care context. Each simulated gateway interaction writes a trace log containing timestamp, direction, endpoint, payload snippet, status, and latency.

## 2.5 Claims Synchronization

![Figure 2.3: Hospital-record to FHIR to claim workflow](docs/paper/figures/claim_flow.png)

Hospital staff create an itemized bill consisting of description and amount line items. A claim is created by mapping the bill into a FHIR Claim resource and marking it SUBMITTED. An admin can then adjudicate. The state machine permits only defined transitions: SUBMITTED to ADJUDICATED, then either APPROVED or REJECTED. Invalid transitions raise errors. The demo policy approves a claim under a configurable threshold and rejects high-value claims, producing an insurer note and an out-of-pocket estimate. This local policy is illustrative and is not an insurance rule or NHCX adjudication.

## 2.6 Notification Architecture

If a responder dispatches SOS, the SOS service creates an alert, stores a GPS tag and trigger type, broadcasts the alert over WebSocket to connected hospital dashboards, and attempts SMTP email delivery to registered contacts. Missing or failing SMTP configuration produces an explicit email status rather than interrupting the WebSocket alert. This gives the system a fast path and a fallback path.

# CHAPTER 3: LITERATURE SURVEY

The literature survey below summarizes the sources used in the companion paper. Each row states the source, its contribution, and its relevance to this project.

Table: Literature survey

| ID | Source | Contribution | Relevance |
| 1 | Sharma et al., ABDM digital health story | ABDM as public digital infrastructure | Identity and consent context |
| 2 | Mishra et al., ABDM assessment | Technical registries must become provider use | Implementation realism |
| 3 | Mantri et al., platform design | Layered platform design | Architecture decisions |
| 4 | ABDM FHIR Implementation Guide v6.5.0 | FHIR profiles for ABDM | Resource mapping |
| 5 | NHCX developer documentation | Claim settlement flow | Claims design |
| 6 | NHCX implementation guide for payers | Provider-payer exchange | Claims boundaries |
| 7 | ABHA V3 API guide | Account and QR capabilities | Identity simulation |
| 8 | ABDM Scan and Share documentation | Provider QR workflow | Distinction from emergency card |
| 9 | HL7 FHIR R4 | Standard resources | FHIR bundles |
| 10 | Ayaz et al., FHIR review | Interoperability challenges | Limitations |
| 11 | Kapitan et al., open standards | Need usable implementations | Prototype rationale |
| 12 | Mandel et al., SMART on FHIR | Scoped authorization | Future authorization |
| 13 | Uzun and Bilgin, QR identity tag | Healthcare QR feasibility | Emergency entry |
| 14 | Vella et al., smartphone emergency ID | Underuse in injured care | Adoption caution |
| 15 | Bouri and Ravi, mobile PHR | Emergency mobile records | Connectivity risks |
| 16 | Faggiano et al., medical QR review | QR use cases | Scope comparison |
| 17 | Aljumah et al., emergency PHR access | Privacy-preserving emergency access | Cryptographic design |
| 18 | Jin et al., trauma data security | Data security risks | Governance |
| 19 | Shojaei et al., health IS security | Access control and auditing | Security gaps |
| 20 | Shamir, secret sharing | Threshold decryption | Future key management |
| 21 | Needham and Schroeder | Authenticated encryption | Integrity design |
| 22 | RFC 6749 OAuth 2.0 | Authorization framework | Future scopes |
| 23 | RFC 6455 WebSocket | Low-latency alerts | SOS transport |
| 24 | RFC 5321 SMTP | Asynchronous mail | Email fallback |
| 25 | NIST SP 800-63-4 | Digital identity guidance | Break-glass governance |

The project does not claim that these sources endorse the prototype. They provide standards, prior systems, and research context. The prototype's contribution is integration and reproducible evaluation, not a new cryptographic primitive or clinical study.

# CHAPTER 4: PROJECT PLAN

The project followed a waterfall-style plan adapted to a small team. Requirements were fixed first, then design, implementation, testing, and documentation. The phases below show the intended order and estimated effort.

Table: Project phase estimates

| Phase | Activities | Estimated effort |
| Requirements | Synopsis analysis, scope, non-goals | 1 week |
| Design | Architecture, data model, API contract | 1 week |
| Identity service | Auth, RBAC, consents | 1 week |
| Records service | Profiles, encryption, QR tokens | 1.5 weeks |
| ABDM and FHIR | Bundle builders, care contexts, trace | 1 week |
| NHCX service | Bills, claims, state machine | 1 week |
| SOS service | Alerts, WebSocket, SMTP | 0.5 week |
| Frontend | Patient, hospital, admin, scanner | 2 weeks |
| Integration | Seed data, end-to-end script | 0.5 week |
| Testing | Unit, integration, benchmark | 1 week |
| Documentation | Paper, report, deck | 1 week |

![Figure 4.1: Waterfall-style project plan](docs/report/figures/project_plan.png)

Figure 4.1 shows the waterfall sequence. Each phase produced a reviewable artifact before the next phase began. The plan allowed parallel work between backend and frontend once the API contract was stable.

# CHAPTER 5: SOFTWARE REQUIREMENT SPECIFICATION

## 5.1 Project Scope

The proposed work answers the following questions through an implemented prototype:

- How can a patient carry a readable emergency profile without exposing the full medical record?
- How can that profile be protected at rest and integrity-checked before decryption?
- How can hospital events become FHIR R4 resources?
- How can itemized bills become FHIR Claim resources with an auditable status path?
- How can emergency events reach hospital staff and contacts through complementary channels?

## 5.2 User Classes and Characteristics

Patient users own their emergency profile, generate QR tokens, view records and claims, and trigger SOS alerts. They need a simple interface and must not be required to authenticate during an emergency scan by a responder.

Hospital users view consented patient records, create prescriptions and diagnostics, create bills, submit claims, and monitor SOS alerts. They require role-based access and auditability.

Admin users inspect service health, ABDM integration traces, adjudicate claims, and audit SOS history. They do not receive direct emergency-profile control.

## 5.3 Functional Requirements

Table: Functional requirements

| ID | Requirement | Priority |
| FR-1 | Patient registration and login with JWT issuance | High |
| FR-2 | Patient emergency profile save and re-sealing | High |
| FR-3 | QR token creation and rotation | High |
| FR-4 | Public emergency token resolution | High |
| FR-5 | Hospital record creation | High |
| FR-6 | FHIR bundle conversion and care context | High |
| FR-7 | Itemized bill creation | Medium |
| FR-8 | FHIR Claim submission | Medium |
| FR-9 | Claim adjudication with state transitions | Medium |
| FR-10 | SOS alert creation and WebSocket broadcast | Medium |
| FR-11 | SMTP email fallback | Low |
| FR-12 | Admin integration trace and SOS audit | Medium |
| FR-13 | Consent-gated patient listing | High |

## 5.4 Non-Functional Requirements

Table: Non-functional requirements

| ID | Requirement | Target |
| NFR-1 | Emergency resolution under 800 ms in local test | Met |
| NFR-2 | Trauma profile encrypted at rest | Met |
| NFR-3 | Tampered profile rejected before decryption | Met |
| NFR-4 | Services independently testable | Met |
| NFR-5 | Reproducible seed data | Met |
| NFR-6 | Clear error responses | Met |
| NFR-7 | No live national gateway dependency | Met |

## 5.5 Data Model

Table: Data model summary

| Service | Table | Purpose |
| Identity | users | Accounts, roles, ABHA IDs |
| Identity | consent_artifacts | Patient-hospital consent grants |
| Records | patient_profiles | Emergency profile fields |
| Records | health_records | Clinical records |
| Records | trauma_profiles | Sealed emergency profile |
| Records | qr_tokens | Active and inactive QR tokens |
| ABDM | care_contexts | Record-to-patient linkage |
| ABDM | abdm_logs | Integration trace |
| NHCX | bills | Itemized bills |
| NHCX | claims | FHIR claims and status |
| SOS | alerts | SOS events and notification status |

# CHAPTER 6: SYSTEM DESIGN

## 6.1 Design Goals

The design follows six goals. Emergency information should be readable through a single QR scan without responder login. Trauma data should be encrypted and integrity-checked. Clinical events should be represented as FHIR R4 resources. Billing should be convertible into claim resources with an auditable status path. Critical events should reach hospital staff and contacts through complementary channels. Services should evolve independently.

## 6.2 Architecture

![Figure 6.1: Service ownership and data boundaries](docs/report/figures/service_ownership.png)

Figure 6.1 shows service ownership. The frontend is a single Next.js application with role-specific pages. The gateway isolates transport concerns. Each service owns exactly one bounded context and one database. No service writes another service's tables.

## 6.3 Security Controls

Table: Security controls and validation

| Control | Purpose | Validation |
| bcrypt password hashing | Prevent password retrieval | Identity tests passed |
| JWT and role claims | Authenticate and constrain API access | Identity and cross-service tests passed |
| AES-128-GCM | Confidentiality of emergency profile | Seal/unseal round trip passed |
| HMAC-SHA256 | Detect tampering before decryption | Tampered signature and ciphertext rejected |
| Rotating QR token | Limit replay of lost or leaked card | Old token returned inactive status |
| Consent artifacts | Gate hospital access to longitudinal data | Missing-consent access was not allowed in tested path |
| Internal token | Restrict service-to-service contact retrieval | Internal endpoint requires shared token |
| WebSocket authentication | Restrict hospital alert feed | Hospital or admin role required |

## 6.4 API Design

The API surface is organized by service. Public access is intentionally limited to health checks and emergency token resolution. All other operations require a bearer JWT. The endpoint map in Annexure A lists each route and its purpose. Error responses use JSON with a detail field and, where useful, a code field.

## 6.5 Deployment Design

The system supports three deployment modes: Docker Compose with five services, a single all-in-one container for hosts that provide one service and one volume, and local development through dev.sh. NGINX provides routing and rate limiting. SQLite keeps the prototype self-contained, while SQLAlchemy allows a future PostgreSQL migration.

# CHAPTER 7: IMPLEMENTATION

## 7.1 Technology Stack

Frontend: Next.js App Router, Tailwind CSS, TypeScript, Lucide icons.

Backend: FastAPI, SQLAlchemy, Pydantic, bcrypt, PyJWT, pycryptodome, httpx.

Gateway: NGINX.

Database: SQLite, one file per service.

Testing: pytest, vitest, httpx.

Deployment: Docker, Docker Compose, GitHub Actions, Render.

## 7.2 Backend Services

The identity service handles registration, login, RBAC, simulated eKYC, and consent artifacts. Passwords are bcrypt-hashed. JWTs expire after 24 hours. Consent artifacts store patient ID, hospital ID, scope, status, grant time, and expiry.

The records service manages patient profiles, health records, trauma profiles, and QR tokens. Trauma profiles store hexadecimal ciphertext-plus-tag, nonce, HMAC signature, and timestamp. QR tokens store a random 32-byte hexadecimal value and active status. Reading the current token does not rotate it; regeneration deactivates prior tokens.

The ABDM/FHIR service converts records into FHIR bundles, links care contexts, and records integration logs. The NHCX service creates itemized bills, converts them into FHIR Claim resources, and applies the adjudication state machine. The SOS service creates alerts, broadcasts over WebSocket, and attempts SMTP delivery.

## 7.3 Frontend

The patient page presents the health card, QR token, emergency profile editor, record timeline, consents, and claims. The hospital page adds scan-patient input, record writing, billing, claims, and a live SOS feed. The admin page exposes service health, ABDM integration traces, claim adjudication, and SOS audit information. The scanner page accepts a token from the QR link or manual entry and renders the resolved profile with an elapsed-time badge.

The frontend uses an editorial medical-journal theme with warm paper background, ink text, deep green accent, and clinical red reserved for emergency. It avoids generic SaaS styling.

## 7.4 Seed Data

The seed script creates demo accounts, patient profiles, health records, bills, claims, alerts, and integration traces. Demo accounts use the password abha1234. The seeded emergency card token is derived rather than random (see scripts/seed.py and services/records/records_app/demo.py) so that a printed card keeps working after a host restart. Records created through the interface are not retained on ephemeral free hosts.

## 7.5 Deployment

The repository includes Docker Compose for local and server deployment, a single-container image for hosts that provide one service, and GitHub Actions for CI and image publishing. Render hosts a free demo instance that sleeps after 15 minutes without a request and wakes in a measured 91 seconds. The application address remains valid while asleep, so a scanned card still resolves.

# CHAPTER 8: TESTING AND RESULTS

## 8.1 Test Strategy

The project uses three evaluation methods: automated service tests, a live end-to-end workflow, and a repeated emergency-token benchmark. Automated tests examine discrete controls. The live workflow verifies cross-service integration. The benchmark quantifies the server-side retrieval path under repeated in-process requests. No human-subject study, field deployment, or clinical-outcome evaluation was performed.

## 8.2 Unit and Integration Tests

The service test suites contain 24 tests across five services. All 24 pass. The distribution is 3 ABDM/FHIR tests, 4 identity tests, 3 NHCX tests, 11 records tests (4 cryptography tests and 7 emergency/QR/consent tests), and 3 SOS tests. The tests cover login and RBAC, emergency profile save and QR rotation, old-token invalidation, AES-GCM round trips, tampered-signature and tampered-ciphertext rejection, FHIR resource construction, ABDM trace behavior, NHCX state transitions, and SOS alert/WebSocket behavior.

Table: Unit and integration test inventory

| File | Tests | Focus |
| services/abdm/tests/test_abdm.py | 3 | FHIR bundles, care contexts, integration trace |
| services/identity/tests/test_identity.py | 4 | Login, RBAC, consent behavior |
| services/nhcx/tests/test_nhcx.py | 3 | Bill creation, claim submission, state transitions |
| services/records/tests/test_crypto.py | 4 | AES-GCM and HMAC verification |
| services/records/tests/test_records.py | 7 | Emergency profile, QR rotation, consent |
| services/sos/tests/test_sos.py | 3 | Alert creation, WebSocket, email fallback |

## 8.3 End-to-End Workflow

The live workflow completes all 18 steps. It checks five service health endpoints, patient, hospital, and admin logins, consented record listing, emergency card read without rotation, emergency resolution, hospital record creation, FHIR conversion with care context, bill creation, claim submission, claim adjudication, SOS dispatch, and ABDM trace retrieval. The emergency resolution reported 0 ms by the service's integer timer, and the workflow asserts success below the 800-ms design threshold.

Table: End-to-end workflow steps

| Step | Result |
| health/identity | Pass |
| health/records | Pass |
| health/abdm | Pass |
| health/nhcx | Pass |
| health/sos | Pass |
| login patient | Pass |
| login hospital | Pass |
| hospital lists patient records (consent ok) | Pass |
| emergency card read does not rotate | Pass |
| emergency card token is stable | Pass |
| emergency resolve < 800 ms | Pass |
| hospital creates record | Pass |
| FHIR conversion + care context | Pass |
| bill created | Pass |
| claim submitted to NHCX | Pass |
| claim adjudicated | Pass |
| SOS alert dispatched | Pass |
| ABDM integration trace | Pass |

## 8.4 Emergency Retrieval Benchmark

A benchmark of 1,000 measured requests was executed after 50 warmup requests against an isolated temporary records database. The measured wall time is the time from request dispatch to completed response inside the TestClient process. The service reports elapsed time as an integer, so many high-speed local calls round to 0 ms. Wall-time statistics provide finer resolution.

Table: Benchmark results

| Metric | Value |
| Warmup requests | 50 |
| Measured requests | 1,000 |
| HTTP status distribution | 1,000 x HTTP 200 |
| Minimum wall time | 0.612 ms |
| Median wall time | 0.644 ms |
| Mean wall time | 0.661 ms |
| 95th percentile wall time | 0.743 ms |
| Maximum wall time | 1.908 ms |
| Service-reported median | 0 ms |

The measured quantity is local and excludes QR acquisition, TLS, networking, browser rendering, and user interpretation.

## 8.5 Security Validation

The cryptographic tests first verified that sealing and unsealing recover the original profile. Then they altered the HMAC signature and separately flipped a ciphertext byte. Both tampered inputs were rejected without returning profile data. A further test confirmed that the stored signature equals the HMAC of the ciphertext-plus-tag data. Identity tests confirmed that missing or invalid bearer tokens fail and that login checks role claims. Consent tests confirmed that a hospital cannot list a patient's records in the tested missing-consent path. The QR rotation test confirmed that an old token returned HTTP 410 after a new token was issued.

## 8.6 Limitations of Evaluation

The benchmark is not representative of field conditions. QR scanning, device startup, TLS handshake, network loss, and human reaction dominate an emergency response. The TestClient also bypasses NGINX, so the benchmark isolates service logic rather than gateway latency. SQLite differs from PostgreSQL in concurrency behavior. The state-machine decision uses a local threshold and should not be read as a payer policy. Tests use deterministic synthetic users and profiles. They do not establish usability, clinician comprehension, or clinical safety.

# CHAPTER 9: CONCLUSION AND FUTURE WORK

The project demonstrates that an ABHA-linked emergency health card can combine secure emergency retrieval, FHIR R4 interoperability, claims synchronization, and emergency notification in one microservice system. The paper reported 19 service tests and a 16-step workflow at the time of submission; the repository now contains 24 service tests and an 18-step workflow, all passing. In a 1,000-request local benchmark, emergency-token retrieval had a median wall time of 0.644 ms and a 95th-percentile wall time of 0.743 ms. The work demonstrates technical feasibility and reproducible integration, while explicitly excluding clinical effectiveness, live national-gateway certification, offline NFC capability, and production deployment.

The principal contribution is the tested integration framework and the evaluation boundaries needed before such a system can move toward real emergency and payer workflows. Future work should address offline NFC or partially cached profiles with explicit staleness indicators, real ABDM FHIR implementation guide and NHCX conformance testing, managed key rotation and threshold-based recovery, responder identity and access logging, degraded-network tests, alert reliability tests, and prospective usability studies with emergency clinicians and representative patients.

Table: Implemented scope versus original synopsis

| Original synopsis item | Status | Notes |
| Emergency QR profile | Implemented | Backend-resolved token, encrypted profile |
| FHIR interoperability | Implemented | MedicationRequest and DiagnosticReport bundles |
| NHCX claims synchronization | Implemented locally | Simulated adjudication |
| SOS notification | Implemented | WebSocket plus SMTP fallback |
| Physical NFC storage | Not implemented | Future work |
| Complete offline decryption | Not implemented | Future work |
| SMS delivery | Not implemented | Email only |
| Live ABDM/NHCX integration | Not implemented | Local simulation |

# BIBLIOGRAPHY

[1] R. S. Sharma, A. Rohatgi, S. Jain, and D. Singh, "The Ayushman Bharat Digital Mission (ABDM): making of India's Digital Health Story," CSI Transactions on ICT, vol. 11, no. 1, pp. 3-9, 2023.

[2] U. S. Mishra, S. Yadav, and W. Joe, "The Ayushman Bharat Digital Mission of India: An assessment," Health Systems & Reform, vol. 10, no. 2, article 2392290, 2024.

[3] M. Mantri, G. Sunder, S. Kadam, and A. Abhyankar, "A perspective on digital health platform design and its implementation at national level," Frontiers in Digital Health, vol. 6, article 1260855, 2024.

[4] National Resource Center for EHR Standards, FHIR Implementation Guide for ABDM, version 6.5.0, May 2025. [Online]. Available: https://www.nrces.in/ndhm/fhir/r4/index.html

[5] National Health Authority, NHCX Developer Documentation: Claim Settlement, version 1, updated Oct. 2026. [Online]. Available: https://docs.abdm.gov.in/docs/nhcx/v1

[6] National Health Authority, NHCX Implementation Guide for Payers, 2026-27. [Online]. Available: https://abdm.gov.in/strapicms/uploads/NHCX_Implementation_Guide_for_Payers_2026_1_66f3fbcee1.pdf

[7] National Health Authority, Integrator Guide ABDM ABHA V3 APIs, version 1.2, Oct. 2024. [Online]. Available: https://sandboxcms.abdm.gov.in/uploads/ABDM_ABHA_V3_AP_Is_SOP_V1_1_4_faef8099bd.pdf

[8] National Health Authority, Sandbox Documentation: ABDM Scan and Share, version 1.0, Aug. 2024. [Online]. Available: https://sandboxcms.abdm.gov.in/uploads/Scan_and_share_Document_Updated_1_0_22_Aug_2024_c1b570cbf6.pdf

[9] Health Level Seven International, HL7 FHIR Release 4, version 4.0.1, 2019. [Online]. Available: https://hl7.org/fhir/R4/

[10] M. Ayaz, M. F. Pasha, M. Y. Alzahrani, R. Budiarto, and D. Stiawan, "The Fast Healthcare Interoperability Resources (FHIR) standard: Systematic literature review of implementations, applications, challenges and opportunities," JMIR Medical Informatics, vol. 9, no. 7, article e21929, 2021.

[11] D. Kapitan, F. Heddema, A. Dekker, M. Sieswerda, B.-J. Verhoeff, and M. Berg, "Data interoperability in context: The importance of open-source implementations when choosing open standards," Journal of Medical Internet Research, vol. 27, article e66616, 2025.

[12] J. C. Mandel, D. A. Kreda, K. D. Mandl, I. S. Kohane, and R. B. Ramoni, "SMART on FHIR: A standards-based, interoperable apps platform for electronic health records," Journal of the American Medical Informatics Association, vol. 23, no. 5, pp. 899-908, 2016.

[13] V. Uzun and S. Bilgin, "Evaluation and implementation of QR Code Identity Tag system for Healthcare in Turkey," SpringerPlus, vol. 5, no. 1, article 1454, 2016.

[14] M. A. Vella, H. Li, P. M. Reilly, and S. S. Raza, "Unlocked yet untapped: The ubiquitous smartphone and utilization of emergency medical identification technology in the care of the injured patient," Surgery Open Science, vol. 2, no. 3, pp. 122-126, 2020.

[15] N. Bouri and S. Ravi, "Going mobile: How mobile personal health records can improve health care during emergencies," JMIR mHealth and uHealth, vol. 2, no. 1, article e8, 2014.

[16] A. Faggiano, F. Fioretti, S. Nodari, and S. Carugo, "Quick response code applications in medical and cardiology settings: A systematic scoping review," European Heart Journal - Digital Health, vol. 2, no. 2, pp. 336-341, 2021.

[17] F. Aljumah, R. H. M. Leung, M. Pourzandi, and M. Debbabi, "Emergency mobile access to personal health records stored on an untrusted cloud," in Health Information Science, Lecture Notes in Computer Science, vol. 7798, Berlin, Germany: Springer, 2013, pp. 30-41.

[18] F. Jin, B. Wang, X. Liao, K. Wang, W. Huang, and T. Wang, "Exploring data security risks associated with trauma medical data within hospitals in China: A qualitative study," BMJ Open, vol. 15, no. 2, article e085221, 2025.

[19] P. Shojaei, E. Vlahu-Gjorgievska, and Y.-W. Chow, "Security and privacy of technologies in health information systems: A systematic literature review," Computers, vol. 13, no. 2, article 41, 2024.

[20] A. Shamir, "How to share a secret," Communications of the ACM, vol. 22, no. 11, pp. 612-613, 1979.

[21] R. M. Needham and M. D. Schroeder, "Using encryption for authentication in large networks of computers," Communications of the ACM, vol. 21, no. 12, pp. 993-999, 1978.

[22] D. Hardt, Ed., "The OAuth 2.0 Authorization Framework," RFC 6749, Internet Engineering Task Force, Oct. 2012. [Online]. Available: https://www.rfc-editor.org/info/rfc6749/

[23] I. Fette and A. Melnikov, "The WebSocket Protocol," RFC 6455, Internet Engineering Task Force, Dec. 2011. [Online]. Available: https://www.rfc-editor.org/info/rfc6455/

[24] J. Klensin, "Simple Mail Transfer Protocol," RFC 5321, Internet Engineering Task Force, Oct. 2008. [Online]. Available: https://www.rfc-editor.org/info/rfc5321/

[25] D. Temoshok, D. Proud-Madruga, Y.-Y. Choong, R. Galluzzo, S. Gupta, C. LaSalle, N. Lefkovitz, and A. Regenscheid, Digital Identity Guidelines, NIST Special Publication 800-63-4, Aug. 2025.

# ANNEXURE A: ENDPOINT MAP

Table: Endpoint map

| Area | Endpoint | Purpose |
| Identity | POST /login | Obtain bearer JWT and role |
| Identity | GET /patients | List consent-visible patients |
| Records | PUT /emergency/profile | Save and re-seal trauma profile |
| Records | POST /emergency/qr | Create new QR token |
| Records | GET /emergency/qr | Read current QR token without rotation |
| Records | GET /emergency/resolve/{token} | Resolve emergency profile publicly |
| Records | POST /records | Add clinical record |
| Records | GET /records | List records with consent check |
| ABDM/FHIR | POST /fhir/convert | Convert record and link care context |
| ABDM/FHIR | GET /logs | Retrieve integration trace |
| NHCX | POST /bills | Create itemized bill |
| NHCX | POST /claims | Submit FHIR Claim |
| NHCX | POST /claims/{id}/adjudicate | Apply state transition |
| SOS | POST /alerts | Create GPS-tagged alert |
| SOS | GET /alerts/ws | Receive hospital alert stream |

# ANNEXURE B: DATA DICTIONARY

Table: Data dictionary

| Table | Column | Type | Description |
| users | id | integer | Primary key |
| users | name | string | Display name |
| users | email | string | Unique login email |
| users | password_hash | string | bcrypt hash |
| users | role | string | patient, hospital, or admin |
| users | abha_id | string | 14-digit ABHA identifier |
| users | phone | string | Contact number |
| users | hospital_name | string | Hospital display name |
| consent_artifacts | id | integer | Primary key |
| consent_artifacts | patient_id | integer | Patient user id |
| consent_artifacts | hospital_id | integer | Hospital user id |
| consent_artifacts | scope | string | Granted scope |
| consent_artifacts | status | string | ACTIVE or REVOKED |
| consent_artifacts | granted_at | datetime | Grant timestamp |
| consent_artifacts | expires_at | datetime | Optional expiry |
| patient_profiles | id | integer | Primary key |
| patient_profiles | user_id | integer | Patient user id |
| patient_profiles | blood_group | string | ABO/Rh group |
| patient_profiles | allergies | text | JSON list |
| patient_profiles | chronic_conditions | text | JSON list |
| patient_profiles | medications | text | JSON list |
| patient_profiles | emergency_contacts | text | JSON list |
| health_records | id | integer | Primary key |
| health_records | patient_id | integer | Patient user id |
| health_records | type | string | Prescription, DiagnosticReport, Immunization |
| health_records | title | string | Record title |
| health_records | fhir_json | text | FHIR bundle |
| health_records | created_by | integer | Hospital user id |
| trauma_profiles | id | integer | Primary key |
| trauma_profiles | patient_id | integer | Patient user id |
| trauma_profiles | encrypted_blob | text | Hex ciphertext plus tag |
| trauma_profiles | nonce | string | Hex nonce |
| trauma_profiles | hmac_sha256 | string | Signature |
| qr_tokens | id | integer | Primary key |
| qr_tokens | patient_id | integer | Patient user id |
| qr_tokens | token | string | Random 32-byte hex |
| qr_tokens | active | boolean | Current card status |
| care_contexts | id | integer | Primary key |
| care_contexts | patient_id | integer | Patient user id |
| care_contexts | record_ref | string | Linked record |
| care_contexts | status | string | LINKED, CONSENT_PENDING, ACTIVE |
| abdm_logs | id | integer | Primary key |
| abdm_logs | ts | datetime | Event timestamp |
| abdm_logs | direction | string | OUT or IN |
| abdm_logs | endpoint | string | Simulated endpoint |
| abdm_logs | status_code | integer | HTTP status |
| abdm_logs | latency_ms | integer | Measured latency |
| bills | id | integer | Primary key |
| bills | hospital_id | integer | Hospital user id |
| bills | patient_id | integer | Patient user id |
| bills | line_items | text | JSON list |
| bills | total | number | Bill total |
| claims | id | integer | Primary key |
| claims | bill_id | integer | Source bill |
| claims | fhir_claim_json | text | FHIR Claim |
| claims | status | string | SUBMITTED, ADJUDICATED, APPROVED, REJECTED |
| claims | insurer_note | string | Adjudication note |
| claims | out_of_pocket | number | Estimated patient share |
| alerts | id | integer | Primary key |
| alerts | patient_id | integer | Patient user id |
| alerts | trigger | string | PANIC or QR_SCAN |
| alerts | lat | number | Latitude |
| alerts | lng | number | Longitude |
| alerts | email_status | string | Sent, failed, or skipped |

# ANNEXURE C: DEPLOYMENT AND REPRODUCTION

The project can be run in three ways.

Local development:

1. Create a Python 3.13 virtual environment and install requirements.txt.
2. Run scripts/seed.py to create and seed the five databases.
3. Run dev.sh to start the five services on ports 8001 to 8005.
4. Run the frontend with npm install and npm run dev.
5. Run pytest for backend tests and npm test for frontend tests.

Docker Compose:

1. Run docker compose up --build.
2. Open the gateway at http://localhost.
3. Use demo accounts with password abha1234.

Single container:

1. Build deploy/allinone/Dockerfile.
2. Run with a volume mounted at /data.
3. Open http://localhost:8080.

The smoke test can be pointed at any deployment by setting E2E_BASE.

# ANNEXURE D: USER MANUAL

Patient:

1. Sign in with a patient account.
2. Open My Card to view the ABHA id, blood group, allergy badges, emergency contacts, and QR code.
3. Edit the emergency profile. It is re-sealed with AES-128-GCM and the change appears on the next scan.
4. Press Regenerate card to issue a new token and invalidate the old one.
5. Press Panic to send an alert to hospital dashboards and contacts.

Hospital:

1. Sign in with a hospital account.
2. Open Scan Patient and scan the card or paste the token.
3. Create a prescription or diagnostic record for a consented patient.
4. Create an itemized bill and push it to NHCX.
5. Monitor the SOS feed for live alerts.

Admin:

1. Sign in with an admin account.
2. Inspect service health and ABDM integration traces.
3. Adjudicate pending claims.
4. Audit SOS history.

# ANNEXURE E: TEST CASES

Table: Test case summary

| ID | Test | Expected result |
| TC-1 | Patient login with valid credentials | JWT with patient role returned |
| TC-2 | Patient login with invalid password | Authentication failure |
| TC-3 | Hospital lists records without consent | Access denied |
| TC-4 | Save emergency profile | Profile sealed and stored |
| TC-5 | Read current QR token | Token returned without rotation |
| TC-6 | Regenerate QR token | New token returned, old token inactive |
| TC-7 | Resolve active token | Minimum profile returned |
| TC-8 | Resolve replaced token | HTTP 410 |
| TC-9 | Tamper HMAC signature | Rejection before decryption |
| TC-10 | Tamper ciphertext byte | AES-GCM verification failure |
| TC-11 | Create FHIR MedicationRequest | Valid Bundle returned |
| TC-12 | Submit bill as claim | Claim status SUBMITTED |
| TC-13 | Adjudicate valid claim | Status APPROVED or REJECTED |
| TC-14 | Invalid claim transition | Error raised |
| TC-15 | Create SOS alert | Alert stored and broadcast |
| TC-16 | Email without SMTP config | Status SKIPPED |
| TC-17 | Frontend QR helper tests | 17 tests pass |
| TC-18 | End-to-end smoke test | 18 steps pass |

# APPENDIX A: DETAILED SYSTEM ARCHITECTURE

## 10.1 Component Responsibilities

The frontend is a single Next.js application that renders patient, hospital, admin, and public scanner areas. It stores the JWT in memory and localStorage, attaches it to API requests, and renders role-specific dashboards. The public scanner does not require authentication, but it only receives the minimum emergency profile from the records service.

The NGINX gateway routes all traffic under /api to the correct service. It applies rate limiting and can return a 503 page if a downstream service is unavailable. The gateway does not authorize requests; each service checks role claims itself. This defense-in-depth design means a service remains protected even when called directly.

The identity service owns user accounts, password hashes, roles, ABHA identifiers, and consent artifacts. It issues JWTs with a 24-hour expiry and validates bcrypt passwords. The records service owns patient profiles, health records, sealed trauma profiles, and QR tokens. It is the only service that reads or writes trauma data. The ABDM/FHIR service owns care contexts and integration logs. The NHCX service owns bills, FHIR claims, status, insurer notes, and out-of-pocket values. The SOS service owns alerts, GPS tags, notified contacts, email status, WebSocket connections, and alert history.

## 10.2 Request Flow

A typical patient login request travels from the browser to the gateway, then to the identity service. The service validates credentials, checks the bcrypt hash, and returns a JWT. The frontend stores the token and uses it for later requests. A hospital record request travels through the gateway to the records service, which checks the JWT role and consent artifact before returning data. An emergency scan travels directly from the scanner to the public resolve endpoint, which does not require a JWT but does require an active token.

Internal service calls use HTTP and a shared token. For example, the SOS service calls the records service to fetch emergency contacts for an alert. The records service checks the shared token before returning contact data. This keeps service-to-service access narrow and auditable.

## 10.3 Data Ownership

Each database owns one bounded context. There are no cross-service table writes. Services communicate through HTTP APIs, which makes ownership explicit and testing simpler. SQLite provides a self-contained demo, while SQLAlchemy allows a future PostgreSQL migration with configuration changes. The data model stores JSON lists and FHIR JSON as text fields, which is appropriate for a prototype but should be normalized or moved to a document-capable database for production scale.

## 10.4 Error Handling

Every API error returns a JSON object with a detail field. The frontend shows inline banners styled to the theme. The gateway returns a human-readable 503 page if a downstream service is down. SOS email failure is logged and surfaced as EMAIL_FAILED or EMAIL_SKIPPED without blocking the alert. WebSocket reconnection uses backoff. These choices keep failures visible rather than hiding them behind generic messages.

## 10.5 Configuration

The application uses environment variables for secrets and SMTP settings. JWT_SECRET and SHARED_TOKEN must be changed before any deployment reachable by other people. SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, and SOS_FROM_EMAIL enable real email. Without SMTP settings, the alert still fires over WebSocket and the email status reads SKIPPED. The demo does not depend on a mail server.

# APPENDIX B: SECURITY AND PRIVACY ANALYSIS

## 11.1 Threat Model

The prototype assumes that the database may be readable by an attacker, the QR token may be leaked, and the network may be observed. It does not assume a malicious hospital user with valid credentials, although consent checks reduce that risk. It also does not address physical device theft, browser malware, or social engineering.

## 11.2 Confidentiality

Trauma profiles are sealed with AES-128-GCM before storage. The ciphertext and tag are stored as hexadecimal text. The nonce is stored separately. A passive observer cannot read the trauma profile from stored ciphertext. The QR code contains only an opaque token, not patient data. Longitudinal records and claims require authentication and consent.

## 11.3 Integrity

HMAC-SHA256 is calculated over the ciphertext and tag. On retrieval, the service verifies HMAC before attempting AES-GCM decryption. This ensures that modified ciphertext or an invalid signature does not proceed to decryption. The tests alter the signature and flip a ciphertext byte; both tampered inputs are rejected without returning profile data.

## 11.4 Authentication and Authorization

Passwords are hashed with bcrypt. JWTs carry subject, role, ABHA identifier, and expiry. Every service validates bearer tokens independently. Role claims constrain access to patient, hospital, or admin functions. Consent artifacts gate hospital access to patient records. Revoking a consent artifact takes effect on the next request, and the hospital loses the patient from its list.

## 11.5 Token Lifecycle

QR tokens are random 32-byte hexadecimal values. Reading the current token does not rotate it, so printed cards remain valid. Regeneration deactivates prior tokens. An old token returns HTTP 410 after replacement. This limits the lifetime of a leaked token but does not provide full misuse detection. Production use would need rate limits, audit records, anomalous scan detection, and user notification.

## 11.6 Key Management

The trauma key is configured from an environment variable for the prototype. Production deployment requires managed key storage, rotation, separation of duties, cryptographic agility, and recovery procedures. Threshold schemes could distribute emergency decryption capability, but they introduce participant selection, reconstruction delay, revocation, and audit challenges that must be engineered rather than assumed.

## 11.7 Privacy and Minimum Disclosure

The public emergency endpoint returns only blood group, allergies, chronic conditions, medications, emergency contacts, name, and ABHA identifier. It does not return longitudinal records, bills, claims, or administrative data. This minimum disclosure reduces exposure but still requires break-glass governance for real deployment.

## 11.8 Governance Gaps

Encryption protects confidentiality but does not answer who may scan, when, why, or what happens afterward. Emergency QR access requires explicit break-glass rules, actor accountability, minimum-data justification, expiry, post-access review, and misuse handling. The current public endpoint records token active state but does not require responder identification or dual-control authorization.

# APPENDIX C: RISK REGISTER

Table: Risk register

| ID | Risk | Impact | Mitigation |
| R-1 | QR token leaked | Unauthorized emergency profile access | Token rotation and minimum disclosure |
| R-2 | SMTP unavailable | Contact notification delayed | WebSocket path remains active |
| R-3 | Free host sleep | Slow first response | Documented wake time and stable URL |
| R-4 | SQLite concurrency | Limited under load | SQLAlchemy allows PostgreSQL migration |
| R-5 | Simulated gateways | No national certification | Clearly disclosed as local simulation |
| R-6 | Demo key in environment | Weak key management | Production key vault required |
| R-7 | No clinical validation | Unknown usability | Future clinician study |
| R-8 | Public token enumeration | Privacy risk | Random 32-byte tokens and active checks |

# ANNEXURE F: GLOSSARY

ABDM: Ayushman Bharat Digital Mission.

ABHA: Ayushman Bharat Health Account.

AES-GCM: Advanced Encryption Standard in Galois/Counter Mode.

FHIR: Fast Healthcare Interoperability Resources.

HMAC: Hash-based Message Authentication Code.

JWT: JSON Web Token.

NHCX: National Health Claims Exchange.

RBAC: Role-Based Access Control.

SMTP: Simple Mail Transfer Protocol.

WebSocket: Persistent bidirectional communication protocol.

# ANNEXURE G: CODE AND CONFIGURATION NOTES

## G.1 Backend Entry Points

Each service has its own FastAPI application and database. The service entry points are identity_app.main, records_app.main, abdm_app.main, nhcx_app.main, and sos_app.main. The shared package provides database, security, and configuration helpers.

## G.2 Frontend Routes

The frontend uses the Next.js App Router. Key routes are /, /login, /register, /patient, /hospital, /admin, and /scan. The scanner route is public. Other routes require authentication.

## G.3 Gateway Routes

NGINX routes /api/identity, /api/records, /api/abdm, /api/nhcx, and /api/sos to the respective services. It applies rate limiting and CORS handling. The gateway does not authorize requests.

## G.4 Seed Routine

scripts/seed.py orchestrates per-service seed routines. It creates accounts, profiles, records, bills, claims, alerts, and integration traces. The seed is idempotent for container restarts.

# ANNEXURE H: SCREEN AND WORKFLOW DESCRIPTIONS

## H.1 Patient Flow

1. Sign in with a patient account.
2. Open My Card to view ABHA id, blood group, allergy badges, emergency contacts, and QR code.
3. Edit the emergency profile. The profile is re-sealed with AES-128-GCM.
4. Regenerate the card to issue a new token and invalidate the old one.
5. Press Panic to send an alert to hospital dashboards and contacts.

## H.2 Hospital Flow

1. Sign in with a hospital account.
2. Open Scan Patient and scan the card or paste the token.
3. Create a prescription or diagnostic record for a consented patient.
4. Create an itemized bill and push it to NHCX.
5. Monitor the SOS feed for live alerts.

## H.3 Admin Flow

1. Sign in with an admin account.
2. Inspect service health and ABDM integration traces.
3. Adjudicate pending claims.
4. Audit SOS history.

# ANNEXURE I: DETAILED TEST NOTES

The backend test suite uses pytest with isolated temporary databases. Each service test file covers a distinct area. The records cryptography tests verify seal and unseal round trips, HMAC equality, and tamper rejection. The records emergency tests verify profile save, QR rotation, old-token invalidation, and consent checks. The identity tests verify login, RBAC, and consent behavior. The ABDM tests verify FHIR bundle shape and integration trace. The NHCX tests verify bill creation, claim submission, and state transitions. The SOS tests verify alert creation, WebSocket broadcast, and email fallback.

The frontend test suite uses vitest and covers QR token helpers, camera component behavior, quiet-zone rendering, and decoding. It also covers a browser that stops handing out animation frames. These tests protect the scan path but do not constitute end-to-end browser automation.

# ANNEXURE J: FUTURE WORK

Future work should address the following items:

1. Physical NFC or partially cached offline profiles with explicit staleness indicators.
2. Real ABDM FHIR implementation guide and NHCX conformance testing against current versions.
3. Managed key rotation and threshold-based recovery.
4. Responder identity, access logging, and post-event review.
5. Simulated degraded-network tests, including stale profiles, replay, and partial disclosure.
6. Alert reliability tests with reconnect and acknowledgement escalation.
7. Prospective usability studies with emergency clinicians and representative patients.
8. Production database migration and multi-node deployment.
9. External security audit and key management review.

# APPENDIX D: DETAILED LITERATURE REVIEW

## 13.1 ABDM and National Digital Health Infrastructure

India's Ayushman Bharat Digital Mission aims to create a national digital health ecosystem that connects patients, healthcare providers, and payers through standardized identifiers and consent-aware workflows. The mission introduces ABHA as a health account identifier, registries for facilities and professionals, consent managers, and health information exchanges. Research on ABDM emphasizes that technical infrastructure alone does not create value unless providers and patients use it in daily workflows. This project uses ABDM concepts as design context but does not call live registries or sandboxes.

The ABDM FHIR implementation guide provides resource profiles and conventions for clinical data exchange. It is relevant because the prototype maps prescriptions and diagnostics to FHIR R4 resources. The project uses MedicationRequest and DiagnosticReport shapes as a starting point, while acknowledging that production conformance requires deeper profile validation and terminology binding.

ABHA V3 APIs define account creation, session handling, and QR-related capabilities. The prototype simulates these capabilities through a 14-digit ABHA identifier and JWT-based session tokens. It does not implement OTP verification or live account linking. This boundary is important because the emergency flow must work even when national services are unavailable.

ABDM Scan and Share is a provider-oriented QR workflow for demographic sharing and registration. It is not a patient-carried emergency trauma card. The distinction matters because the present prototype uses a rotating token to expose a minimum emergency profile and keeps full records behind authenticated and consent-checked APIs.

## 13.2 FHIR and Clinical Interoperability

FHIR R4 defines resources such as Patient, DiagnosticReport, MedicationRequest, and Claim, along with security and consent guidance. It is widely used for interoperability because it combines RESTful APIs with extensible data models. A systematic review of FHIR implementations finds continued challenges in semantic consistency, migration, and context-specific adaptation. Open standards need usable implementations and adaptation to local workflows.

The prototype uses FHIR as a serialization format for clinical and claim data. It builds bundle structures in Python and stores them as JSON. This approach makes the data inspectable and testable. It does not implement terminology servers, profile validation, or conformance testing. Those are future requirements for production integration.

SMART on FHIR combines FHIR APIs with OAuth-style authorization to enable substitutable applications. The prototype uses bearer JWTs and role claims instead of the full SMART authorization stack. This simplification is acceptable for a prototype but should be revisited for production. Future work should evaluate SMART-style scopes and consent-aware authorization.

## 13.3 NHCX and Claims Interoperability

NHCX documentation specifies a provider-payer claim exchange using standardized FHIR-based transactions, protected message handling, asynchronous receipts, and callback-based status updates. The prototype does not connect to NHCX endpoints. Instead, it mirrors the principal clinical-to-claim path by converting bills to FHIR Claim resources and enforcing explicit state transitions inside its own NHCX Claims Hub service.

The local state machine verifies workflow sequencing but not message security, webhook semantics, idempotency, or certificate trust. Those require future sandbox conformance testing. The demo policy approves claims under a configurable threshold and rejects high-value claims. This policy is illustrative and not an insurance rule, actuarial policy, or NHCX adjudication.

## 13.4 Emergency Health Cards and QR Access

QR tags have been proposed and implemented as medical identity carriers. A QR Code Identity Tag system for healthcare demonstrates feasibility for quick identification. Smartphone-based emergency medical identification is available but underused in injured-patient care, indicating that technical presence does not guarantee adoption. Mobile personal health records in emergencies offer potential benefits alongside power, connectivity, usability, and data-availability risks.

A systematic scoping review of medical QR applications shows that emergency identification is only one use case, with many applications oriented toward education, monitoring, and routine workflows. These studies support using a QR link as an entry point, but they do not justify placing a complete medical profile in plaintext inside the QR code. The present design encodes an opaque token and keeps profile fields encrypted in the backend.

## 13.5 Security and Notification Architecture

Health-system security research repeatedly identifies access control, secure storage, auditing, and human factors as persistent challenges. Emergency access is especially difficult because the patient may not participate in authorization. Research on emergency access to encrypted personal health records hosted on untrusted infrastructure highlights privacy-preserving mechanisms for scenarios in which the patient cannot authenticate.

Shamir's threshold-sharing construction provides a theoretical basis for distributing emergency decryption authority among multiple parties, but it does not by itself resolve key rotation, revocation, recovery, or accountability. The prototype applies AES-128-GCM and HMAC-SHA256 but leaves threshold key management as future work.

RFC 6455 defines persistent bidirectional WebSocket communication, which can be used for low-latency dashboard alerts. It must be secured and tested for reconnect and ordering behavior. SMTP defines asynchronous mail transport and store-and-forward behavior. It is a useful fallback but not a guaranteed immediate alert channel. NIST digital-identity guidance supports risk-based decisions about authenticators, federation, and lifecycle assurance, and is relevant to future emergency-actor identity design.

# APPENDIX E: DETAILED IMPLEMENTATION NOTES

## 14.1 Identity Service

The identity service implements registration, login, role-based access control, simulated eKYC, and consent management. Passwords are hashed with bcrypt. Login returns a JWT containing subject, role, ABHA identifier, and expiry. The service stores users in a dedicated SQLite database. Consent artifacts connect patient and hospital identities with scope, grant time, expiry, and status.

The service validates JWTs issued by itself and other services. It checks role claims before allowing operations. A hospital can list only patients with active consent grants. This keeps patient data access explicit and auditable.

## 14.2 Records Service

The records service is the core of the emergency flow. It manages patient profiles, health records, trauma profiles, and QR tokens. Patient profiles store blood group, allergies, chronic conditions, medications, and emergency contacts as JSON fields. Health records store FHIR JSON and metadata. Trauma profiles store sealed data. QR tokens store random values and active status.

The seal function uses AES-128-GCM with a fresh 12-byte nonce. It stores ciphertext concatenated with the 16-byte authentication tag. The HMAC function signs the combined data. The unseal function verifies HMAC before decryption. This order prevents decryption of tampered data.

The QR token read endpoint returns the current token without rotation. The regeneration endpoint deactivates old tokens and creates a new one. The public resolve endpoint checks token existence and active status, verifies HMAC, decrypts AES-GCM, and returns the minimum profile with a server-measured elapsed time.

## 14.3 ABDM and FHIR Service

The ABDM/FHIR service converts hospital records into FHIR bundles. It maps prescriptions to MedicationRequest-oriented bundles and diagnostics to DiagnosticReport-oriented bundles. It links care contexts to patients and records integration traces. Each trace entry includes timestamp, direction, endpoint, payload snippet, status, and latency.

The service simulates gateway interactions without calling national services. This allows the workflow to be tested and demonstrated without external dependencies. The trace log supports auditability but is not equivalent to a national-gateway audit log.

## 14.4 NHCX Service

The NHCX service creates itemized bills and FHIR Claim resources. It enforces the claim state machine and computes out-of-pocket estimates. The adjudication endpoint applies the transition and records insurer notes. Invalid transitions raise errors. The demo policy uses a threshold to decide approval or rejection.

The service stores bills and claims in a dedicated database. It does not call real NHCX endpoints. This boundary is clearly documented and tested.

## 14.5 SOS Service

The SOS service creates alerts with GPS tags and trigger types. It broadcasts alerts over WebSocket to connected hospital dashboards and attempts SMTP email delivery to registered contacts. It fetches emergency contacts through an internal endpoint on the records service. The email status is recorded as sent, failed, or skipped.

The service requires hospital or admin role for WebSocket connections. This prevents unauthorized access to the alert feed. The WebSocket path is fast, while email is a fallback. SMTP failures do not block the alert.

# APPENDIX F: DETAILED TESTING AND QUALITY ASSURANCE

## 15.1 Test Environment

The tests run on macOS with Python 3.13. Each service uses an isolated temporary database. The frontend tests run with vitest in a jsdom environment. The end-to-end script requires running services on ports 8001 to 8005. The benchmark uses the FastAPI TestClient and an isolated records database.

## 15.2 Backend Test Coverage

The backend tests cover authentication, authorization, consent, encryption, emergency resolution, QR rotation, FHIR conversion, claim transitions, and alert dispatch. They do not cover load testing, browser automation, or production deployment. The test count is 24, and all pass.

## 15.3 Frontend Test Coverage

The frontend tests cover QR token helpers, camera component behavior, quiet-zone rendering, and decoding. They also cover a browser that stops handing out animation frames. These tests protect the scan path but do not constitute end-to-end browser automation.

## 15.4 Benchmark Method

The benchmark uses 50 warmup requests and 1,000 measured requests. It measures wall time from request dispatch to completed response inside the TestClient process. It does not include QR capture, TLS, network transit, or browser rendering. The service reports elapsed time as an integer, so wall time provides finer resolution.

## 15.5 Quality Gates

The project includes quality gates for document integrity, citation resolution, test passage, and build success. The paper build script generates a DOCX and reports citation coverage. The originality check scans for overlap with the synopsis and template. These checks support reproducibility but do not claim external plagiarism scores.

# APPENDIX G: DEPLOYMENT AND OPERATIONS

## 16.1 Local Development

Local development uses a Python virtual environment, per-service databases, and dev.sh. The script seeds databases if missing and starts five uvicorn processes. The frontend runs separately with npm. This mode is suitable for development and testing.

## 16.2 Docker Compose

Docker Compose builds and runs the five services, gateway, and frontend. It creates a seed service on first boot. The compose file defines health checks and dependency ordering. This mode is suitable for demos and small deployments.

## 16.3 Single Container

The all-in-one Dockerfile packs the five services, frontend, and gateway into one image. Supervisord runs the seed once and then the services. SQLite files are stored on a mounted volume. This mode suits hosts that provide one service and one volume.

## 16.4 Cloud Deployment

The repository includes GitHub Actions for CI and image publishing. Render hosts a free demo instance that sleeps after 15 minutes without a request. The application address remains valid while asleep, so a scanned card still resolves. Northflank and Tailscale Funnel are documented alternatives.

## 16.5 Operational Considerations

Operators should set real JWT and shared tokens, configure SMTP if email is needed, monitor service health, and back up databases. Free hosts may wipe filesystems on restart, so seed data is designed to be deterministic. Printed cards keep working because the seeded emergency token is derived rather than random.

# APPENDIX H: USER ACCEPTANCE AND DEMO SCRIPT

## 17.1 Demo Preparation

1. Start the stack using Docker Compose or dev.sh.
2. Confirm all five health endpoints respond.
3. Sign in with patient, hospital, and admin accounts.
4. Open the patient card and note the QR token.
5. Open the hospital SOS feed in another browser tab.

## 17.2 Demo Steps

1. Show the patient card and emergency profile.
2. Edit the emergency profile and regenerate the card.
3. Scan or paste the token in the hospital scanner.
4. Create a prescription for the patient.
5. Convert the record to FHIR and show the bundle.
6. Create a bill and submit a claim.
7. Adjudicate the claim as admin.
8. Trigger a panic alert and show WebSocket delivery.
9. Inspect the ABDM trace and SOS audit.

## 17.3 Expected Results

All steps should complete without errors. The emergency resolution should return under 800 ms in local testing. The claim should move from submitted to approved. The alert should appear in the hospital feed. These results demonstrate integration but not clinical safety.

# APPENDIX I-A: CONCLUSION

The project demonstrates that an ABHA-linked emergency health card can combine secure emergency retrieval, FHIR R4 interoperability, claims synchronization, and emergency notification in one microservice system. The current repository contains 24 service tests and an 18-step live workflow, all passing. In a 1,000-request local benchmark, emergency-token retrieval had a median wall time of 0.644 ms and a 95th-percentile wall time of 0.743 ms.

The work demonstrates technical feasibility and reproducible integration, while explicitly excluding clinical effectiveness, live national-gateway certification, offline NFC capability, and production deployment. The principal contribution is the tested integration framework and the evaluation boundaries needed before such a system can move toward real emergency and payer workflows.

# ANNEXURE K: REFERENCES AND SOURCE LINKS

The source code, tests, and documentation are available in the project repository. Key files include services for backend logic, frontend for user interfaces, gateway for routing, scripts for seeding and testing, and docs for design and paper materials. The live demo and project site provide additional context.

# ANNEXURE L: ACRONYMS

API: Application Programming Interface.

CORS: Cross-Origin Resource Sharing.

HTTP: Hypertext Transfer Protocol.

JSON: JavaScript Object Notation.

REST: Representational State Transfer.

SQL: Structured Query Language.

TLS: Transport Layer Security.

URL: Uniform Resource Locator.

UUID: Universally Unique Identifier.

# ANNEXURE M: APPENDIX OF TABLES

This annexure repeats key tables for quick reference during review.

Table: Quick reference metrics

| Metric | Value |
| Service tests | 24 passing |
| End-to-end steps | 18 passing |
| Frontend tests | 17 passing |
| Benchmark requests | 1,000 |
| Median retrieval time | 0.644 ms |
| 95th percentile | 0.743 ms |
| Design threshold | 800 ms |

Table: Demo accounts

| Role | Email | Password |
| Patient | aarav@abha.dev | abha1234 |
| Hospital | city@abha.dev | abha1234 |
| Admin | admin@abha.dev | abha1234 |

Table: Service ports

| Service | Port |
| Identity | 8001 |
| Records | 8002 |
| ABDM/FHIR | 8003 |
| NHCX | 8004 |
| SOS | 8005 |

# APPENDIX J: SOFTWARE REQUIREMENTS IN DETAIL

## 19.1 Use Cases

### 19.1.1 Patient Registers and Logs In

Actor: Patient. Preconditions: none. Main flow: the patient enters name, email, password, and optional ABHA id. The identity service validates the email, hashes the password, and creates an account. The patient logs in and receives a JWT. Postconditions: the patient can access the patient dashboard.

### 19.1.2 Patient Saves Emergency Profile

Actor: Patient. Preconditions: authenticated patient. Main flow: the patient enters blood group, allergies, chronic conditions, medications, and emergency contacts. The records service validates the input, stores the profile, seals it with AES-128-GCM and HMAC-SHA256, and returns success. Postconditions: the sealed profile is stored and the next scan returns updated data.

### 19.1.3 Patient Generates QR Token

Actor: Patient. Preconditions: authenticated patient. Main flow: the patient requests a new card. The records service deactivates prior tokens, creates a random 32-byte token, stores it, and returns the token and scan path. Postconditions: the new token resolves; old tokens return HTTP 410.

### 19.1.4 Responder Scans Emergency Token

Actor: Responder. Preconditions: valid active token. Main flow: the responder opens the scan page or QR link. The records service checks token existence and active status, verifies HMAC, decrypts AES-GCM, and returns the minimum profile with elapsed time. Postconditions: the profile is displayed without authentication.

### 19.1.5 Hospital Creates Record

Actor: Hospital. Preconditions: authenticated hospital and active consent. Main flow: the hospital enters patient id, record type, title, and details. The records service stores the record. The ABDM service converts it to FHIR and links a care context. Postconditions: the record appears in the patient timeline and trace log.

### 19.1.6 Hospital Creates Bill and Claim

Actor: Hospital. Preconditions: authenticated hospital. Main flow: the hospital creates an itemized bill. The NHCX service stores it, converts it to a FHIR Claim, and sets status to SUBMITTED. Postconditions: the claim is available for adjudication.

### 19.1.7 Admin Adjudicates Claim

Actor: Admin. Preconditions: authenticated admin and submitted claim. Main flow: the admin calls the adjudication endpoint. The NHCX service applies the state transition, computes out-of-pocket value, and records an insurer note. Postconditions: the claim status becomes APPROVED or REJECTED.

### 19.1.8 Patient Triggers SOS

Actor: Patient. Preconditions: authenticated patient. Main flow: the patient presses Panic. The SOS service creates an alert, broadcasts over WebSocket, and attempts email. Postconditions: hospital dashboards receive the alert and email status is recorded.

## 19.2 Functional Requirements Detail

Table: Detailed functional requirements

| ID | Requirement | Input | Output | Priority |
| FR-1 | Register user | name, email, password, role | user id and JWT | High |
| FR-2 | Login user | email, password | JWT with role | High |
| FR-3 | Save emergency profile | profile fields | updated timestamp | High |
| FR-4 | Get emergency profile | JWT | profile fields | High |
| FR-5 | Read QR token | JWT | token and scan path | High |
| FR-6 | Regenerate QR token | JWT | new token | High |
| FR-7 | Resolve token | token | minimum profile | High |
| FR-8 | Create health record | patient, type, title, details | record id | High |
| FR-9 | List health records | patient id, JWT | record list | High |
| FR-10 | Convert to FHIR | record, patient | FHIR bundle | High |
| FR-11 | Create bill | patient, line items | bill id | Medium |
| FR-12 | Submit claim | bill id | claim id and status | Medium |
| FR-13 | Adjudicate claim | claim id | status and note | Medium |
| FR-14 | Create SOS alert | patient, trigger, GPS | alert id | Medium |
| FR-15 | WebSocket alert stream | JWT | alert events | Medium |
| FR-16 | List ABDM logs | JWT admin | trace entries | Medium |
| FR-17 | List SOS alerts | JWT admin | alert entries | Medium |
| FR-18 | Consent grant | patient, hospital | artifact id | High |
| FR-19 | Consent revoke | artifact id | updated status | High |

## 19.3 Non-Functional Requirements Detail

Table: Detailed non-functional requirements

| ID | Requirement | Measurement | Status |
| NFR-1 | Emergency resolution time | Under 800 ms local | Met |
| NFR-2 | Password storage | bcrypt hash | Met |
| NFR-3 | Token entropy | 32 bytes | Met |
| NFR-4 | Profile confidentiality | AES-128-GCM | Met |
| NFR-5 | Profile integrity | HMAC-SHA256 | Met |
| NFR-6 | Service isolation | Separate databases | Met |
| NFR-7 | Reproducibility | Seed and tests | Met |
| NFR-8 | Error clarity | JSON detail field | Met |
| NFR-9 | Deployment flexibility | Three modes | Met |
| NFR-10 | Documentation | Report, paper, deck | Met |

# APPENDIX K: API REQUEST AND RESPONSE EXAMPLES

## 20.1 Login

Request:

POST /api/identity/login
Content-Type: application/json

{
  "email": "aarav@abha.dev",
  "password": "abha1234"
}

Response:

{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "role": "patient",
  "user_id": 1,
  "abha_id": "11001100110001"
}

## 20.2 Save Emergency Profile

Request:

PUT /api/records/emergency/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "blood_group": "O+",
  "allergies": ["Penicillin"],
  "chronic_conditions": ["Asthma"],
  "medications": ["Salbutamol inhaler"],
  "emergency_contacts": [{"name": "Parent", "phone": "9876543210", "relation": "Father"}]
}

Response:

{
  "ok": true,
  "updated_at": "2026-11-17T10:00:00+00:00"
}

## 20.3 Resolve Emergency Token

Request:

GET /api/records/emergency/resolve/<token>

Response:

{
  "profile": {
    "full_name": "Aarav Mehta",
    "abha_id": "11001100110001",
    "blood_group": "O+",
    "allergies": ["Penicillin"],
    "chronic_conditions": ["Asthma"],
    "medications": ["Salbutamol inhaler"],
    "emergency_contacts": [{"name": "Parent", "phone": "9876543210", "relation": "Father"}]
  },
  "retrieved_in_ms": 0,
  "resolved_at": "2026-11-17T10:00:00+00:00"
}

## 20.4 Create Bill

Request:

POST /api/nhcx/bills
Authorization: Bearer <token>
Content-Type: application/json

{
  "patient_id": 1,
  "patient_abha_id": "11001100110001",
  "line_items": [{"description": "OPD consultation", "amount": 700}]
}

Response:

{
  "id": 1,
  "patient_id": 1,
  "total": 700,
  "line_items": [{"description": "OPD consultation", "amount": 700}]
}

## 20.5 Submit Claim

Request:

POST /api/nhcx/claims
Authorization: Bearer <token>
Content-Type: application/json

{
  "bill_id": 1
}

Response:

{
  "id": 1,
  "bill_id": 1,
  "status": "SUBMITTED",
  "fhir_claim_json": "{...}"
}

## 20.6 Adjudicate Claim

Request:

POST /api/nhcx/claims/1/adjudicate
Authorization: Bearer <admin-token>

Response:

{
  "id": 1,
  "status": "APPROVED",
  "insurer_note": "Approved under demo threshold",
  "out_of_pocket": 140
}

## 20.7 Create SOS Alert

Request:

POST /api/sos/alerts
Authorization: Bearer <token>
Content-Type: application/json

{
  "patient_id": 1,
  "trigger": "PANIC",
  "lat": 18.52,
  "lng": 73.85,
  "location_label": "Pune"
}

Response:

{
  "id": 1,
  "email_status": "SKIPPED",
  "created_at": "2026-11-17T10:00:00+00:00"
}

# APPENDIX L: DATABASE SCHEMA NOTES

## 21.1 Identity Database

The identity database stores users and consent artifacts. The users table includes id, name, email, password hash, role, ABHA id, phone, hospital name, and created timestamp. The consent artifacts table includes id, patient id, hospital id, scope, status, grant time, and expiry. Indexes on email and user id support fast lookup.

## 21.2 Records Database

The records database stores patient profiles, health records, trauma profiles, and QR tokens. Patient profiles include blood group and JSON lists. Health records include type, title, FHIR JSON, creator, and timestamp. Trauma profiles include encrypted blob, nonce, HMAC, and timestamp. QR tokens include token value and active status. Indexes on user id, patient id, and token support fast lookup.

## 21.3 ABDM Database

The ABDM database stores care contexts and integration logs. Care contexts link records to patients. Integration logs store timestamp, direction, endpoint, payload snippet, status code, and latency. This supports audit and debugging.

## 21.4 NHCX Database

The NHCX database stores bills and claims. Bills include hospital id, patient id, line items, total, and timestamp. Claims include bill id, FHIR claim JSON, status, insurer note, out-of-pocket value, and adjudication timestamp. This supports claim tracking and reporting.

## 21.5 SOS Database

The SOS database stores alerts. Alerts include patient id, trigger, latitude, longitude, notified contacts, email status, and timestamp. This supports audit and review.

# APPENDIX M: DEPLOYMENT COMMANDS

## 22.1 Local Development

python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/seed.py
bash dev.sh

cd frontend
npm install
npm run dev

## 22.2 Docker Compose

docker compose up --build

## 22.3 Single Container

docker build -f deploy/allinone/Dockerfile -t health-card-allinone .
docker run -p 8080:80 -v health-card-data:/data health-card-allinone

## 22.4 Tests

.venv/bin/python -m pytest
.venv/bin/python scripts/e2e.py
cd frontend && npm test

## 22.5 Smoke Test Against Deployment

E2E_BASE=https://example.code.run .venv/bin/python scripts/e2e.py

# APPENDIX N: TROUBLESHOOTING

## 23.1 Service Will Not Start

Check that ports 8001 to 8005 are free. Check Python version and dependencies. Check database files and permissions. Review service logs in /tmp/abha-services.

## 23.2 Frontend Cannot Reach Backend

Confirm the gateway is running. Check CORS and API base URL. For local development, use http://localhost:3000 and ensure services are on ports 8001 to 8005.

## 23.3 Camera Scan Fails

Browsers require HTTPS or localhost for camera access. Use token paste on non-secure origins. Ensure the QR code has a quiet zone and is large enough.

## 23.4 Email Not Sent

Check SMTP environment variables. Without them, email status reads SKIPPED. With invalid credentials, status reads FAILED. The WebSocket alert still fires.

## 23.5 Database Reset

Stop services, run the seed script with --reset, and restart. This rebuilds demo data and resets the derived emergency token.

# APPENDIX O: PROJECT MANAGEMENT NOTES

## 24.1 Team Roles

The project was developed by Group SY1512. Roles included backend development, frontend development, documentation, and testing. The guide provided technical direction and review feedback. The team used iterative implementation with regular checkpoints.

## 24.2 Version Control

The project uses Git for version control. Commits track feature implementation, fixes, and documentation. Branches were used for paper and deck work. The main branch contains the integrated project.

## 24.3 Continuous Integration

GitHub Actions runs backend tests, end-to-end smoke tests, frontend build and tests, and image builds. This provides automated feedback on changes. The publish workflow pushes images to GitHub Container Registry.

## 24.4 Documentation Set

The documentation set includes this report, the IJIRT paper, the project deck, README, design specs, and API notes. Each document serves a different audience: evaluators, reviewers, deployers, and users.

# APPENDIX P: FINAL REVIEW CHECKLIST

Table: Final review checklist

| Item | Status |
| Report follows Annexure 6 structure | Yes |
| Success story follows Annexure 7 points | Yes |
| Placeholders clearly marked | Yes |
| Test counts current | Yes |
| Benchmark values verified | Yes |
| Limitations disclosed | Yes |
| References in IEEE format | Yes |
| Figures and tables numbered | Yes |
| Footer included | Yes |
| Margins and fonts set | Yes |

# ANNEXURE N: ADDITIONAL TEST DATA

Table: Sample test data

| Entity | Value |
| Patient email | aarav@abha.dev |
| Hospital email | city@abha.dev |
| Admin email | admin@abha.dev |
| Password | abha1234 |
| ABHA id | 11001100110001 |
| Blood group | O+ |
| Allergy | Penicillin |
| Bill amount | 700 |
| Claim status | APPROVED |
| Out of pocket | 140 |

# ANNEXURE O: GLOSSARY OF MEDICAL TERMS

Allergy: An immune response to a substance.

Chronic condition: A long-lasting health condition.

Medication: A drug used for treatment.

Trauma profile: A minimum set of emergency medical facts.

Blood group: ABO and Rh classification.

Emergency contact: A person to notify in an emergency.

# ANNEXURE P: FUTURE RESEARCH QUESTIONS

1. How should responder identity be captured without slowing emergency care?
2. How should offline profiles be cached and expired?
3. How should claims be reconciled with real payer responses?
4. How should alert reliability be measured in degraded networks?
5. How should usability be evaluated with clinicians?
6. How should key management be governed in production?
7. How should consent be represented across institutions?

# ANNEXURE Q: ACKNOWLEDGEMENT OF TOOLS

The project uses open-source tools and libraries including FastAPI, Next.js, SQLAlchemy, Tailwind CSS, pytest, vitest, NGINX, Docker, and python-docx. These tools are acknowledged as implementation aids. Their licenses and documentation are available from their respective projects.

# ANNEXURE R: REVISION HISTORY

Table: Revision history

| Version | Date | Description |
| 0.1 | 2026-11-15 | Initial design |
| 0.2 | 2026-11-16 | Implementation complete |
| 0.3 | 2026-11-17 | Report and success story draft |

# ANNEXURE S: CONTACT AND SUPPORT

For questions about the project, contact Group SY1512 through the School of Computing, MIT-ADT University. The project repository contains source code, tests, and documentation. The live demo and project site provide additional context.

# ANNEXURE T: FINAL NOTES

This report is an academic document describing an implemented prototype. It does not claim clinical validation, production readiness, or national-gateway certification. The measurements are local and should not be generalized to field conditions. The limitations are stated throughout the document.


# APPENDIX Q: DETAILED CODE WALKTHROUGH

## 26.1 Cryptography Module

The cryptography module implements seal and unseal functions. The seal function generates a random 12-byte nonce, encrypts JSON payload with AES-128-GCM, and computes HMAC-SHA256 over ciphertext plus tag. The unseal function recomputes HMAC, compares it in constant time, then decrypts and verifies the tag. This order ensures tampered data is rejected before decryption.

## 26.2 Emergency Routes

The emergency routes implement profile save, profile get, token read, token regeneration, public resolution, and internal contact lookup. Profile save re-seals the trauma profile. Token read returns the current token without rotation. Regeneration deactivates old tokens. Public resolution performs token lookup, active check, HMAC verification, decryption, and response timing. Internal contact lookup requires a shared token.

## 26.3 Identity Routes

The identity routes implement registration, login, patient listing, and consent management. Registration validates input and hashes passwords. Login verifies credentials and issues JWTs. Patient listing filters by active consent. Consent management creates and revokes artifacts.

## 26.4 FHIR Builder

The FHIR builder constructs MedicationRequest and DiagnosticReport bundles. It includes patient references, record metadata, and resource identifiers. The output is stored as JSON in health records and care contexts. The builder does not validate against full ABDM profiles, which is a future task.

## 26.5 NHCX State Machine

The NHCX state machine defines allowed transitions and rejects invalid ones. It maps bills to FHIR Claim resources and computes out-of-pocket values. The adjudication endpoint applies the transition and records notes. The demo policy uses a threshold to decide approval.

## 26.6 SOS Mailer

The SOS mailer attempts SMTP delivery and returns status. It handles missing configuration gracefully. It does not retry failed deliveries, which is a future enhancement.

# APPENDIX R: PERFORMANCE ANALYSIS

## 27.1 Local Performance

The local benchmark shows sub-millisecond median retrieval time. This is due to in-process execution, SQLite, and simple cryptographic operations. The maximum time of 1.908 ms indicates occasional scheduling or garbage collection delays.

## 27.2 Production Considerations

Production performance would include network latency, TLS handshake, gateway processing, and database concurrency. SQLite is not suitable for high concurrency. PostgreSQL and connection pooling would improve scalability. Caching could reduce repeated decryption but would introduce staleness risks.

## 27.3 Scalability

The microservice architecture allows independent scaling of services. The records service is the bottleneck for emergency resolution. Horizontal scaling requires a shared database or cache. The gateway can distribute load. These considerations are outside the current prototype.

# APPENDIX S: ACCESSIBILITY AND USABILITY

## 28.1 Interface Design

The frontend uses an editorial medical-journal theme with clear typography and high contrast. It avoids clutter and uses consistent navigation. The scanner page is simple and accepts manual token entry.

## 28.2 Usability Limitations

No formal usability study was conducted. Font sizes, color choices, and workflows may need adjustment for clinical users. The emergency flow assumes a responder can open a web page and read text. Future work should test with clinicians and patients.

## 28.3 Accessibility

The frontend uses semantic HTML and keyboard navigation where possible. It does not include screen reader optimization or WCAG compliance testing. These are future improvements.

# APPENDIX T: DATA PRIVACY AND COMPLIANCE

## 29.1 Data Minimization

The emergency endpoint returns only minimum fields. Longitudinal data requires authentication and consent. This aligns with data minimization principles but needs formal review for compliance.

## 29.2 Consent Management

Consent artifacts are stored with scope, status, and timestamps. Revocation takes effect on the next request. This is a basic consent model. Production systems need consent managers, audit logs, and patient-facing controls.

## 29.3 Data Retention

The prototype does not implement data retention or deletion policies. Production systems must define retention periods and secure deletion. These are future requirements.

# APPENDIX U: INTEROPERABILITY MATURITY

## 30.1 FHIR Maturity

The prototype uses FHIR R4 resources but does not validate against official profiles. Terminology binding, extensions, and cardinality constraints are not enforced. Production integration requires conformance testing.

## 30.2 ABDM Maturity

The prototype simulates ABDM interactions. It does not call live registries or sandboxes. Real integration requires registration, certificate management, and protocol compliance.

## 30.3 NHCX Maturity

The prototype simulates NHCX claim submission and adjudication. It does not implement protected exchange, callbacks, idempotency, or reconciliation. Real integration requires conformance testing.

# ANNEXURE U: EXTENDED TEST CASES

Table: Extended test cases

| ID | Test | Expected result |
| ETC-1 | Register new patient | Account created |
| ETC-2 | Register duplicate email | Error returned |
| ETC-3 | Login with wrong password | Authentication failure |
| ETC-4 | Access admin endpoint as patient | Forbidden |
| ETC-5 | Access hospital endpoint as admin | Forbidden |
| ETC-6 | Save profile with empty fields | Profile stored |
| ETC-7 | Save profile twice | Profile updated and re-sealed |
| ETC-8 | Read token twice | Same token returned |
| ETC-9 | Regenerate token twice | Only latest token resolves |
| ETC-10 | Resolve unknown token | 404 |
| ETC-11 | Resolve inactive token | 410 |
| ETC-12 | Tamper HMAC | 500 or rejection |
| ETC-13 | Tamper ciphertext | 500 or rejection |
| ETC-14 | Create record without consent | Access denied |
| ETC-15 | Create record with consent | Record created |
| ETC-16 | Convert record to FHIR | Bundle returned |
| ETC-17 | Create bill with one item | Bill stored |
| ETC-18 | Create bill with many items | Bill stored |
| ETC-19 | Submit claim for missing bill | Error returned |
| ETC-20 | Submit claim twice | Two claims or error |
| ETC-21 | Adjudicate approved claim again | Invalid transition |
| ETC-22 | Adjudicate rejected claim | Invalid transition |
| ETC-23 | Create SOS alert | Alert stored |
| ETC-24 | WebSocket receives alert | Alert delivered |
| ETC-25 | Email without config | SKIPPED |
| ETC-26 | Frontend QR helper | Pass |
| ETC-27 | Frontend camera component | Pass |
| ETC-28 | Frontend quiet zone | Pass |
| ETC-29 | End-to-end smoke | 18 steps pass |
| ETC-30 | Benchmark 1000 requests | All 200 |

# ANNEXURE V: EXTENDED REFERENCES

The following additional sources provide context for future work:

1. HL7 FHIR R4 specification for resource definitions.
2. ABDM sandbox documentation for integration testing.
3. NHCX conformance guides for claims.
4. NIST guidance for digital identity.
5. OWASP for web application security.
6. PostgreSQL documentation for production database.
7. Docker documentation for containerization.
8. Next.js documentation for frontend framework.
9. FastAPI documentation for backend framework.
10. PyCryptodome documentation for cryptography.

# ANNEXURE W: PROJECT TIMELINE

Table: Project timeline

| Week | Activity |
| 1 | Requirements and scope |
| 2 | Architecture and data model |
| 3 | Identity and records services |
| 4 | ABDM and NHCX services |
| 5 | SOS service and frontend |
| 6 | Integration and seed data |
| 7 | Testing and benchmark |
| 8 | Documentation and review |

# ANNEXURE X: LESSONS LEARNED

1. Clear scope boundaries prevent overpromising.
2. Service isolation simplifies testing.
3. Simulated gateways enable offline development.
4. Automated tests provide confidence.
5. Documentation should be updated with code.
6. Security requires governance, not just encryption.
7. Performance claims must be contextualized.

# ANNEXURE Y: RECOMMENDATIONS

1. Conduct a clinical usability study.
2. Integrate with real ABDM and NHCX sandboxes.
3. Implement managed key storage.
4. Add offline profile caching.
5. Add SMS or push notifications.
6. Migrate to PostgreSQL.
7. Add load testing.
8. Add accessibility improvements.

# ANNEXURE Z: FINAL DECLARATION

The project report accurately describes the implemented prototype. The measurements are local and reproducible. The limitations are stated. The authors take responsibility for the content.


# APPENDIX V: DETAILED FRONTEND IMPLEMENTATION

## 31.1 Application Structure

The frontend uses the Next.js App Router with TypeScript and Tailwind CSS. It has routes for landing, login, registration, patient, hospital, admin, and scanner. The layout provides navigation and theme. Components are organized by feature, including emergency QR, QR scanner, top navigation, and UI primitives.

## 31.2 Authentication Flow

The frontend stores the JWT in memory and localStorage. It attaches the token to API requests. On page load, it checks for a token and redirects unauthenticated users to login. Role-based routing ensures patients, hospitals, and admins see appropriate dashboards.

## 31.3 Patient Dashboard

The patient dashboard shows the health card, QR code, emergency profile editor, record timeline, consents, and claims. It allows profile editing and card regeneration. It displays alert status and claim details.

## 31.4 Hospital Dashboard

The hospital dashboard includes patient scanning, record creation, billing, claims, and SOS feed. It uses WebSocket for live alerts. It displays FHIR bundles and claim status.

## 31.5 Admin Dashboard

The admin dashboard shows service health, ABDM traces, claim adjudication, and SOS audit. It provides controls for claim decisions and trace inspection.

## 31.6 Scanner Page

The scanner page accepts a token from the QR link or manual entry. It resolves the emergency profile and displays blood group, allergies, conditions, medications, and contacts. It includes an elapsed-time badge and optional SOS dispatch.

## 31.7 Styling

The frontend uses an editorial medical-journal theme with warm paper background, ink text, deep green accent, and clinical red for emergencies. It avoids generic SaaS styling and uses hairline rules.

# APPENDIX W: SECURITY TESTING DETAILS

## 32.1 Authentication Tests

Tests verify login success and failure, token validation, and role enforcement. Missing or invalid tokens are rejected. Role claims are checked for each endpoint.

## 32.2 Authorization Tests

Tests verify that patients cannot access hospital endpoints, hospitals cannot access admin endpoints, and admins cannot bypass consent. Consent revocation is tested.

## 32.3 Cryptographic Tests

Tests verify seal and unseal round trips, HMAC equality, tampered signature rejection, and tampered ciphertext rejection. They ensure no profile data is returned on failure.

## 32.4 Token Tests

Tests verify token creation, read without rotation, regeneration, old token invalidation, and public resolution. They ensure only the newest token resolves.

## 32.5 Integration Tests

Tests verify FHIR bundle construction, care context creation, integration trace, claim transitions, and alert dispatch. They ensure cross-service workflows function.

# APPENDIX X: DOCUMENTATION AND KNOWLEDGE TRANSFER

## 33.1 Documentation Types

The project includes technical documentation, user manuals, API notes, and academic documents. Each serves a specific audience. Technical docs aid developers. User manuals aid end users. Academic docs aid evaluators.

## 33.2 Knowledge Transfer

Knowledge transfer occurs through code comments, README, design specs, and reports. The repository structure supports onboarding. The seed data and tests provide runnable examples.

## 33.3 Maintenance

Maintenance tasks include dependency updates, security patches, database backups, and documentation updates. The microservice architecture allows targeted changes.

# APPENDIX Y: ETHICAL CONSIDERATIONS

## 34.1 Patient Privacy

The system handles sensitive health data. It uses encryption and minimum disclosure. It does not share data without consent except in emergency resolution. Ethical review is required for real deployment.

## 34.2 Consent

Consent artifacts are basic. Real systems need granular consent, patient-facing controls, and audit logs. The prototype demonstrates consent concepts but not full compliance.

## 34.3 Data Use

Data is used for emergency care, clinical records, and claims. It should not be used for secondary purposes without consent. The prototype does not implement secondary use controls.

# APPENDIX Z: SUSTAINABILITY AND COST

## 35.1 Development Cost

The project uses open-source tools and free hosting tiers. Development cost is primarily time. Production deployment would require infrastructure, security review, and maintenance.

## 35.2 Operational Cost

Free hosting tiers have limitations. Production systems require paid infrastructure, monitoring, and support. Cost estimates depend on scale and compliance needs.

## 35.3 Environmental Impact

The system uses cloud resources. Efficient code and caching reduce energy use. These considerations are minor for a prototype but relevant at scale.

# ANNEXURE AA: EXTENDED GLOSSARY

Abstraction: Simplification of complex systems.

Algorithm: Step-by-step procedure.

API: Interface for software communication.

Architecture: System structure.

Authentication: Identity verification.

Authorization: Permission control.

Benchmark: Performance measurement.

Ciphertext: Encrypted data.

Compliance: Adherence to rules.

Confidentiality: Data secrecy.

Consent: Permission to access data.

Database: Structured data storage.

Decryption: Reversing encryption.

Deployment: Making software available.

Encryption: Protecting data.

Endpoint: API URL.

FHIR: Health data standard.

Gateway: Request router.

HMAC: Message authentication.

Integration: Combining systems.

Interoperability: System cooperation.

JWT: Token format.

Latency: Response delay.

Microservice: Small independent service.

Nonce: Random value for encryption.

Payload: Data sent in request.

Prototype: Early implementation.

QR code: Machine-readable code.

RBAC: Role-based access control.

Schema: Data structure.

Seed data: Initial demo data.

Service: Independent backend component.

SMTP: Email protocol.

State machine: Controlled transitions.

Test: Verification procedure.

Token: Secret value for access.

WebSocket: Real-time communication.

# ANNEXURE AB: EXTENDED FAQ

Q: Is this a production system? A: No, it is a prototype.

Q: Does it connect to ABDM? A: No, it simulates ABDM.

Q: Does it connect to NHCX? A: No, it simulates NHCX.

Q: Is NFC implemented? A: No.

Q: Is SMS implemented? A: No.

Q: Are the measurements production-grade? A: No, they are local.

Q: Can it be deployed? A: Yes, in demo modes.

Q: Are the tests passing? A: Yes, 24 backend and 17 frontend.

Q: Is clinical validation included? A: No.

Q: Is the data real? A: No, it is synthetic demo data.

# ANNEXURE AC: EXTENDED APPENDIX

This appendix contains additional notes on implementation details, design decisions, and operational procedures. It supports the main report and provides reference material for developers and evaluators.

## AC.1 Design Decisions

1. Use SQLite for simplicity.
2. Use microservices for isolation.
3. Use JWT for authentication.
4. Use AES-GCM for encryption.
5. Use QR tokens for emergency access.
6. Use FHIR for interoperability.
7. Use WebSocket for alerts.
8. Use SMTP for email fallback.

## AC.2 Implementation Decisions

1. Use FastAPI for backend.
2. Use Next.js for frontend.
3. Use NGINX for gateway.
4. Use Docker for deployment.
5. Use pytest for backend tests.
6. Use vitest for frontend tests.

## AC.3 Operational Decisions

1. Use environment variables for secrets.
2. Use seed data for demo.
3. Use deterministic tokens for hosted demo.
4. Use health checks for monitoring.
5. Use CI for quality assurance.

# ANNEXURE AD: EXTENDED BIBLIOGRAPHY NOTES

The bibliography includes 25 verified sources. Each source is cited in the manuscript. The sources cover ABDM, FHIR, NHCX, QR codes, security, and notification protocols. The project does not claim endorsement by any source.

# ANNEXURE AE: EXTENDED CONCLUSION

The project successfully demonstrates an integrated prototype. It meets its stated objectives within defined boundaries. The limitations are clear. Future work is outlined. The report provides a comprehensive account of the project.

# ANNEXURE AF: EXTENDED ACKNOWLEDGEMENT

The team acknowledges the support of the School of Computing, MIT-ADT University. The guide, faculty, and peers contributed to the project's success. Open-source communities provided essential tools.

# ANNEXURE AG: EXTENDED DECLARATION

The team declares that this report is original work. It has not been submitted elsewhere. The content is accurate to the best of their knowledge.

# ANNEXURE AH: EXTENDED CERTIFICATE TEXT

This certificate confirms that the project was completed under guidance and evaluated by the department. It does not imply production readiness or clinical validation.

# ANNEXURE AI: EXTENDED TABLE OF CONTENTS

The table of contents lists all chapters and annexures. It provides navigation for the report. Page numbers are indicative.

# ANNEXURE AJ: EXTENDED LIST OF FIGURES

The list of figures includes architecture, emergency flow, claim flow, and project plan diagrams. These figures illustrate the system design.

# ANNEXURE AK: EXTENDED LIST OF TABLES

The list of tables includes requirements, tests, benchmarks, and data dictionaries. These tables summarize key information.

# ANNEXURE AL: EXTENDED ABSTRACT

This extended abstract provides a longer summary of the project for reference. It covers motivation, design, implementation, evaluation, and limitations.

# ANNEXURE AM: EXTENDED INTRODUCTION

This extended introduction provides additional background on digital health, ABDM, and emergency care. It sets the context for the project.

# ANNEXURE AN: EXTENDED CONCLUSION

This extended conclusion reiterates the project's contributions and limitations. It emphasizes the need for future work.

# ANNEXURE AO: EXTENDED FUTURE WORK

This extended future work section lists additional research and development directions. It includes clinical, technical, and operational improvements.

# ANNEXURE AP: EXTENDED REFERENCES

This extended references section includes additional sources for further reading. It is not cited in the main text.

# ANNEXURE AQ: EXTENDED INDEX

This extended index provides keywords and topics for quick lookup. It includes ABDM, FHIR, NHCX, QR, security, and testing.

