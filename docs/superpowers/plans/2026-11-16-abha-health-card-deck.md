# ABHA Health Card 10-Slide Project Deck Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a polished, editable 10-slide 16:9 PowerPoint and PDF preview that presents the ABHA Health Card as an academically credible, visually distinctive “Emergency Passport” project review.

**Architecture:** A small Python deck package owns the theme, reusable drawing primitives, verified copy, asset generation, slide builders, and presentation validation. `python-pptx` generates native editable shapes and text; QR codes and real project screenshots are inserted as assets; Keynote exports the finished deck to PDF on macOS.

**Tech Stack:** Python 3.13, `python-pptx`, `qrcode`, Pillow, pytest, Next.js project runtime for screenshots, AppleScript + Keynote for PDF export.

---

## File Map

- Create `requirements-deck.txt` — isolated presentation-generation dependencies.
- Create `deck/__init__.py` — package marker and public build API.
- Create `deck/theme.py` — exact palette, dimensions, typography, grid constants, and low-level drawing helpers.
- Create `deck/content.py` — final slide titles, evidence statements, and speaker notes.
- Create `deck/assets.py` — QR generation and product-screenshot asset validation.
- Create `deck/validation.py` — structural and visual-policy checks for the generated deck.
- Create `deck/builder.py` — slide ordering and presentation assembly.
- Create `deck/slides/__init__.py` — slide-builder package marker.
- Create `deck/slides/narrative.py` — slides 1–3: cover, problem, solution.
- Create `deck/slides/system.py` — slides 4–6: experience, architecture, security.
- Create `deck/slides/interoperability.py` — slides 7–8: standards and SOS.
- Create `deck/slides/closing.py` — slides 9–10: validation and close.
- Create `scripts/build_deck.py` — command-line entry point for the `.pptx`.
- Create `scripts/export_deck_pdf.applescript` — repeatable Keynote PDF export.
- Create `tests/test_deck.py` — slide count, content, notes, bounds, and anti-template checks.
- Create `tests/test_deck_assets.py` — QR and screenshot asset checks.
- Create `deck/assets/screenshots/` — real patient, hospital, and admin screenshots captured from the project.
- Create `deliverables/ABHA_Health_Card_Project_Deck.pptx` — final editable deck.
- Create `deliverables/ABHA_Health_Card_Project_Deck.pdf` — final review/preview PDF.
- Modify `README.md` — add a short “Project presentation” section with build and preview commands.

### Task 1: Establish the deck toolchain and regression tests

**Files:**
- Create: `requirements-deck.txt`
- Create: `deck/__init__.py`
- Create: `deck/theme.py`
- Create: `tests/test_deck.py`

- [ ] **Step 1: Add the deck dependency file**

```text
python-pptx==1.0.2
qrcode[pil]==8.0
Pillow==11.3.0
```

- [ ] **Step 2: Write the failing structural test**

Create `tests/test_deck.py` with these assertions:

```python
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

from deck.builder import build_presentation
from deck.validation import validate_presentation


EXPECTED_TITLES = [
    "At 03:12, the ambulance doesn’t need a login.",
    "Critical context arrives fragmented.",
    "One scan. The right context. Immediately.",
    "One patient. Three workspaces.",
    "Anatomy of a health card.",
    "Sealed by default. Opened by need.",
    "Native data. No translation drama.",
    "Panic → panel → people.",
    "Measured, not marketed.",
    "A health record that arrives before the ambulance does.",
]


def test_deck_has_ten_slides_with_expected_titles(tmp_path: Path) -> None:
    output = tmp_path / "deck.pptx"
    build_presentation(output)

    prs = Presentation(output)
    assert len(prs.slides) == 10
    all_text = ["\n".join(shape.text for shape in slide.shapes if hasattr(shape, "text")) for slide in prs.slides]
    for title, slide_text in zip(EXPECTED_TITLES, all_text, strict=True):
        assert title in slide_text


def test_deck_has_notes_and_no_out_of_bounds_shapes(tmp_path: Path) -> None:
    output = tmp_path / "deck.pptx"
    build_presentation(output)
    prs = Presentation(output)

    for index, slide in enumerate(prs.slides, start=1):
        assert slide.notes_slide.notes_text_frame.text.strip(), f"slide {index} missing notes"
        for shape in slide.shapes:
            assert shape.left >= 0
            assert shape.top >= 0
            assert shape.left + shape.width <= prs.slide_width + Inches(0.01)
            assert shape.top + shape.height <= prs.slide_height + Inches(0.01)


def test_deck_avoids_gradient_and_template_shapes(tmp_path: Path) -> None:
    output = tmp_path / "deck.pptx"
    build_presentation(output)
    prs = Presentation(output)
    errors = validate_presentation(prs)
    assert errors == []
```

