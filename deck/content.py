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
        message="A portable emergency identity that works before an account can be opened.",
        evidence=(
            "ABDM + NHCX",
            "AES-128-GCM trauma profile",
            "Offline-capable demo",
        ),
        notes=(
            "This project turns the ABHA health card into an emergency instrument, "
            "not only a digital identity. The same patient record supports three "
            "workflows: a responder scanning a signed QR, a hospital writing "
            "standards-shaped clinical records, and an administrator tracing claims "
            "and alerts. The key design choice is that the demonstration remains "
            "reliable even when external government sandboxes are unavailable."
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
            "During an emergency, the most important facts are often the hardest to "
            "retrieve. Allergies may sit in one file, medications in another, and "
            "coverage in a billing system that has not yet been contacted. A "
            "responder should not need a login, multiple tabs, or a patient’s memory "
            "to make a safe initial decision. That context gap is the problem this "
            "project is designed to remove."
        ),
    ),
    SlideCopy(
        index=3,
        section="SOLUTION",
        title="One scan. The right context. Immediately.",
        message="A signed QR resolves a minimal, verified trauma profile.",
        evidence=(
            "Signed QR token",
            "Blood group + allergies + conditions",
            "Retrieval target under 800 ms",
        ),
        notes=(
            "The patient card contains a signed token, not sensitive medical data "
            "itself. The public scanner validates that token, verifies its integrity, "
            "decrypts the stored trauma profile, and returns a compact set of "
            "responder-critical facts. The API also measures server retrieval time so "
            "the interface can communicate latency honestly. The design target is "
            "under 800 milliseconds, with no patient identity exposed before token "
            "validation."
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
        message="The emergency path validates integrity before it decrypts anything.",
        evidence=(
            "Random 32-byte token",
            "HMAC-SHA256 integrity",
            "AES-128-GCM encryption",
            "Consent gate",
        ),
        notes=(
            "The trauma profile is encrypted at rest with AES-128-GCM. Its "
            "HMAC-SHA256 signature is checked before decryption is attempted, so "
            "tampered ciphertext is rejected early. The QR carries a random, "
            "revocable token rather than medical details. Hospital access to "
            "longitudinal records is separately protected by role checks and consent "
            "artifacts, allowing consent to be revoked without changing the "
            "emergency QR profile."
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
            "care-context links and gateway calls are recorded with endpoint, status, "
            "and latency for auditability. The ABDM and NHCX interfaces are internally "
            "simulated in this demo so the complete workflow remains deterministic "
            "and available offline; they are not presented as live government "
            "connections."
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
            "and location coordinates. Registered contacts are then notified by email "
            "when SMTP is configured. Email failure never blocks the live alert; the "
            "service records a skipped or failed email status while the hospital feed "
            "continues to work. This keeps the emergency path resilient to a "
            "mail-provider outage."
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
            "One-command Docker startup",
        ),
        notes=(
            "The project is backed by 19 automated service tests and a 16-step "
            "end-to-end scenario covering authentication, scanning, records, billing, "
            "claims, and SOS. Docker Compose starts the frontend, gateway, and five "
            "services from one command, with seeded data for a repeatable demo. We "
            "also state the boundaries clearly: government gateways are simulated, "
            "production hardening is out of scope, and SMTP remains optional for the "
            "demo."
        ),
    ),
    SlideCopy(
        index=10,
        section="CLOSE",
        title="A health record that arrives before the ambulance does.",
        message=(
            "The 60-second proof connects identity, emergency access, clinical "
            "records, claims, and alerts."
        ),
        evidence=(
            "Open card",
            "Scan QR",
            "Write FHIR",
            "Push claim",
            "Trigger SOS",
        ),
        notes=(
            "The complete proof is intentionally short: open the patient card, scan "
            "its QR, write a FHIR-backed record, push an itemized claim, and trigger "
            "the live SOS feed. The next production steps are a PostgreSQL "
            "deployment, approval for real ABDM and NHCX sandbox credentials, stronger "
            "observability, and a controlled clinical pilot. The core contribution is "
            "already demonstrable as one connected, offline-capable system."
        ),
    ),
)
