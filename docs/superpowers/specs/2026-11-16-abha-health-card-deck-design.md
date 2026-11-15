# Design Spec — ABHA Health Card 10-Slide Project Deck

Date: 2026-11-16
Project: SY1512 — School of Computing, MIT-ADT University
Source project: `health_card/` — Next-Gen Hybrid Offline-Capable ABHA Health Card
Deliverables: editable 16:9 PowerPoint (`.pptx`) and PDF preview

## 1. Objective

Create a polished 10-slide academic project-review presentation that explains the ABHA Health Card clearly, demonstrates meaningful engineering depth, and feels authored for this project rather than assembled from a generic presentation template.

The deck must support an approximately 5–8 minute review presentation and remain understandable to a mixed academic audience. Every factual claim must be verifiable against the repository; the deck must not invent production metrics, government integration status, medical outcomes, or performance results.

## 2. Audience and Narrative

Primary audience: academic jury or faculty reviewing Group SY1512’s project.

The narrative moves from the emergency problem to the proposed product, then through system design, core technical flows, evidence, and a live-demo close. The story should feel like an emergency dossier rather than a conventional slide deck.

### Slide sequence

1. **Cover — “At 03:12, the ambulance doesn’t need a login.”**
   - Establish the emergency moment and project identity.
   - Visual: oversized black ABHA patient card, coral rescue spine, actual QR mark, project/group footer.
   - Supporting: ABHA + NHCX, encrypted emergency profile, offline-capable demo.

2. **The Problem — “Critical context arrives fragmented.”**
   - Explain that allergies, medications, history, and coverage are separated across portals and files.
   - Visual: 03:12 emergency timeline with detached clinical facts and a visible “context gap.”
   - Supporting: no login-independent responder view in a conventional health workflow.

3. **The Solution — “One scan. The right context. Immediately.”**
   - Present the signed emergency QR as the product’s central interaction.
   - Visual: QR as the visual anchor; blood group, allergies, conditions, and retrieval target arranged as one clinical strip.
   - Supporting: public resolver validates the token before returning a trauma profile.

4. **The Experience — “One patient. Three workspaces.”**
   - Explain the role-specific product journey for Patient, Hospital, and Admin.
   - Visual: three editorial lanes, each anchored by a real product screenshot from the project.
   - Supporting: patient card/consents, hospital scan/records/SOS, admin trace/claims/audit.

5. **System Architecture — “Anatomy of a health card.”**
   - Explain the five-service architecture behind one patient view.
   - Visual: layered service anatomy with Identity, Records, ABDM, NHCX, and SOS; frontend and NGINX gateway; one database per service.
   - Supporting: Next.js frontend, FastAPI services, per-service SQLite databases, JWT/RBAC boundaries.

6. **Core Innovation — “Sealed by default. Opened by need.”**
   - Explain the emergency profile security flow.
   - Visual: tamper-evident seal motif around a numbered flow: signed token → HMAC verification → AES-GCM decryption → consent/access gate.
   - Supporting: encrypted profile at rest, HMAC integrity check before decryption, role-based access, revocable consent.

7. **Interoperability — “Native data. No translation drama.”**
   - Explain how clinical records and claims map to standards-shaped data.
   - Visual: a MedicationRequest/Claim receipt, ABDM trace strip, and NHCX status route.
   - Supporting: HL7 FHIR v4 resources, ABDM care-context trace, itemized bills, FHIR Claim, simulated adjudication.
   - Important qualifier: ABDM and NHCX gateways are internally simulated for reliable offline demonstration.

8. **Emergency Coordination — “Panic → panel → people.”**
   - Explain the live SOS fan-out.
   - Visual: pulse originating from the patient and branching to the hospital feed and emergency contacts; real hospital-dashboard screenshot.
   - Supporting: authenticated WebSocket broadcast, GPS coordinates, SMTP email, graceful `EMAIL_SKIPPED` behavior when SMTP is not configured.

9. **Evidence — “Measured, not marketed.”**
   - Show implementation maturity and test evidence.
   - Visual: audit ledger with large repository-backed figures, test results, offline deployment, and a concise limitations/future-work section.
   - Supporting facts to verify before production: five FastAPI services, per-service databases, repository test count, 16-step E2E scenario, one-command Docker startup, and frontend role areas.
   - Avoid claiming real government-sandbox connectivity, clinical efficacy, production hardening, or measured outcomes beyond the repository.

