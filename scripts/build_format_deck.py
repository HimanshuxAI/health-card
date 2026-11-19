#!/usr/bin/env python3
"""Duplicate the required presentation template and fill it with the ABHA Health Card content.

Only slide content (text and the placeholder images that belong to the old project) is
replaced. Footer text boxes, MIT logo pictures, slide-number placeholders, slide master,
layouts and theme are left exactly as they are in the supplied template.
"""

from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

TEMPLATE = Path("/Users/himanshu/Downloads/Final_Project_Presentation_format.pptx")
OUTPUT = Path("/Users/himanshu/Downloads/Final_Project_Presentation_ABHA_Health_Card.pptx")
REPO = Path("/Users/himanshu/Documents/health_card")

NAVY = RGBColor(0x07, 0x37, 0x63)


def find(slide, name):
    for shape in slide.shapes:
        if shape.name == name:
            return shape
    raise KeyError(f"Shape not found: {name}")


def font_snapshot(shape):
    for para in shape.text_frame.paragraphs:
        for run in para.runs:
            if run.text.strip():
                f = run.font
                color = None
                try:
                    if f.color.type is not None and f.color.rgb is not None:
                        color = f.color.rgb
                except (AttributeError, TypeError):
                    pass
                return {
                    "name": f.name,
                    "size": f.size,
                    "bold": f.bold,
                    "italic": f.italic,
                    "color": color,
                }
    return {}


def apply(run, style, *, size=None, name=None, bold=None, color=None):
    f = run.font
    f.name = name if name is not None else style.get("name")
    f.size = size if size is not None else style.get("size")
    f.bold = bold if bold is not None else style.get("bold")
    f.italic = style.get("italic")
    c = color if color is not None else style.get("color")
    if c is not None:
        f.color.rgb = c


def set_text(shape, lines, *, size=None, name=None, bold=None, color=None, spacing=None,
             bold_first=False):
    """Replace a shape's text while retaining its original run formatting."""
    style = font_snapshot(shape)
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    for i, line in enumerate(lines):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.level = 0
        run = para.add_run()
        run.text = line
        line_bold = True if (bold_first and i == 0) else (False if bold_first else bold)
        apply(run, style, size=size, name=name, bold=line_bold, color=color)
        if spacing is not None:
            para.space_after = Pt(spacing)
    return shape


def set_editorial(shape, headline, items, *, size=14, head_size=17, spacing=8):
    """Editorial layout inside an existing text box: takeaway line + labelled items.

    No new shapes are added; the template's geometry, palette and footer stay intact.
    """
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.space_after = Pt(spacing + 4)
    r = p.add_run()
    r.text = headline
    r.font.name = "Times New Roman"
    r.font.size = Pt(head_size)
    r.font.bold = True
    r.font.color.rgb = NAVY

    for item in items:
        p = tf.add_paragraph()
        p.space_after = Pt(spacing)
        if " — " in item:
            lead, rest = item.split(" — ", 1)
            r1 = p.add_run()
            r1.text = lead + " — "
            r1.font.name = "Times New Roman"
            r1.font.size = Pt(size)
            r1.font.bold = True
            r1.font.color.rgb = NAVY
            r2 = p.add_run()
            r2.text = rest
            r2.font.name = "Times New Roman"
            r2.font.size = Pt(size)
            r2.font.bold = False
            r2.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
        else:
            r = p.add_run()
            r.text = item
            r.font.name = "Times New Roman"
            r.font.size = Pt(size)
            r.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
    return shape


def set_items(shape, items, *, size=14, spacing=8):
    """Labelled items in an existing box, with navy bold lead-ins and black detail."""
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(spacing)
        lead, rest = item.split(" — ", 1) if " — " in item else (item, "")
        r1 = p.add_run()
        r1.text = lead + (" — " if rest else "")
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(size)
        r1.font.bold = bool(rest)
        r1.font.color.rgb = NAVY if rest else RGBColor(0x00, 0x00, 0x00)
        if rest:
            r2 = p.add_run()
            r2.text = rest
            r2.font.name = "Times New Roman"
            r2.font.size = Pt(size)
            r2.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
    return shape