- [ ] **Step 3: Run the test and confirm it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_deck.py -q
```

Expected: collection fails with `ModuleNotFoundError: No module named 'deck'`.

- [ ] **Step 4: Implement the theme and core primitives**

Create `deck/theme.py` with these exact constants and public helpers:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

SLIDE_W = 13.333
SLIDE_H = 7.5
MARGIN = 0.65
COLUMN_GAP = 0.18

BLACK = RGBColor(0x10, 0x15, 0x12)
BONE = RGBColor(0xEE, 0xE9, 0xDE)
BONE_2 = RGBColor(0xD8, 0xD2, 0xC4)
CORAL = RGBColor(0xFF, 0x56, 0x38)
GREEN = RGBColor(0x00, 0xA8, 0x78)
OFF_WHITE = RGBColor(0xFA, 0xF8, 0xF2)
MUTED = RGBColor(0x65, 0x70, 0x69)

DISPLAY_FONT = "Georgia"
BODY_FONT = "Arial"
MONO_FONT = "Courier New"


@dataclass(frozen=True)
class SlideFrame:
    slide: object
    index: int
    section: str
    dark: bool = False


def new_presentation() -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(SLIDE_W)
    prs.slide_height = Inches(SLIDE_H)
    return prs


def add_slide(prs: Presentation, index: int, section: str, *, dark: bool = False) -> SlideFrame:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    background = slide.background.fill
    background.solid()
    background.fore_color.rgb = BLACK if dark else BONE
    return SlideFrame(slide=slide, index=index, section=section, dark=dark)


def add_text(frame: SlideFrame, text: str, x: float, y: float, w: float, h: float, *, font: str = BODY_FONT, size: float = 18, color: RGBColor | None = None, bold: bool = False, align: PP_ALIGN = PP_ALIGN.LEFT, valign: MSO_ANCHOR = MSO_ANCHOR.TOP, margin: float = 0.0, line_spacing: float = 1.0) -> object:
    shape = frame.slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = shape.text_frame
    tf.clear()
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(margin)
    tf.vertical_anchor = valign
    tf.word_wrap = True
    paragraph = tf.paragraphs[0]
    paragraph.text = text
    paragraph.alignment = align
    paragraph.line_spacing = line_spacing
    run = paragraph.runs[0]
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color or (BONE if frame.dark else BLACK)
    return shape


def add_rect(frame: SlideFrame, x: float, y: float, w: float, h: float, *, fill: RGBColor, line: RGBColor | None = None, width: float = 0.75, radius: bool = False) -> object:
    kind = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shape = frame.slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = line or fill
    shape.line.width = Pt(width)
    if radius:
        shape.adjustments[0] = 0.08
    return shape


def add_line(frame: SlideFrame, x1: float, y1: float, x2: float, y2: float, *, color: RGBColor | None = None, width: float = 0.75) -> object:
    from pptx.enum.shapes import MSO_CONNECTOR
    shape = frame.slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    shape.line.color.rgb = color or (BONE_2 if frame.dark else BLACK)
    shape.line.width = Pt(width)
    return shape


def add_footer(frame: SlideFrame) -> None:
    ink = BONE if frame.dark else BLACK
    add_text(frame, "ABHA HEALTH CARD  /  SY1512", MARGIN, 7.13, 4.0, 0.18, size=7.5, color=ink, bold=True)
    add_text(frame, f"{frame.index:02d}", 12.25, 7.08, 0.43, 0.22, font=MONO_FONT, size=9, color=ink, align=PP_ALIGN.RIGHT)
    add_line(frame, MARGIN, 7.02, 12.68, 7.02, color=ink, width=0.5)


def set_notes(frame: SlideFrame, notes: str) -> None:
    frame.slide.notes_slide.notes_text_frame.text = notes.strip()
```

Create `deck/__init__.py`:

```python
"""ABHA Health Card presentation generator."""
```

- [ ] **Step 5: Run the test and confirm the expected missing-module failure has advanced**

Run:

