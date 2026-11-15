from dataclasses import dataclass


@dataclass(frozen=True)
class SlideCopy:
    index: int
    section: str
    title: str
    message: str
    evidence: tuple[str, ...]
    notes: str


SLIDES = (
    SlideCopy(
        index=1,
        section="OPEN",
        title="At 03:12, the ambulance doesn’t need a login.",
        message="A portable emergency identity that works before a responder login.",
        evidence=(
            "ABDM + NHCX",
            "AES-128-GCM trauma profile",
            "Offline-capable demo",
        ),
        notes=(
            "This project turns the ABHA health card into an emergency instrument, "
            "not only a digital identity. The same patient record supports three "
            "workflows: a responder scanning an opaque QR token, a hospital writing "
            "standards-shaped clinical records, and an administrator tracing claims "
            "and alerts. The patient creates the random token from their authenticated "
            "card; the responder needs no login."
        ),
    ),
    SlideCopy(
        index=2,
        section="PROBLEM",
        title="Critical context arrives fragmented.",
        message="Emergency facts are split across portals, files, and workflows.",
        evidence=(
            "Separate portals",
            "Missing responder context",
            "Emergency-time penalty",
        ),
        notes=(
            "During an emergency, the most important facts are often hardest to "
            "retrieve. Allergies may sit in one file, medications in another, and "
            "coverage in a billing system not yet checked. A responder should not "
            "need a login, multiple tabs, or a patient’s memory to make a safe initial "
            "decision. This context gap is what the project removes."
        ),
    ),
    SlideCopy(
        index=3,
        section="SOLUTION",
        title="One scan. The right context. Immediately.",
        message="An opaque QR token resolves a minimal, verified trauma profile.",
        evidence=(
            "Opaque random QR token",
            "Blood group + allergies + conditions",
            "Retrieval target under 800 ms",
        ),
        notes=(
            "The patient card contains an opaque random lookup token, not sensitive "
            "medical data itself. The scanner uses that token to find the stored profile, "
            "then verifies the encrypted profile’s HMAC-SHA256 signature before "
            "AES-128-GCM decryption. It returns responder-critical facts. The API also "
            "measures retrieval time so the interface can communicate latency honestly. "
            "The design target is under 800 milliseconds."
        ),
    ),
    SlideCopy(
        index=4,
        section="EXPERIENCE",
        title="One patient. Three workspaces.",
        message=(
            "The same identity supports purpose-built patient, hospital, and admin "
            "views."
        ),
        evidence=("Patient", "Hospital", "Admin"),
        notes=(
            "The product avoids forcing every actor into one generic dashboard. "
            "Patients manage their card, emergency profile, consent, records, and "
            "claims. Hospitals scan a patient, write records, create bills, and "
            "monitor live alerts. Administrators trace integrations, adjudicate "
            "claims, and audit SOS history. The interface changes with the role while "
            "the underlying patient identity and service-owned records remain "
            "consistent."
        ),
    ),
    SlideCopy(
        index=5,
        section="ARCHITECTURE",
        title="Anatomy of a health card.",
        message="Five focused services cooperate behind one patient-facing gateway.",
        evidence=(
            "5 FastAPI services",
            "Next.js frontend",
            "NGINX gateway",
            "5 SQLite databases",
        ),
        notes=(
            "The backend is intentionally split by business capability. Identity owns "
            "authentication and consent. Records owns profiles, clinical records, "
            "encrypted trauma data, and QR tokens. ABDM maps records to HL7 FHIR v4. "
            "NHCX owns bills and claim adjudication. SOS owns live alerts and "
            "notification. Each service owns a separate SQLite database, while NGINX "
            "provides one routing boundary for the Next.js frontend."
        ),
    ),
    SlideCopy(
        index=6,
        section="SECURITY",
        title="Sealed by default. Opened by need.",
        message=(
            "The emergency path verifies the encrypted stored trauma profile before "
            "decrypting anything."
        ),
        evidence=(
            "16-byte random QR token",
            "HMAC verifies encrypted stored trauma profile before decryption",
            "AES-128-GCM encryption",
            "Consent gate",
        ),
        notes=(
            "The trauma profile is encrypted with AES-128-GCM. After an opaque random "
            "token locates it, the server verifies the encrypted trauma profile’s "
            "HMAC-SHA256 signature before attempting decryption, rejecting tampered "
            "ciphertext early. The QR carries a revocable 16-byte lookup token, not medical "
            "details. Records remain protected by role checks and consent artifacts, allowing "
            "consent revocation without changing the emergency QR profile."
        ),
    ),
    SlideCopy(
        index=7,
        section="INTEROPERABILITY",
        title="Native data. No translation drama.",
        message=(
            "Clinical events and claims use standards-shaped resources and explicit "
            "trace."
        ),
        evidence=(
            "HL7 FHIR v4",
            "ABDM care contexts",
            "NHCX FHIR Claim",
            "Internally simulated gateways",
        ),
        notes=(
            "A prescription becomes a MedicationRequest, a diagnostic report becomes "
            "a DiagnosticReport, and an itemized bill becomes a FHIR Claim. ABDM "
            "care-context links and gateway calls capture endpoint, status, and latency "
            "for auditability. The ABDM and NHCX interfaces are internally simulated in "
            "this demo so the workflow stays deterministic and available offline; they are "
            "not live government connections."
        ),
    ),
    SlideCopy(
        index=8,
        section="EMERGENCY",
        title="Panic → panel → people.",
        message="One SOS action fans out to the hospital and emergency contacts.",
        evidence=(
            "Authenticated WebSocket",
            "GPS coordinates",
            "SMTP contact email",
        ),
        notes=(
            "Pressing Panic creates one alert and broadcasts it to authenticated "
            "hospital dashboards over WebSocket. The event includes patient identity "
            "and location coordinates. Registered contacts receive email when SMTP is "
            "configured. Email failure never blocks the live alert; the service records "
            "a skipped or failed status while the hospital feed continues. This keeps "
            "emergency delivery resilient to mail outages."
        ),
    ),
    SlideCopy(
        index=9,
        section="EVIDENCE",
        title="Measured, not marketed.",
        message=(
            "The repository demonstrates a working vertical slice with automated "
            "checks."
        ),
        evidence=(
            "19 automated tests",
            "16-step E2E scenario",
            "5 services",
            "One-command service startup",
        ),
        notes=(
            "The project has 19 automated service tests and a 16-step end-to-end "
            "scenario covering authentication, scanning, records, billing, claims, and "
            "SOS. Docker Compose starts the gateway and five services plus a seed job for "
            "seeded data; the Next.js frontend runs separately. We also state the boundaries: "
            "government "
            "gateways are simulated, production hardening is out of scope, and SMTP remains "
            "optional."
        ),
    ),
    SlideCopy(
        index=10,
        section="CLOSE",
        title="A health record that arrives before the ambulance does.",
        message=(
            "The short proof connects identity, emergency access, clinical records, "
            "claims, and alerts."
        ),
        evidence=(
            "Open card",
            "Scan QR",
            "Write FHIR",
            "Push claim",
            "Trigger SOS",
        ),
        notes=(
            "The proof is intentionally short: open the patient card, scan its QR, "
            "write a FHIR-backed record, push an itemized claim, and trigger the live "
            "SOS feed. Next production steps are a PostgreSQL deployment, approval for "
            "real ABDM and NHCX sandbox credentials, stronger observability, and a "
            "controlled clinical pilot. The core contribution is demonstrable as one "
            "connected, offline-capable system."
        ),
    ),
)