def set_first_run(shape, text):
    """Replace only the leading run of a heading, leaving its exact formatting intact."""
    runs = [r for p in shape.text_frame.paragraphs for r in p.runs]
    if not runs:
        shape.text_frame.text = text
        return
    runs[0].text = text
    for run in runs[1:]:
        run.text = ""


def set_cell(cell, text):
    """Set a table cell to one clean paragraph, keeping its original run style."""
    style = font_snapshot(cell)
    tf = cell.text_frame
    tf.clear()
    tf.word_wrap = True
    run = tf.paragraphs[0].add_run()
    run.text = text
    apply(run, style)


def add_pic(slide, image, *, left, top, width):
    return slide.shapes.add_picture(str(image), Inches(left), Inches(top), width=Inches(width))


def delete_shape(slide, name):
    shape = find(slide, name)
    shape._element.getparent().remove(shape._element)


def replace_picture(slide, old_name, image, *, left, top, width=None, height=None):
    old = find(slide, old_name)
    left = old.left if left is None else left
    top = old.top if top is None else top
    old._element.getparent().remove(old._element)
    kwargs = {}
    if width is not None:
        kwargs["width"] = width
    if height is not None:
        kwargs["height"] = height
    return slide.shapes.add_picture(str(image), left, top, **kwargs)