```bash
.venv/bin/python -m pytest tests/test_deck.py -q
```

Expected: failure now reports that `deck.builder` or `deck.validation` does not exist.

- [ ] **Step 6: Commit the toolchain and tests**

```bash
git add requirements-deck.txt deck/__init__.py deck/theme.py tests/test_deck.py
git commit -m "test: define ABHA deck structure and visual policy"
```

### Task 2: Add verified content, asset generation, and validation

**Files:**
- Create: `deck/content.py`
- Create: `deck/assets.py`
- Create: `deck/validation.py`
- Create: `tests/test_deck_assets.py`

- [ ] **Step 1: Write failing asset tests**

```python
from pathlib import Path

from PIL import Image

from deck.assets import ensure_qr, required_screenshot


def test_ensure_qr_creates_readable_square_png(tmp_path: Path) -> None:
    output = tmp_path / "qr.png"
    ensure_qr("http://localhost:3000", output)
    with Image.open(output) as image:
        assert image.width == image.height
        assert image.width >= 512
        assert image.format == "PNG"


def test_required_screenshot_rejects_missing_file(tmp_path: Path) -> None:
    try:
        required_screenshot(tmp_path / "patient.png")
    except FileNotFoundError as exc:
        assert "patient.png" in str(exc)
    else:
        raise AssertionError("missing screenshot must raise FileNotFoundError")
```

- [ ] **Step 2: Run the asset tests and confirm failure**

Run: `.venv/bin/python -m pytest tests/test_deck_assets.py -q`

Expected: `ModuleNotFoundError: No module named 'deck.assets'`.

- [ ] **Step 3: Add final content and speaker notes**

Create `deck/content.py` with this complete content model:

