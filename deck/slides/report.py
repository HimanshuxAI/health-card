from __future__ import annotations

from pathlib import Path

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR
from pptx.presentation import Presentation
from pptx.shapes.base import BaseShape
from pptx.text.text import _Run
from pptx.util import Inches, Pt

from deck.assets import required_screenshot
from deck.content import SLIDES
from deck.theme import (
    BLACK,
    BONE,
    BONE_2,
    CORAL,
    DISPLAY_FONT,
    GREEN,
    MONO_FONT,
    MUTED,
    OFF_WHITE,
    SlideFrame,
    add_footer,
    add_line,
    add_rect,
    add_slide,
    add_text,
    set_notes,
)


HOSPITAL_SOS_SCREENSHOT = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "screenshots"
    / "hospital_sos.png"
)


def _style_run(
    run: _Run, *, font: str, size: float, color: RGBColor, bold: bool = False
) -> None:
    run.font.name = font
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold


def _add_outline_rect(
    frame: SlideFrame,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    color: RGBColor,
    width: float,
) -> BaseShape:
    """Add an unfilled square-corner rectangle used as a thin frame."""
    shape = frame.slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.fill.background()
    shape.line.color.rgb = color
    shape.line.width = Pt(width)
    return shape


def _add_mapping_row(
    frame: SlideFrame,
    *,
    x: float,
    y: float,
    w: float,
    source: str,
    target: str,
) -> BaseShape:
    """Add one mapping row whose full text is ``SOURCE -> TARGET``."""
    shape = add_text(
        frame,
        source + " -> " + target,
        x,
        y,
        w,
        0.34,
        font=MONO_FONT,
        size=12,
        color=BLACK,
    )
    paragraph = shape.text_frame.paragraphs[0]
    paragraph.clear()
    source_run = paragraph.add_run()
    source_run.text = source + " "
    _style_run(source_run, font=MONO_FONT, size=12, color=BLACK, bold=True)
    target_run = paragraph.add_run()
    target_run.text = "-> " + target
    _style_run(target_run, font=MONO_FONT, size=12, color=CORAL, bold=True)
    return shape