def build():
    prs = Presentation(TEMPLATE)
    slides = prs.slides

    # Renumber section titles to match this deck's outline (the template carried
    # numbering from the unrelated project it came with).
    headings = [
        (2, "Google Shape;66;p4", "01. Introduction"),
        (3, "Google Shape;76;p6", "02. Problem Statement & Objectives"),
        (4, "Google Shape;87;p8", "03. Concepts and Methods"),
        (5, "Google Shape;100;p9", "04. Literature Survey"),
        (6, "Google Shape;112;p7", "05. Identification of Gaps & Scope of Work"),
        (7, "Google Shape;118;p12", "06. Implementation"),
        (8, "Google Shape;126;p13", "07. Results & Measured Outputs"),
        (9, "Google Shape;135;p14", "08. Conclusion & Future Work"),
        (10, "Google Shape;144;g5cc8714c89_2_35", "09. References"),
        (13, "Google Shape;169;p11", "10. Process & Architecture"),
        (14, "Google Shape;178;p10", "11. Tools & Languages"),
    ]
    for slide_no, shape_name, title in headings:
        set_first_run(find(slides[slide_no], shape_name), title)
    # "References" uses a much narrower, larger heading than the other sections.
    ref_heading = find(slides[10], "Google Shape;144;g5cc8714c89_2_35")
    ref_heading.width = Inches(5.2)
    for para in ref_heading.text_frame.paragraphs:
        for run in para.runs:
            run.font.size = Pt(28)

    # 1 — Cover
    s = slides[0]
    set_first_run(find(s, "Google Shape;48;p2"), "ABHA Health Card")
    set_text(
        find(s, "Google Shape;49;p2"),
        [
            "Group SY1512",
            "School of Computing, MIT-ADT University",
            "B.Tech Computer Science & Engineering",
            "",
            "A portable emergency identity that works before a responder login.",
            "ABDM + NHCX · AES-128-GCM trauma profile · Offline-capable demo",
        ],
        size=Pt(16),
        name="Times New Roman",
        bold=True,
    )

    # 2 — Outline
    s = slides[1]
    set_text(
        find(s, "Google Shape;60;g5cc8714c89_0_4"),
        [
            "Introduction",
            "Problem Statement & Objectives",
            "Concepts & Methods",
            "Literature Survey",
            "Identification of Gaps & Scope of Work",
            "Implementation",
            "Results & Measured Outputs",
            "Conclusion & Future Work",
            "References",
            "Process & Architecture",
            "Tools & Languages",
            "Q&A",
        ],
        size=Pt(18),
        name="Times New Roman",
    )

    # 3 — Introduction
    s = slides[2]
    intro_body = find(s, "Google Shape;69;p4")
    intro_body.height = Inches(1.8)
    set_text(
        find(s, "Google Shape;69;p4"),
        [
            "03:12. An unconscious patient cannot approve an OTP. A responder needs blood group, "
            "allergies and contacts — before any login screen appears.",
            "ABDM supplies identity, consent and FHIR. The missing piece is the emergency path: a "
            "signed QR token that resolves to a minimal verified trauma profile.",
            "Encrypted at rest · offline-capable demo · no government sandbox dependency.",
        ],
        size=Pt(15),
        name="Times New Roman",
        spacing=5,
    )
    # Real product screenshot replaces the old project's generic diagram.
    replace_picture(
        s,
        "Google Shape;70;p4",
        REPO / "docs/deck_assets/patient_card.png",
        left=Inches(1.7),
        top=Inches(2.75),
        width=Inches(6.1),
    )

    # 4 — Problem Statement and Objectives
    s = slides[3]
    set_editorial(
        find(s, "Google Shape;79;p6"),
        "Critical context arrives fragmented.",
        [
            "03:12 / ALLERGIES — hidden in a patient file.",
            "MEDICATIONS — stored in a separate list.",
            "CONDITIONS — buried in clinical history.",
            "COVERAGE — held by the billing system.",
        ],
        size=18,
        head_size=24,
        spacing=8,
    )
    set_items(
        find(s, "Google Shape;80;p6"),
        [
            "The responder gets a login screen while the patient gets an emergency. One ABHA-linked "
            "identity closes that gap."
        ],
        size=18,
        spacing=8,
    )

    # 5 — Concepts and Methods
    s = slides[4]
    set_items(
        find(s, "Google Shape;90;p8"),
        [
            "1. Concept — One card, opaque token, verified trauma profile.",
            "Seal — AES-128-GCM + HMAC-SHA256 over ciphertext + tag.",
            "Resolver — Signed token → minimum trauma profile.",
        ],
        size=18,
        spacing=8,
    )
    set_items(
        find(s, "Google Shape;91;p8"),
        [
            "2. Clinical — Prescription → MedicationRequest; report → DiagnosticReport.",
            "Trace — Endpoint, status and latency logged.",
            "Link — ABHA identifier → care context.",
        ],
        size=18,
        spacing=8,
    )
    c1 = find(s, "Google Shape;90;p8")
    c1.top = Inches(0.66); c1.height = Inches(1.85)
    c2 = find(s, "Google Shape;91;p8")
    c2.top = Inches(2.55); c2.height = Inches(1.85)
    c3 = find(s, "Google Shape;92;p8")
    c3.top = Inches(4.35); c3.height = Inches(1.9)
    set_items(
        c3,
        [
            "3. Claims — Bill → FHIR Claim → adjudication states.",
            "SOS — WebSocket + GPS + SMTP; failure never blocks.",
            "Evidence — 24 tests, E2E workflow, 1,000 requests.",
        ],
        size=18,
        spacing=8,
    )
    # The template's two TRL diagrams belong to the old project and are too small to
    # read here; remove them so the three concept blocks stay legible.
    delete_shape(s, "Google Shape;93;p8")
    delete_shape(s, "Google Shape;94;p8")
    add_pic(s, REPO / "docs/deck_assets/demo_qr.png", left=7.05, top=1.15, width=1.95)
    qr_note = s.shapes.add_textbox(Inches(6.7), Inches(3.3), Inches(2.6), Inches(0.9))
    set_text(
        qr_note,
        ["OPAQUE TOKEN", "SCAN TO RESOLVE"],
        size=Pt(13),
        name="Times New Roman",
        bold=True,
        color=NAVY,
        spacing=4,
    )

    # 6 — Literature Survey (keep the template's 4x4 table)
    s = slides[5]
    table = find(s, "Google Shape;103;p9").table
    rows = [
        [
            "Sr. no",
            "Literature Title",
            "Author",
            "Findings",
        ],
        [
            "1.",
            "The Ayushman Bharat Digital Mission (ABDM): making of India's Digital Health Story",
            "Sharma et al., 2023",
            "Public digital infrastructure for identity and consent; value depends on provider use.",
        ],
        [
            "2.",
            "HL7 FHIR Release 4, version 4.0.1",
            "HL7 International, 2019",
            "Standard clinical resources used for MedicationRequest, DiagnosticReport and Claim.",
        ],
        [
            "3.",
            "QR Code Identity Tag system for Healthcare in Turkey",
            "Uzun & Bilgin, 2016",
            "QR enables fast identification; this project adds a sealed, backend-resolved profile.",
        ],
    ]
    for r, row in enumerate(rows):
        for c, text in enumerate(row):
            set_cell(table.cell(r, c), text)
    # The template's table frame (3.28 in) does not match its internal grid (9.45 in).
    # PowerPoint uses the grid, so align both to a readable full-width table.
    tbl_shape = find(s, "Google Shape;103;p9")
    tbl_shape.left = Inches(0.27)
    tbl_shape.top = Inches(0.95)
    tbl_shape.width = Inches(9.46)
    tbl_shape.height = Inches(4.35)
    for col, w in zip(table.columns, [0.55, 3.35, 1.8, 3.76]):
        col.width = Inches(w)
    for row, h in zip(table.rows, [0.42, 1.31, 1.31, 1.31]):
        row.height = Inches(h)
    for r, row in enumerate(table.rows):
        for cell in row.cells:
            cell.margin_left = Inches(0.06)
            cell.margin_right = Inches(0.06)
            cell.margin_top = Inches(0.04)
            cell.margin_bottom = Inches(0.04)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            for para in cell.text_frame.paragraphs:
                para.alignment = PP_ALIGN.LEFT
                p_pr = para._p.get_or_add_pPr()
                p_pr.set("marL", "0")
                p_pr.set("indent", "0")
                for child in list(p_pr):
                    if etree.QName(child).localname.startswith("bu"):
                        p_pr.remove(child)
                etree.SubElement(
                    p_pr, "{http://schemas.openxmlformats.org/drawingml/2006/main}buNone"
                )
                for run in para.runs:
                    run.font.name = "Calibri"
                    run.font.size = Pt(11 if r == 0 else 10)
                    run.font.bold = r == 0

    # 7 — Identification of gaps and scope of work
    s = slides[6]
    gaps_body = find(s, "Google Shape;111;p7")
    # The template places this body box under the title; move it below the heading.
    gaps_body.top = Inches(0.95)
    gaps_body.height = Inches(4.6)
    set_editorial(
        gaps_body,
        "The responder gets a login screen while the patient gets an emergency.",
        [
            "1) QR tags carry no sealed trauma profile and no token rotation.",
            "2) Mobile records need a device, a network and patient interaction.",
            "3) Allergies, conditions and coverage sit in separate systems.",
            "4) Claims are prepared by hand, outside the clinical workflow.",
            "5) Encrypted-record research stops at the primitive — no end-to-end audit.",
            "6) Few prototypes publish measured emergency-retrieval results.",
        ],
        size=18,
        head_size=24,
        spacing=8,
    )

    # 8 — Implementation (template slide has no body shape; add one in the same content area)
    s = slides[7]
    box = s.shapes.add_textbox(Inches(0.54), Inches(1.05), Inches(5.0), Inches(5.5))
    set_editorial(
        box,
        "Anatomy of a health card.",
        [
            "Next.js frontend → NGINX gateway → five FastAPI services.",
            "PORTS — 8001 identity · 8002 records · 8003 ABDM · 8004 NHCX · 8005 SOS.",
            "EMERGENCY — token → resolver → HMAC verify → AES-GCM open.",
            "HOSPITAL — JWT + role + active consent artifact.",
            "CLAIMS — bill → FHIR Claim → ADJUDICATED → APPROVED / REJECTED.",
            "SOS — alert → WebSocket → GPS + SMTP (EMAIL_SKIPPED on failure).",
            "RUN — docker compose up --build; seeded on first boot.",
        ],
        size=16,
        head_size=23,
        spacing=8,
    )
    add_pic(s, REPO / "docs/deck_assets/hospital_dashboard.png", left=5.8, top=1.15, width=3.8)
    add_pic(s, REPO / "docs/deck_assets/hospital_sos.png", left=5.8, top=3.0, width=3.8)

    # 9 — Results
    s = slides[8]
    results_body = find(s, "Google Shape;128;p13")
    results_body.width = Inches(5.0)
    set_editorial(
        results_body,
        "24 tests · 1,000 requests · 0.644 ms median",
        [
            "$ pytest services/*/tests -q → 24 passed",
            "$ python scripts/e2e.py → ALL PASS",
            "1,000 × HTTP 200 · p95 0.743 ms · max 1.908 ms",
            "Tampered HMAC → rejected · rotated token → 410",
            "BOUNDARY — Simulated gateways; no clinical validation.",
        ],
        size=18,
        head_size=24,
        spacing=10,
    )
    add_pic(s, REPO / "docs/deck_assets/admin_trace.png", left=5.8, top=1.35, width=3.8)
    trace_note = s.shapes.add_textbox(Inches(5.8), Inches(2.85), Inches(3.8), Inches(0.6))
    set_text(
        trace_note,
        ["ADMIN TRACE / EVERY GATEWAY CALL"],
        size=Pt(12),
        name="Times New Roman",
        bold=True,
        color=NAVY,
    )

    # 10 — Conclusion and Future Work
    s = slides[9]
    set_editorial(
        find(s, "Google Shape;138;p14"),
        "A health record that arrives before the ambulance does.",
        [
            "BUILT — Emergency QR, FHIR R4 records, NHCX-shaped claims and SOS in one system.",
            "LIMITS — Simulated gateways; no clinical validation; not production hardened.",
            "NEXT — Offline cached profiles with staleness flags; real sandbox conformance.",
            "NEXT — Managed key rotation; responder audit logs; degraded-network tests.",
            "NEXT — Usability studies with emergency clinicians and representative patients.",
        ],
        size=18,
        head_size=24,
        spacing=10,
    )

    # 11 — References
    s = slides[10]
    set_text(
        find(s, "Google Shape;143;g5cc8714c89_2_35"),
        [
            "[1] R. S. Sharma, A. Rohatgi, S. Jain, and D. Singh, \"The Ayushman Bharat Digital "
            "Mission (ABDM): making of India's Digital Health Story,\" CSI Transactions on ICT, "
            "vol. 11, no. 1, pp. 3-9, 2023.",
            "[2] U. S. Mishra, S. Yadav, and W. Joe, \"The ABDM of India: An assessment,\" Health "
            "Systems & Reform, vol. 10, no. 2, 2024.",
            "[3] National Resource Center for EHR Standards, FHIR Implementation Guide for ABDM, "
            "version 6.5.0, 2025.",
            "[4] National Health Authority, NHCX Developer Documentation: Claim Settlement, "
            "version 1, 2026.",
            "[5] Health Level Seven International, HL7 FHIR Release 4, version 4.0.1, 2019.",
            "[6] V. Uzun and S. Bilgin, \"Evaluation and implementation of QR Code Identity Tag "
            "system for Healthcare in Turkey,\" SpringerPlus, vol. 5, art. 1454, 2016.",
        ],
        size=Pt(12),
        name="Times New Roman",
        spacing=8,
    )

    # 12 / 13 — Thank You and Questions keep their template text.

    # 14 — Process and Architecture
    s = slides[13]
    set_editorial(
        find(s, "Google Shape;172;p11"),
        "How it was built.",
        [
            "01 / REQUIREMENTS — Synopsis, scope, non-goals; five service boundaries.",
            "02 / DESIGN — Data model, API contract, threat boundaries; one SQLite file per service.",
            "03 / BUILD — Identity, records, ABDM/FHIR, NHCX, SOS; Next.js frontend.",
            "04 / TEST — 24 service tests, end-to-end workflow, 1,000-request benchmark.",
            "05 / SHIP — Docker Compose, GitHub Actions, Render demo; seed on first boot.",
        ],
        size=18,
        head_size=24,
        spacing=10,
    )

    # 15 — Tools and Languages
    s = slides[14]
    set_editorial(
        find(s, "Google Shape;181;p10"),
        "Tools & languages.",
        [
            "PYTHON 3 — FastAPI, SQLAlchemy, Pydantic, bcrypt, PyJWT, pycryptodome, httpx.",
            "NEXT.JS — App Router, TypeScript, Tailwind CSS, Lucide icons.",
            "NGINX — Routing, rate limiting, WebSocket upgrade.",
            "SQLITE — One database file per service.",
            "HL7 FHIR R4 — MedicationRequest, DiagnosticReport, Claim bundles.",
            "PYTEST / VITEST / HTTPX — Service and end-to-end checks.",
            "DOCKER / GITHUB ACTIONS / RENDER — Compose, CI and the live demo.",
        ],
        size=18,
        head_size=24,
        spacing=9,
    )

    prs.save(OUTPUT)
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    build()