```python
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
    SlideCopy(1, "OPEN", "At 03:12, the ambulance doesn’t need a login.", "A portable emergency identity that works before an account can be opened.", ("ABDM + NHCX", "AES-128-GCM trauma profile", "Offline-capable demo"), "This project turns the ABHA health card into an emergency instrument, not only a digital identity. The same patient record supports three workflows: a responder scanning a signed QR, a hospital writing standards-shaped clinical records, and an administrator tracing claims and alerts. The key design choice is that the demonstration remains reliable even when external government sandboxes are unavailable."),
    SlideCopy(2, "PROBLEM", "Critical context arrives fragmented.", "Emergency facts are split across portals, files, and workflows.", ("Separate portals", "Missing responder context", "Emergency-time penalty"), "During an emergency, the most important facts are often the hardest to retrieve. Allergies may sit in one file, medications in another, and coverage in a billing system that has not yet been contacted. A responder should not need a login, multiple tabs, or a patient’s memory to make a safe initial decision. That context gap is the problem this project is designed to remove."),
    SlideCopy(3, "SOLUTION", "One scan. The right context. Immediately.", "A signed QR resolves a minimal, verified trauma profile.", ("Signed QR token", "Blood group + allergies + conditions", "Retrieval target under 800 ms"), "The patient card contains a signed token, not sensitive medical data itself. The public scanner validates that token, verifies its integrity, decrypts the stored trauma profile, and returns a compact set of responder-critical facts. The API also measures server retrieval time so the interface can communicate latency honestly. The design target is under 800 milliseconds, with no patient identity exposed before token validation."),
    SlideCopy(4, "EXPERIENCE", "One patient. Three workspaces.", "The same identity supports purpose-built patient, hospital, and admin views.", ("Patient", "Hospital", "Admin"), "The product avoids forcing every actor into one generic dashboard. Patients manage their card, emergency profile, consent, records, and claims. Hospitals scan a patient, write records, create bills, and monitor live alerts. Administrators trace integrations, adjudicate claims, and audit SOS history. The interface changes with the role while the underlying patient identity and service-owned records remain consistent."),
    SlideCopy(5, "ARCHITECTURE", "Anatomy of a health card.", "Five focused services cooperate behind one patient-facing gateway.", ("5 FastAPI services", "Next.js frontend", "NGINX gateway", "5 SQLite databases"), "The backend is intentionally split by business capability. Identity owns authentication and consent. Records owns profiles, clinical records, encrypted trauma data, and QR tokens. ABDM maps records to HL7 FHIR v4. NHCX owns bills and claim adjudication. SOS owns live alerts and notification. Each service owns a separate SQLite database, while NGINX provides one routing boundary for the Next.js frontend."),
    SlideCopy(6, "SECURITY", "Sealed by default. Opened by need.", "The emergency path validates integrity before it decrypts anything.", ("Random 32-byte token", "HMAC-SHA256 integrity", "AES-128-GCM encryption", "Consent gate"), "The trauma profile is encrypted at rest with AES-128-GCM. Its HMAC-SHA256 signature is checked before decryption is attempted, so tampered ciphertext is rejected early. The QR carries a random, revocable token rather than medical details. Hospital access to longitudinal records is separately protected by role checks and consent artifacts, allowing consent to be revoked without changing the emergency QR profile."),
    SlideCopy(7, "INTEROPERABILITY", "Native data. No translation drama.", "Clinical events and claims use standards-shaped resources and explicit trace.", ("HL7 FHIR v4", "ABDM care contexts", "NHCX FHIR Claim", "Internally simulated gateways"), "A prescription becomes a MedicationRequest, a diagnostic report becomes a DiagnosticReport, and an itemized bill becomes a FHIR Claim. ABDM care-context links and gateway calls are recorded with endpoint, status, and latency for auditability. The ABDM and NHCX interfaces are internally simulated in this demo so the complete workflow remains deterministic and available offline; they are not presented as live government connections."),
    SlideCopy(8, "EMERGENCY", "Panic → panel → people.", "One SOS action fans out to the hospital and emergency contacts.", ("Authenticated WebSocket", "GPS coordinates", "SMTP contact email"), "Pressing Panic creates one alert and broadcasts it to authenticated hospital dashboards over WebSocket. The event includes patient identity and location coordinates. Registered contacts are then notified by email when SMTP is configured. Email failure never blocks the live alert; the service records a skipped or failed email status while the hospital feed continues to work. This keeps the emergency path resilient to a mail-provider outage."),
    SlideCopy(9, "EVIDENCE", "Measured, not marketed.", "The repository demonstrates a working vertical slice with automated checks.", ("19 automated tests", "16-step E2E scenario", "5 services", "One-command Docker startup"), "The project is backed by 19 automated service tests and a 16-step end-to-end scenario covering authentication, scanning, records, billing, claims, and SOS. Docker Compose starts the frontend, gateway, and five services from one command, with seeded data for a repeatable demo. We also state the boundaries clearly: government gateways are simulated, production hardening is out of scope, and SMTP remains optional for the demo."),
    SlideCopy(10, "CLOSE", "A health record that arrives before the ambulance does.", "The 60-second proof connects identity, emergency access, clinical records, claims, and alerts.", ("Open card", "Scan QR", "Write FHIR", "Push claim", "Trigger SOS"), "The complete proof is intentionally short: open the patient card, scan its QR, write a FHIR-backed record, push an itemized claim, and trigger the live SOS feed. The next production steps are a PostgreSQL deployment, approval for real ABDM and NHCX sandbox credentials, stronger observability, and a controlled clinical pilot. The core contribution is already demonstrable as one connected, offline-capable system."),
)
```

All evidence strings are repository-faithful: they use implemented technologies and measured repository checks, not claims of production interoperability or clinical efficacy.

- [ ] **Step 4: Implement QR generation and screenshot validation**

```python
from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_H


def ensure_qr(url: str, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_H, box_size=12, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    qr.make_image(fill_color="#101512", back_color="#FAF8F2").save(output)
    return output


def required_screenshot(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Required project screenshot is missing: {path}")
    return path
```

- [ ] **Step 5: Implement validation**

Implement `deck/validation.py` as a non-mutating validator:

