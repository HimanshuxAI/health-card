from __future__ import annotations

import math
from pathlib import Path

from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.presentation import Presentation
from pptx.shapes.base import BaseShape
from pptx.util import Inches, Pt

from deck.content import SLIDES
from deck.theme import (
    BLACK,
    BONE,
    BONE_2,
    CORAL,
    DISPLAY_FONT,
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


QR_URL = "http://localhost:3000/scan"


def _style_run(run, *, font: str, size: float, color: RGBColor, bold: bool = False) -> None:
    run.font.name = font
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold


def _add_coral_word_title(
    frame: SlideFrame,
    before: str,
    accent: str,
    *,
    x: float,
    y: float,
    w: float,
    h: float,
    size: float,
) -> BaseShape:
    """Add one editable text shape with only its final phrase in coral."""
    shape = add_text(
        frame,
        before + accent,
        x,
        y,
        w,
        h,
        font=DISPLAY_FONT,
        size=size,
        color=BLACK,
    )
    paragraph = shape.text_frame.paragraphs[0]
    paragraph.clear()
    before_run = paragraph.add_run()
    before_run.text = before
    _style_run(before_run, font=DISPLAY_FONT, size=size, color=BLACK)
    accent_run = paragraph.add_run()
    accent_run.text = accent
    _style_run(accent_run, font=DISPLAY_FONT, size=size, color=CORAL)
    return shape


def _rotate_around(
    shape: BaseShape,
    *,
    center_x: float,
    center_y: float,
    angle_degrees: float,
) -> None:
    """Rotate a shape and its center around a shared card center."""
    angle = math.radians(angle_degrees)
    shape_center_x = shape.left / Inches(1) + shape.width / Inches(1) / 2
    shape_center_y = shape.top / Inches(1) + shape.height / Inches(1) / 2
    delta_x = shape_center_x - center_x
    delta_y = shape_center_y - center_y
    rotated_x = center_x + delta_x * math.cos(angle) - delta_y * math.sin(angle)
    rotated_y = center_y + delta_x * math.sin(angle) + delta_y * math.cos(angle)
    shape.left = Inches(rotated_x - shape.width / Inches(1) / 2)
    shape.top = Inches(rotated_y - shape.height / Inches(1) / 2)
    shape.rotation = angle_degrees


def _require_qr(qr_path: Path | None) -> Path:
    if qr_path is None:
        raise ValueError("A generated QR path is required for this slide.")
    return qr_path


def build_cover(
    prs: Presentation, qr_path: Path | None = None
) -> SlideFrame:
    """Build the emergency-passport cover slide."""
    copy = SLIDES[0]
    frame = add_slide(prs, copy.index, copy.section, dark=True)
    qr_path = _require_qr(qr_path)

    # A 17% rescue spine establishes the emergency-dossier motif.
    add_rect(frame, 0, 0, 13.333 * 0.17, 7.5, fill=CORAL)
    spine_label = add_text(
        frame,
        "EMERGENCY ACCESS / SY1512",
        0.05,
        1.05,
        2.15,
        0.28,
        font=MONO_FONT,
        size=10,
        color=BLACK,
        bold=True,
    )
    spine_label.rotation = 270

    add_text(
        frame,
        copy.title,
        2.85,
        1.28,
        4.35,
        2.28,
        font=DISPLAY_FONT,
        size=35,
        color=BONE,
    )
    accent = add_rect(frame, 2.94, 3.69, 3.45, 0.12, fill=CORAL)
    accent.rotation = -3.5
    add_text(
        frame,
        copy.message,
        2.9,
        4.05,
        4.25,
        0.85,
        size=15.5,
        color=BONE_2,
        line_spacing=1.05,
    )
    for x, y, w, evidence in (
        (2.90, 5.12, 1.40, copy.evidence[0]),
        (4.35, 5.12, 2.80, copy.evidence[1]),
        (2.90, 5.43, 2.00, copy.evidence[2]),
    ):
        add_text(
            frame,
            evidence,
            x,
            y,
            w,
            0.22,
            font=MONO_FONT,
            size=9.5,
            color=BONE_2,
        )

    # The physical patient card is the only rounded object in the deck.
    card_x, card_y, card_w, card_h = 7.55, 0.85, 4.50, 5.45
    card_angle = 5.0
    card_center_x = card_x + card_w / 2
    card_center_y = card_y + card_h / 2

    shadow = add_rect(
        frame,
        card_x + 0.14,
        card_y + 0.16,
        card_w,
        card_h,
        fill=BLACK,
        line=BONE_2,
        width=1.25,
    )
    shadow.rotation = card_angle

    card = add_rect(
        frame,
        card_x,
        card_y,
        card_w,
        card_h,
        fill=BLACK,
        line=BONE,
        width=1.5,
        radius=True,
    )
    card.rotation = card_angle

    card_parts: list[BaseShape] = []
    card_parts.append(
        add_rect(frame, card_x, card_y, card_w, 0.13, fill=CORAL)
    )
    card_parts.append(
        add_text(
            frame,
            "EMERGENCY PROFILE",
            card_x + 0.30,
            card_y + 0.34,
            card_w - 0.60,
            0.25,
            font=MONO_FONT,
            size=10,
            color=CORAL,
            bold=True,
        )
    )
    card_parts.append(
        add_text(
            frame,
            "Aarav Mehta",
            card_x + 0.30,
            card_y + 0.76,
            card_w - 0.60,
            0.55,
            font=DISPLAY_FONT,
            size=24,
            color=BONE,
        )
    )
    card_parts.append(
        add_text(
            frame,
            "14-XXXX-XXXX-XXXX",
            card_x + 0.30,
            card_y + 1.40,
            card_w - 0.60,
            0.28,
            font=MONO_FONT,
            size=10.5,
            color=BONE_2,
        )
    )
    card_parts.append(
        add_rect(frame, card_x + 0.30, card_y + 1.86, card_w - 0.60, 0.02, fill=BONE_2)
    )
    for offset, field in enumerate(
        ("BLOOD GROUP  O+", "ALLERGY  Penicillin", "CONSENT  Active")
    ):
        card_parts.append(
            add_text(
                frame,
                field,
                card_x + 0.30,
                card_y + 2.10 + offset * 0.49,
                card_w - 0.60,
                0.28,
                font=MONO_FONT,
                size=10,
                color=BONE,
                bold=offset == 2,
            )
        )

    qr_size = 1.34
    qr = frame.slide.shapes.add_picture(
        str(qr_path),
        Inches(card_x + 0.30),
        Inches(card_y + 3.72),
        width=Inches(qr_size),
        height=Inches(qr_size),
    )
    card_parts.append(qr)
    card_parts.append(
        add_text(
            frame,
            "LOCAL DEMO QR",
            card_x + 1.90,
            card_y + 3.84,
            card_w - 2.20,
            0.24,
            font=MONO_FONT,
            size=9.5,
            color=CORAL,
            bold=True,
        )
    )
    card_parts.append(
        add_text(
            frame,
            "OPAQUE TOKEN",
            card_x + 1.90,
            card_y + 4.15,
            card_w - 2.20,
            0.24,
            font=MONO_FONT,
            size=9.5,
            color=BONE_2,
        )
    )
    card_parts.append(
        add_text(
            frame,
            "SCAN TO RESOLVE",
            card_x + 1.90,
            card_y + 4.50,
            card_w - 2.20,
            0.24,
            font=MONO_FONT,
            size=9.5,
            color=BONE,
        )
    )

    for part in card_parts:
        _rotate_around(
            part,
            center_x=card_center_x,
            center_y=card_center_y,
            angle_degrees=card_angle,
        )

    add_text(
        frame,
        "Group SY1512 · School of Computing · MIT-ADT University",
        2.85,
        6.38,
        7.8,
        0.25,
        size=10,
        color=BONE_2,
    )
    add_footer(frame)
    set_notes(frame, copy.notes)
    return frame


def _add_fact_strip(
    frame: SlideFrame,
    *,
    x: float,
    y: float,
    w: float,
    number: str,
    label: str,
    subline: str,
) -> None:
    add_rect(frame, x, y, w, 1.02, fill=OFF_WHITE, line=BONE_2, width=0.75)
    add_rect(frame, x, y, 0.09, 1.02, fill=CORAL)
    add_text(
        frame,
        number,
        x + 0.24,
        y + 0.12,
        0.55,
        0.55,
        font=DISPLAY_FONT,
        size=31,
        color=CORAL,
    )
    add_text(
        frame,
        label,
        x + 0.88,
        y + 0.16,
        w - 1.08,
        0.32,
        font=DISPLAY_FONT,
        size=16,
        color=BLACK,
        bold=True,
    )
    add_text(
        frame,
        subline,
        x + 0.88,
        y + 0.57,
        w - 1.08,
        0.25,
        size=10.5,
        color=MUTED,
    )


def build_problem(
    prs: Presentation, qr_path: Path | None = None
) -> SlideFrame:
    """Build the fragmented-context problem slide."""
    del qr_path  # Kept uniform with the other narrative builders.
    copy = SLIDES[1]
    frame = add_slide(prs, copy.index, copy.section)

    add_text(
        frame,
        "03:12",
        0.82,
        0.66,
        3.1,
        1.38,
        font=DISPLAY_FONT,
        size=84,
        color=BLACK,
    )
    add_text(
        frame,
        "AM · CITY HOSPITAL",
        0.87,
        2.13,
        2.85,
        0.24,
        size=9.5,
        color=MUTED,
        bold=True,
    )
    add_line(frame, 0.87, 2.48, 3.68, 2.48, color=BLACK, width=1.0)

    add_text(
        frame,
        copy.title,
        4.12,
        0.76,
        7.72,
        1.05,
        font=DISPLAY_FONT,
        size=31,
        color=BLACK,
    )
    add_text(
        frame,
        copy.message,
        4.15,
        1.82,
        7.25,
        0.54,
        size=15,
        color=MUTED,
    )

    _add_fact_strip(
        frame,
        x=0.85,
        y=2.84,
        w=3.08,
        number="01",
        label="Allergies?",
        subline="Hidden in a patient file.",
    )
    _add_fact_strip(
        frame,
        x=4.37,
        y=2.48,
        w=3.10,
        number="02",
        label="Medications?",
        subline="Stored in a medication list.",
    )
    _add_fact_strip(
        frame,
        x=8.08,
        y=2.93,
        w=3.24,
        number="03",
        label="Conditions?",
        subline="Buried in clinical history.",
    )
    _add_fact_strip(
        frame,
        x=3.06,
        y=4.48,
        w=3.34,
        number="04",
        label="Coverage?",
        subline="Held by a billing system.",
    )

    add_rect(frame, 12.02, 2.35, 0.10, 3.57, fill=CORAL)
    gap_label = add_text(
        frame,
        "CONTEXT GAP",
        11.00,
        2.62,
        1.52,
        0.26,
        font=MONO_FONT,
        size=11.5,
        color=CORAL,
        bold=True,
    )
    gap_label.rotation = 270

    for x, width, evidence in (
        (0.85, 2.55, copy.evidence[0]),
        (4.02, 3.05, copy.evidence[1]),
        (7.70, 3.30, copy.evidence[2]),
    ):
        add_text(
            frame,
            evidence,
            x,
            5.77,
            width,
            0.22,
            font=MONO_FONT,
            size=9,
            color=MUTED,
        )

    add_rect(frame, 0.85, 6.05, 1.08, 0.07, fill=CORAL)
    add_text(
        frame,
        "The responder gets a login screen while the patient gets an emergency.",
        0.85,
        6.18,
        10.92,
        0.45,
        font=DISPLAY_FONT,
        size=17.5,
        color=BLACK,
    )

    add_footer(frame)
    set_notes(frame, copy.notes)
    return frame


def build_solution(
    prs: Presentation, qr_path: Path | None = None
) -> SlideFrame:
    """Build the one-scan emergency-resolution slide."""
    copy = SLIDES[2]
    frame = add_slide(prs, copy.index, copy.section)
    qr_path = _require_qr(qr_path)

    add_text(
        frame,
        "EMERGENCY RESOLUTION / LOCAL DEMO",
        0.78,
        0.64,
        3.75,
        0.24,
        font=MONO_FONT,
        size=9,
        color=MUTED,
        bold=True,
    )
    add_rect(frame, 0.68, 1.08, 3.80, 3.80, fill=BLACK)
    frame.slide.shapes.add_picture(
        str(qr_path),
        Inches(0.80),
        Inches(1.20),
        width=Inches(3.56),
        height=Inches(3.56),
    )
    add_rect(frame, 0.64, 2.95, 3.88, 0.055, fill=CORAL)
    add_text(
        frame,
        "SCAN /scan",
        0.80,
        5.00,
        3.56,
        0.24,
        font=MONO_FONT,
        size=9,
        color=BLACK,
        bold=True,
        align=PP_ALIGN.CENTER,
    )

    _add_coral_word_title(
        frame,
        "One scan. The right context. ",
        "Immediately.",
        x=4.95,
        y=0.86,
        w=7.55,
        h=1.55,
        size=34,
    )
    add_text(
        frame,
        copy.message,
        5.00,
        2.55,
        7.10,
        0.50,
        size=15,
        color=MUTED,
    )

    process_x = (5.00, 6.96, 8.92, 10.88)
    add_line(frame, process_x[0], 3.48, 12.46, 3.48, color=BLACK, width=1.0)
    for index, label in enumerate(
        ("TOKEN LOOKUP", "HMAC VERIFY", "AES-GCM OPEN", "CONSENT GATE")
    ):
        x = process_x[index]
        add_rect(frame, x, 3.40, 0.16, 0.16, fill=CORAL)
        add_text(
            frame,
            label,
            x + 0.23,
            3.28,
            1.52,
            0.32,
            font=MONO_FONT,
            size=10,
            color=BLACK,
            bold=True,
        )

    add_text(
        frame,
        "  /  ".join(copy.evidence),
        5.00,
        4.60,
        7.35,
        0.26,
        font=MONO_FONT,
        size=9,
        color=MUTED,
    )

    add_text(
        frame,
        "SEEDED PROFILE EXAMPLE",
        9.56,
        5.09,
        3.02,
        0.22,
        font=MONO_FONT,
        size=9,
        color=MUTED,
        bold=True,
        align=PP_ALIGN.RIGHT,
    )

    strip_x = 0.75
    strip_y = 5.42
    strip_w = 11.83
    strip_h = 1.22
    cell_w = strip_w / 4
    cells = (
        ("BLOOD GROUP", "O+"),
        ("ALLERGIES", "03"),
        ("CONDITIONS", "05"),
        ("RETRIEVAL TARGET", "<800 ms"),
    )
    for index, (label, value) in enumerate(cells):
        x = strip_x + index * cell_w
        add_rect(
            frame,
            x,
            strip_y,
            cell_w,
            strip_h,
            fill=OFF_WHITE,
            line=BLACK,
            width=0.75,
        )
        add_text(
            frame,
            label,
            x + 0.18,
            strip_y + 0.18,
            cell_w - 0.36,
            0.22,
            font=MONO_FONT,
            size=9,
            color=MUTED,
            bold=True,
        )
        add_text(
            frame,
            value,
            x + 0.18,
            strip_y + 0.53,
            cell_w - 0.36,
            0.43,
            font=DISPLAY_FONT if value != "<800 ms" else MONO_FONT,
            size=21 if value != "<800 ms" else 18,
            color=BLACK,
            bold=True,
        )

    add_footer(frame)
    set_notes(frame, copy.notes)
    return frame


__all__ = ["build_cover", "build_problem", "build_solution"]