10. **Close & Demo — “A health record that arrives before the ambulance does.”**
    - End with a memorable five-step demo route and an actionable next action.
    - Visual: five numbered stamps/steps: open card → scan QR → write FHIR record → push claim → trigger SOS.
    - Supporting: actual local-demo QR, concise future-work strip, project and institution details.

## 3. Visual System

### Concept: “Emergency Passport”

The deck behaves like a set of coordinated physical artifacts: a patient card, fragmented emergency file, sealed record, interoperability receipt, dispatch pulse, and audit dossier. It must not resemble a SaaS pitch template.

### Palette

- Graphite black: `#101512`
- Warm bone: `#EEE9DE`
- Bone secondary: `#D8D2C4`
- Rescue coral: `#FF5638` — emergency and SOS only
- Clinical green: `#00A878` — verified/active/successful states
- Off-white: `#FAF8F2`

### Typography

- Display: Georgia Regular — oversized editorial headings and major figures
- UI/body: Arial — high legibility across PowerPoint environments
- Micro-labels: Arial Bold, uppercase, with expanded letter spacing
- Technical identifiers: Courier New — ABHA IDs, tokens, API routes, FHIR fields, and timing values

### Composition Rules

- True 16:9 canvas: 13.333 × 7.5 inches
- Twelve-column alignment grid with approximately 0.65-inch outer margins
- Strong hierarchy: one dominant visual or statement per slide
- Hairline rules (approximately 0.75–1 pt), occasional 4 pt emphasis rules
- Asymmetrical grids, cropped elements, rotated micro-labels, and edge-to-edge blocks
- No gradients, glassmorphism, glow effects, generic floating icon grids, or decorative stock medical imagery
- Rounded corners are limited to the physical health-card/QR artifact; most structural elements use square corners
- Small, sparse line symbols may be drawn as native PowerPoint shapes when they clarify a flow
- Consistent top-level project marker and bottom-right slide number, with subtle progress indicators

### Visual Consistency

Each slide must feel part of one system while using a different composition. Reuse the same paper/black/coral/green palette, type hierarchy, rule weights, label grammar, and artifact motifs. Avoid repeating the exact same layout ten times.

## 4. Asset Strategy

- Build slides primarily with native editable PowerPoint shapes and text.
- Use actual project screenshots for the patient, hospital, and admin experiences. If the runtime cannot be started during production, replace the affected screenshot block with a native PowerPoint wireframe of the same project view rather than omitting the product evidence.
- Generate actual QR codes from project routes; label local/demo QR codes clearly.
- Use diagrams and evidence excerpts from the repository rather than invented charts.
- Include concise speaker notes per slide.
- Do not use AI-generated people, fake doctors, stock hospital photography, or synthetic medical imagery.

## 5. Technical Production

Preferred implementation: Python with `python-pptx` for editable `.pptx` generation, `Pillow`/`qrcode` for QR assets, and a headless browser or existing frontend build for screenshots. PDF export should use LibreOffice when available; otherwise, render slide previews through another available local converter and package them for review.

Every slide must be checked for:

- object overflow and clipping
- text overflow and accidental overlap
- alignment against the grid
- contrast and font-size legibility
- correct factual wording and repository-backed numbers
- correct slide count and ordering
- presence of notes where supported

## 6. Acceptance Criteria

1. Exactly 10 slides in the approved sequence.
2. Editable 16:9 PowerPoint with no slide assembled only from a flat background image.
3. Distinctive “Emergency Passport” visual system with the approved palette.
4. Real project facts, screenshots, QR codes, and test evidence; no fabricated claims.
5. No generic stock-template look: no gradients, glass effects, generic rounded SaaS-card grids, emoji icons, or decorative AI imagery.
6. Clean hierarchy, alignment, whitespace, and consistent formatting across the deck.
7. Speaker notes for all slides.
8. PDF/preview generated and inspected before delivery.
9. Existing uncommitted project work is not overwritten, reformatted, or included in unrelated commits.

## 7. Out of Scope

- Rebuilding or changing the application
- Claims of real ABDM/NHCX production connectivity
- A business-plan or investor pitch
- More than 10 slides
- Generic healthcare stock photography or AI-generated human figures