def build_interoperability(prs: Presentation) -> SlideFrame:
    """Build the standards-shaped interoperability slide (page 7)."""
    copy = SLIDES[6]
    frame = add_slide(prs, copy.index, copy.section)

    add_text(
        frame,
        "INTEROPERABILITY / STANDARDS-SHAPED DATA",
        0.78,
        0.62,
        5.0,
        0.24,
        font=MONO_FONT,
        size=9.5,
        color=MUTED,
        bold=True,
    )
    add_text(
        frame,
        copy.title,
        0.78,
        0.98,
        7.35,
        1.05,
        font=DISPLAY_FONT,
        size=29,
        color=BLACK,
    )
    add_text(
        frame,
        copy.message,
        0.78,
        2.12,
        7.0,
        0.55,
        size=14.5,
        color=MUTED,
    )

    # Left column: the native resource map, one editable row per mapping.
    add_text(
        frame,
        "NATIVE RESOURCE MAP",
        0.78,
        2.95,
        3.5,
        0.24,
        font=MONO_FONT,
        size=9.5,
        color=CORAL,
        bold=True,
    )
    mappings = (
        ("PRESCRIPTION", "HL7 FHIR MedicationRequest"),
        ("DIAGNOSTIC REPORT", "HL7 FHIR DiagnosticReport"),
        ("ITEMIZED BILL", "NHCX FHIR Claim"),
    )
    for offset, (source, target) in enumerate(mappings):
        y = 3.32 + offset * 0.66
        add_line(frame, 0.78, y - 0.12, 8.13, y - 0.12, color=BLACK, width=0.75)
        _add_mapping_row(
            frame,
            x=0.78,
            y=y,
            w=7.35,
            source=source,
            target=target,
        )

    # Monospace ABDM trace strip on a black band.
    add_rect(frame, 0.78, 5.35, 7.35, 1.25, fill=BLACK)
    add_text(
        frame,
        "ABDM TRACE  /  ENDPOINT · STATUS · LATENCY",
        1.0,
        5.52,
        6.9,
        0.24,
        font=MONO_FONT,
        size=9.5,
        color=CORAL,
        bold=True,
    )
    add_text(
        frame,
        "ABDM CARE CONTEXT LINK  ·  200  ·  SIM",
        1.0,
        5.84,
        6.9,
        0.24,
        font=MONO_FONT,
        size=9.5,
        color=BONE_2,
    )
    add_text(
        frame,
        "NHCX CLAIM SUBMIT  ·  200  ·  SIM",
        1.0,
        6.12,
        6.9,
        0.24,
        font=MONO_FONT,
        size=9.5,
        color=BONE_2,
    )

    # Right column: boundary statement first, then the approved evidence.
    add_rect(frame, 8.42, 0.98, 0.10, 1.62, fill=CORAL)
    add_text(
        frame,
        "BOUNDARY",
        8.72,
        0.98,
        2.0,
        0.26,
        font=MONO_FONT,
        size=10,
        color=CORAL,
        bold=True,
    )
    add_text(
        frame,
        "GATEWAYS INTERNALLY SIMULATED  /  DETERMINISTIC OFFLINE DEMO",
        8.72,
        1.34,
        3.85,
        0.62,
        font=MONO_FONT,
        size=11,
        color=BLACK,
        bold=True,
    )
    add_line(frame, 8.72, 2.14, 12.62, 2.14, color=BLACK, width=0.75)
    for offset, evidence in enumerate(copy.evidence):
        y = 2.36 + offset * 0.46
        add_rect(frame, 8.72, y + 0.055, 0.09, 0.09, fill=CORAL)
        add_text(
            frame,
            evidence,
            8.98,
            y,
            3.6,
            0.26,
            font=MONO_FONT,
            size=10,
            color=BLACK,
        )
    add_text(
        frame,
        "NOT LIVE GOVERNMENT CONNECTIONS",
        8.72,
        4.32,
        3.6,
        0.22,
        font=MONO_FONT,
        size=9,
        color=MUTED,
    )

    add_footer(frame)
    set_notes(frame, copy.notes)
    return frame


def build_emergency(
    prs: Presentation, screenshot_path: Path | None = None
) -> SlideFrame:
    """Build the panic-to-people emergency slide (page 8)."""
    copy = SLIDES[7]
    frame = add_slide(prs, copy.index, copy.section, dark=True)
    screenshot = required_screenshot(screenshot_path or HOSPITAL_SOS_SCREENSHOT)

    add_text(
        frame,
        "EMERGENCY / LIVE ALERT PATH",
        0.85,
        0.62,
        4.0,
        0.24,
        font=MONO_FONT,
        size=9.5,
        color=CORAL,
        bold=True,
    )
    add_text(
        frame,
        copy.title,
        0.85,
        0.98,
        6.3,
        1.05,
        font=DISPLAY_FONT,
        size=30,
        color=BONE,
    )
    add_text(
        frame,
        copy.message,
        0.85,
        2.10,
        6.3,
        0.55,
        size=14.5,
        color=BONE_2,
    )

    # Three-stage flow on one continuous coral spine.
    add_line(frame, 0.9, 3.62, 7.62, 3.62, color=CORAL, width=2.25)
    stages = (
        ("PANIC", "One authenticated action"),
        ("PANEL", "WebSocket broadcast to hospital dashboards"),
        ("PEOPLE", "GPS coordinates + SMTP contact email"),
    )
    for offset, (stage, detail) in enumerate(stages):
        node_x = 1.02 + offset * 2.25
        add_rect(frame, node_x, 3.54, 0.16, 0.16, fill=CORAL)
        add_text(
            frame,
            stage,
            node_x + 0.10,
            3.06,
            1.9,
            0.42,
            font=DISPLAY_FONT,
            size=19,
            color=BONE,
            bold=True,
        )
        add_text(
            frame,
            detail,
            node_x + 0.10,
            3.86,
            1.95,
            0.85,
            size=11,
            color=BONE_2,
        )

    # Resilience strip: mail outages never stall the live feed.
    add_rect(
        frame,
        0.85,
        5.30,
        6.45,
        0.58,
        fill=BLACK,
        line=CORAL,
        width=1.25,
    )
    add_text(
        frame,
        "EMAIL FAILURE NEVER BLOCKS THE LIVE ALERT",
        1.05,
        5.30,
        6.05,
        0.58,
        font=MONO_FONT,
        size=10.5,
        color=CORAL,
        bold=True,
        valign=MSO_ANCHOR.MIDDLE,
    )
    add_text(
        frame,
        "SERVICE RECORDS SKIPPED / FAILED EMAIL STATUS WHILE THE FEED CONTINUES",
        0.85,
        6.02,
        6.45,
        0.22,
        font=MONO_FONT,
        size=9,
        color=BONE_2,
    )

    # Captured hospital SOS dashboard: the page's exactly-one picture.
    add_rect(frame, 7.62, 1.28, 5.06, 3.36, fill=BONE_2)
    frame.slide.shapes.add_picture(
        str(screenshot),
        Inches(7.75),
        Inches(1.41),
        width=Inches(4.8),
        height=Inches(3.0),
    )
    _add_outline_rect(
        frame,
        7.70,
        1.36,
        4.9,
        3.1,
        color=BLACK,
        width=1.0,
    )
    add_text(
        frame,
        "HOSPITAL DASHBOARD / LIVE SOS FEED",
        7.75,
        4.80,
        4.8,
        0.24,
        font=MONO_FONT,
        size=9.5,
        color=BONE_2,
    )

    add_footer(frame)
    set_notes(frame, copy.notes)
    return frame