```python
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Inches

from deck.content import SLIDES


def validate_presentation(prs: Presentation) -> list[str]:
    errors: list[str] = []
    slides = list(prs.slides)
    if len(slides) != 10:
        errors.append(f"expected 10 slides, found {len(slides)}")

    tolerance = Inches(0.01)
    rounded_rectangles = 0

    for index, slide in enumerate(slides, start=1):
        texts = [shape.text for shape in slide.shapes if hasattr(shape, "text")]
        if index <= len(SLIDES) and SLIDES[index - 1].title not in texts:
            errors.append(f"slide {index}: missing approved title")

        notes = slide.notes_slide.notes_text_frame.text.strip()
        if not notes:
            errors.append(f"slide {index}: missing speaker notes")

        slide_xml = slide._element.xml
        if "<a:gradFill" in slide_xml:
            errors.append(f"slide {index}: gradient fill is not allowed")
        rounded_rectangles += slide_xml.count('prst="roundRect"')

        for shape in slide.shapes:
            if shape.left < -tolerance or shape.top < -tolerance:
                errors.append(f"slide {index}: shape starts outside the canvas")
            if shape.left + shape.width > prs.slide_width + tolerance:
                errors.append(f"slide {index}: shape exceeds the right canvas edge")
            if shape.top + shape.height > prs.slide_height + tolerance:
                errors.append(f"slide {index}: shape exceeds the bottom canvas edge")

        if index in (4, 8):
            pictures = sum(shape.shape_type == MSO_SHAPE_TYPE.PICTURE for shape in slide.shapes)
            if pictures == 0:
                errors.append(f"slide {index}: required project screenshot is missing")

    if rounded_rectangles > 4:
        errors.append(f"expected at most 4 rounded rectangles, found {rounded_rectangles}")
    return errors
```

This returns human-readable errors for slide count, missing titles or notes, out-of-bounds shapes, gradients, excessive rounded rectangles, and missing product screenshots. It never mutates the presentation.

- [ ] **Step 6: Run the asset tests**

Run: `.venv/bin/python -m pytest tests/test_deck_assets.py -q`

Expected: 2 tests pass.

- [ ] **Step 7: Commit**

```bash
git add deck/content.py deck/assets.py deck/validation.py tests/test_deck_assets.py
git commit -m "feat: add deck content assets and validation"
```

### Task 3: Build the narrative slides (1–3)

**Files:**
- Create: `deck/slides/__init__.py`
- Create: `deck/slides/narrative.py`
- Modify: `deck/builder.py`

- [ ] **Step 1: Implement slide 1 — cover**

Create `build_cover(prs)` using native shapes:

- full graphite background;
- 17% coral rescue spine on the left;
- large Georgia title on the left-center;
- an oversized black patient card rotated 4–6° on the right, with ABHA ID, name, blood group, allergy count, and a generated QR;
- group and institution footer;
- exact approved title.

The QR must be generated from `http://localhost:3000/scan` and inserted as an image. The patient card is the only rounded rectangle on this slide.

- [ ] **Step 2: Implement slide 2 — problem**

Create `build_problem(prs)`:

- 03:12 displayed as a 72–90 point Georgia figure;
- four detached fact strips for allergies, medications, conditions, and coverage;
- a vertical coral “context gap” marker;
- one concise consequence line: “The responder gets a login screen while the patient gets an emergency.”

- [ ] **Step 3: Implement slide 3 — solution**

Create `build_solution(prs)`:

- large QR at left with a coral scan line;
- title at right;
- a four-cell clinical strip for blood group, allergies, conditions, and retrieval target;
- monospace labels for `HMAC VERIFY`, `AES-GCM OPEN`, and `CONSENT GATE`.

- [ ] **Step 4: Wire slides 1–3 into the builder**

`deck/builder.py` must expose:

```python
def build_presentation(output: Path) -> Path:
    prs = new_presentation()
    for builder in (build_cover, build_problem, build_solution):
        builder(prs)
    output.parent.mkdir(parents=True, exist_ok=True)
    prs.save(output)
    return output
```

Temporary builder version may contain only three slides while this task is in progress; add the remaining builders in Tasks 4–6.

- [ ] **Step 5: Run structural tests**

Run: `.venv/bin/python -m pytest tests/test_deck.py -q`

Expected: the slide-count assertion fails at 3, while title and no-gradient assertions reach their intended checks.

- [ ] **Step 6: Commit**

```bash
git add deck/builder.py deck/slides/__init__.py deck/slides/narrative.py
git commit -m "feat: build cover problem and solution slides"
```

### Task 4: Build experience, architecture, and security slides (4–6)

**Files:**
- Create: `deck/slides/system.py`
- Modify: `deck/builder.py`

- [ ] **Step 1: Capture real project screenshots**

Start the five services and frontend in the worktree, sign in with seeded demo accounts, and capture these routes:

- `deck/assets/screenshots/patient.png` — patient card and emergency profile area;
- `deck/assets/screenshots/hospital.png` — hospital dashboard/SOS workspace;
- `deck/assets/screenshots/admin.png` — admin ABDM trace/claims area.

Use clean viewport dimensions of at least 1440×900. Crop only browser chrome; do not include credentials, tokens, or local personal paths in the visible capture.