def build_evidence(prs: Presentation) -> SlideFrame:
    """Build the measured-not-marketed evidence slide (page 9)."""
    copy = SLIDES[8]
    frame = add_slide(prs, copy.index, copy.section)

    add_text(
        frame,
        "EVIDENCE / REPOSITORY VERIFICATION",
        0.78,
        0.62,
        5.0,
        0.24,
        font=MONO_FONT,
        size=9.5,
        color=MUTED,
        bold=True,
    )
    add_text(
        frame,
        copy.title,
        0.78,
        0.96,
        6.6,
        1.05,
        font=DISPLAY_FONT,
        size=30,
        color=BLACK,
    )
    add_text(
        frame,
        copy.message,
        0.78,
        2.08,
        6.9,
        0.55,
        size=14.5,
        color=MUTED,
    )

    # Left column: verified facts as individually editable rows.
    add_text(
        frame,
        "VERIFIED IN THIS REPOSITORY",
        0.78,
        2.95,
        4.9,
        0.24,
        font=MONO_FONT,
        size=9.5,
        color=CORAL,
        bold=True,
    )
    facts = (
        (3.32, "19 automated service tests"),
        (3.82, "16-step end-to-end scenario"),
        (4.32, "5 FastAPI services"),
        (4.82, "5 SQLite databases"),
        (5.32, "One-command service startup"),
    )
    for y, fact in facts:
        add_rect(frame, 0.78, y + 0.07, 0.13, 0.13, fill=CORAL)
        add_text(
            frame,
            fact,
            1.04,
            y,
            4.6,
            0.34,
            size=13.5,
            color=BLACK,
            bold=True,
        )
    add_text(
        frame,
        "COMPOSE STARTS GATEWAY + 5 SERVICES + SEED",
        1.04,
        5.72,
        4.9,
        0.22,
        font=MONO_FONT,
        size=9,
        color=MUTED,
    )
    add_text(
        frame,
        "THE NEXT.JS FRONTEND RUNS SEPARATELY",
        1.04,
        5.96,
        4.9,
        0.22,
        font=MONO_FONT,
        size=9,
        color=MUTED,
    )

    # Right column: terminal-style verification log, native text only.
    add_rect(frame, 5.95, 2.95, 6.68, 2.72, fill=BLACK)
    add_rect(frame, 5.95, 2.95, 6.68, 0.06, fill=CORAL)
    add_text(
        frame,
        "SY1512 VERIFICATION LOG",
        6.18,
        3.12,
        4.0,
        0.24,
        font=MONO_FONT,
        size=9,
        color=BONE_2,
    )
    log_lines = (
        (3.48, "$ pytest services/*/tests -q", CORAL),
        (3.76, "19 passed", GREEN),
        (4.10, "$ python scripts/e2e.py", CORAL),
        (4.38, "ALL PASS: 16/16", GREEN),
        (4.72, "$ docker compose up -d", CORAL),
        (5.00, "GATEWAY + 5 SERVICES + SEED READY", BONE_2),
        (5.28, "NEXT.JS FRONTEND RUNS SEPARATELY", BONE_2),
    )
    for y, line, color in log_lines:
        add_text(
            frame,
            line,
            6.18,
            y,
            6.2,
            0.26,
            font=MONO_FONT,
            size=10.5,
            color=color,
        )

    # Boundaries strip, square corners with a coral leading rule.
    add_rect(
        frame,
        0.78,
        6.24,
        11.85,
        0.62,
        fill=OFF_WHITE,
        line=BONE_2,
        width=0.75,
    )
    add_rect(frame, 0.78, 6.24, 0.09, 0.62, fill=CORAL)
    add_text(
        frame,
        "BOUNDARIES STATED",
        1.05,
        6.32,
        2.5,
        0.22,
        font=MONO_FONT,
        size=9.5,
        color=CORAL,
        bold=True,
    )
    add_text(
        frame,
        "SIMULATED GATEWAYS · NO PRODUCTION HARDENING · SMTP OPTIONAL",
        1.05,
        6.56,
        11.3,
        0.26,
        font=MONO_FONT,
        size=11.5,
        color=BLACK,
        bold=True,
    )

    add_footer(frame)
    set_notes(frame, copy.notes)
    return frame