- [ ] **Step 2: Implement slide 4 — experience**

Create `build_experience(prs)`:

- three unequal editorial lanes for Patient, Hospital, and Admin;
- actual screenshots placed with square crops and thin black borders;
- labels `CARRY IT`, `USE IT`, `AUDIT IT`;
- a single coral route line connecting the three roles.

- [ ] **Step 3: Implement slide 5 — architecture**

Create `build_architecture(prs)`:

- stacked service layers for Identity, Records, ABDM, NHCX, and SOS;
- each layer shows responsibility and its database file;
- a vertical coral “ONE PATIENT VIEW” block;
- Next.js frontend and NGINX gateway shown above the service stack.

- [ ] **Step 4: Implement slide 6 — security**

Create `build_security(prs)`:

- a large outlined coral seal with a native lock shape;
- four-step horizontal chain: token → HMAC → AES-GCM → consent;
- explicit copy that the HMAC check occurs before decryption;
- a small “tamper = reject” stamp.

- [ ] **Step 5: Wire slides 4–6 and add real screenshots**

Update the builder order to:

```python
for builder in (
    build_cover,
    build_problem,
    build_solution,
    build_experience,
    build_architecture,
    build_security,
):
    builder(prs)
```

- [ ] **Step 6: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_deck.py tests/test_deck_assets.py -q
```

Expected: asset tests pass; slide-count assertion advances to 6.

- [ ] **Step 7: Commit**

```bash
git add deck/assets/screenshots deck/builder.py deck/slides/system.py
git commit -m "feat: add product experience architecture and security slides"
```

### Task 5: Build interoperability and SOS slides (7–8)

**Files:**
- Create: `deck/slides/interoperability.py`
- Modify: `deck/builder.py`

- [ ] **Step 1: Implement slide 7 — interoperability**

Create `build_interoperability(prs)` with:

- left-side ABDM/FHIR/NHCX “ports”;
- a dark MedicationRequest receipt with exact repository-style fields;
- a right-side integration trace using the repository’s seeded rows: `/v1/registration/health-id/generate` (200, 141 ms), `/v1/hip/link/care-context` (200, 96 ms), and `/v1/consent-requests/init` (200, 187 ms);
- a coral qualifier: “Real-shaped interfaces · internally simulated for an offline demo.”

- [ ] **Step 2: Implement slide 8 — emergency coordination**

Create `build_sos(prs)`:

- graphite background;
- a large coral pulse ring at left;
- two outgoing branches to “Hospital feed” and “Emergency contacts”;
- a real hospital screenshot on the right, cropped to emphasize the live SOS panel;
- small labels for WebSocket, GPS, and SMTP.

- [ ] **Step 3: Wire slides 7–8**

Append `build_interoperability` and `build_sos` to the builder tuple.

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/test_deck.py -q`

Expected: slide-count assertion advances to 8.

- [ ] **Step 5: Commit**

```bash
git add deck/builder.py deck/slides/interoperability.py
git commit -m "feat: add interoperability and live SOS slides"
```

### Task 6: Build evidence and close slides (9–10)

**Files:**
- Create: `deck/slides/closing.py`
- Modify: `deck/builder.py`

- [ ] **Step 1: Verify the evidence numbers**

Run:

```bash
.venv/bin/python -m pytest services/identity/tests services/records/tests services/abdm/tests services/nhcx/tests services/sos/tests -q
```

Expected: 19 tests pass.

Run the repository E2E script while the five services are active and record whether all 16 steps pass. If the live E2E cannot run, the deck must say “16-step E2E scenario implemented” rather than “16/16 passing.”

- [ ] **Step 2: Implement slide 9 — evidence**

Create `build_evidence(prs)`:

- four ledger cells for 5 services, 19 automated tests, 16 E2E steps, and 1-command startup;
- a green circular `PASS` stamp only if the corresponding check passed;
- an honest limitations strip: simulated government gateways, no production hardening, SMTP optional;
- a small future-work line: production database, real sandbox credentials, stronger observability.

- [ ] **Step 3: Implement slide 10 — close**

Create `build_close(prs)`:

- black card occupying most of the canvas;
- exact closing title;
- five-step route with numbers and verbs;
- actual QR to `http://localhost:3000`;
- institution and group details;
- a small next-step strip covering production database, real sandbox approval, and pilot deployment.

- [ ] **Step 4: Wire all ten slides and add notes**

The final builder order must be:

```python
BUILDERS = (
    build_cover,
    build_problem,
    build_solution,
    build_experience,
    build_architecture,
    build_security,
    build_interoperability,
    build_sos,
    build_evidence,
    build_close,
)
```

Each builder must call `set_notes` using the notes from `deck/content.py`.

- [ ] **Step 5: Run all deck tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_deck.py tests/test_deck_assets.py -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add deck/builder.py deck/slides/closing.py
git commit -m "feat: complete evidence and closing slides"
```

### Task 7: Generate the deliverables and PDF preview

**Files:**
- Create: `scripts/build_deck.py`
- Create: `scripts/export_deck_pdf.applescript`
- Create: `deliverables/ABHA_Health_Card_Project_Deck.pptx`
- Create: `deliverables/ABHA_Health_Card_Project_Deck.pdf`

- [ ] **Step 1: Add the CLI entry point**

`scripts/build_deck.py` must accept `--output`, default to `deliverables/ABHA_Health_Card_Project_Deck.pptx`, build the deck, validate it, and exit nonzero on validation errors.

Expected output:

```text
Built 10 slides: deliverables/ABHA_Health_Card_Project_Deck.pptx
Validation: OK
```

- [ ] **Step 2: Build the PowerPoint**

Run:

```bash
.venv/bin/python scripts/build_deck.py
```

Expected: a non-empty `.pptx` file and the two success lines above.

- [ ] **Step 3: Add repeatable Keynote PDF export**

`scripts/export_deck_pdf.applescript` must accept the PPTX and PDF paths, open the deck in Keynote, export it as PDF, close the document, and quit Keynote only if Keynote was not already running.

- [ ] **Step 4: Export and inspect the PDF**

Run:

```bash
osascript scripts/export_deck_pdf.applescript \
  "$PWD/deliverables/ABHA_Health_Card_Project_Deck.pptx" \
  "$PWD/deliverables/ABHA_Health_Card_Project_Deck.pdf"
```

Expected: the PDF contains 10 pages. Render every page to PNG using Preview/Quartz or `qlmanage`, and inspect each page for clipping, overlap, inconsistent alignment, and missing screenshots.

- [ ] **Step 5: Verify slide count and notes in the final file**

Run:

```bash
.venv/bin/python - <<'PY'
from pptx import Presentation
p = Presentation('deliverables/ABHA_Health_Card_Project_Deck.pptx')
print('slides', len(p.slides))
print('notes', sum(bool(s.notes_slide.notes_text_frame.text.strip()) for s in p.slides))
PY
```

Expected:

```text
slides 10
notes 10
```

- [ ] **Step 6: Commit**

```bash
git add scripts/build_deck.py scripts/export_deck_pdf.applescript deliverables
 git commit -m "build: generate ABHA project deck and PDF preview"
```

### Task 8: Document and perform final verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add a concise presentation section**

Document:

```bash
python3.13 -m venv .venv
.venv/bin/pip install -r requirements-deck.txt
.venv/bin/python scripts/build_deck.py
osascript scripts/export_deck_pdf.applescript \
  "$PWD/deliverables/ABHA_Health_Card_Project_Deck.pptx" \
  "$PWD/deliverables/ABHA_Health_Card_Project_Deck.pdf"
```

List both output paths and state that the PPTX contains editable shapes and speaker notes.

- [ ] **Step 2: Run the complete verification suite**

Run:

```bash
.venv/bin/python -m pytest tests/test_deck.py tests/test_deck_assets.py services/identity/tests services/records/tests services/abdm/tests services/nhcx/tests services/sos/tests -q
```

Expected: all application and deck tests pass.

- [ ] **Step 3: Inspect repository cleanliness and deliverables**

Run:

```bash
git diff --check
git status --short
ls -lh deliverables/ABHA_Health_Card_Project_Deck.pptx deliverables/ABHA_Health_Card_Project_Deck.pdf
```

Expected: no whitespace errors; only intentional files are changed; both deliverables are non-empty.

- [ ] **Step 4: Commit documentation**

```bash
git add README.md
 git commit -m "docs: explain how to build the project presentation"
```

- [ ] **Step 5: Final commit summary**

Run:

```bash
git log --oneline --decorate -10
```

Confirm the deck toolchain, slides, deliverables, and documentation are each represented by focused commits.