def build_close(prs: Presentation) -> SlideFrame:
    """Build the closing short-proof slide (page 10)."""
    copy = SLIDES[9]
    frame = add_slide(prs, copy.index, copy.section, dark=True)

    add_text(
        frame,
        "CLOSE / THE SHORT PROOF",
        0.85,
        0.62,
        4.0,
        0.24,
        font=MONO_FONT,
        size=9.5,
        color=CORAL,
        bold=True,
    )
    add_text(
        frame,
        copy.title,
        0.85,
        0.96,
        11.9,
        1.0,
        font=DISPLAY_FONT,
        size=27,
        color=BONE,
    )
    add_text(
        frame,
        copy.message,
        0.85,
        2.08,
        8.0,
        0.55,
        size=14.5,
        color=BONE_2,
    )

    # Five numbered steps on one coral spine, labels verbatim from evidence.
    add_line(frame, 0.9, 3.9, 12.4, 3.9, color=CORAL, width=2.25)
    for offset, step in enumerate(copy.evidence):
        node_x = 1.02 + offset * 2.25
        add_rect(frame, node_x, 3.82, 0.16, 0.16, fill=CORAL)
        add_text(
            frame,
            f"{offset + 1:02d}",
            node_x + 0.10,
            3.42,
            1.0,
            0.28,
            font=MONO_FONT,
            size=12,
            color=CORAL,
            bold=True,
        )
        add_text(
            frame,
            step,
            node_x + 0.10,
            4.16,
            2.1,
            0.3,
            size=14,
            color=BONE,
            bold=True,
        )

    # Next steps, unequal editorial columns on thin bone rules.
    add_text(
        frame,
        "NEXT STEPS",
        0.85,
        5.15,
        2.5,
        0.26,
        font=MONO_FONT,
        size=10.5,
        color=CORAL,
        bold=True,
    )
    next_steps = (
        (0.85, 2.9, "PostgreSQL deployment"),
        (4.05, 2.9, "Real ABDM / NHCX sandbox credential approval"),
        (7.25, 2.5, "Stronger observability"),
        (10.05, 2.63, "Controlled clinical pilot"),
    )
    for x, w, step in next_steps:
        add_line(frame, x, 5.52, x + w - 0.3, 5.52, color=BONE_2, width=0.75)
        add_text(
            frame,
            step,
            x,
            5.62,
            w,
            0.75,
            size=12,
            color=BONE_2,
        )

    add_footer(frame)
    set_notes(frame, copy.notes)
    return frame


__all__ = [
    "build_close",
    "build_evidence",
    "build_emergency",
    "build_interoperability",
]
