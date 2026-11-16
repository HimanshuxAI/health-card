from __future__ import annotations

from pathlib import Path

from PIL import Image
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.presentation import Presentation
from pptx.shapes.base import BaseShape
from pptx.util import Inches, Pt

from deck.assets import required_screenshot
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


_REQUIRED_SCREENSHOTS = (
    "patient.png",
    "hospital.png",
    "hospital_sos.png",
    "admin.png",
    "admin_trace.png",
)


def _add_editorial_screenshot(
    frame: SlideFrame,
    path: Path,
    *,
    x: float,
    y: float,
    w: float,
    h: float,
) -> BaseShape:
    """Add one cropped project screenshot with a thin, native black border."""
    with Image.open(path) as image:
        source_width, source_height = image.size

    # The captures are 1440×900 browser views, but their product content occupies
    # the upper-left working area. Focus that area instead of carrying a large
    # blank browser canvas into every editorial panel.
    crop_left_px = round(source_width * 0.05)
    crop_right_px = crop_left_px + round(source_width * 0.58)
    visible_width_px = crop_right_px - crop_left_px
    visible_height_px = min(source_height, visible_width_px * h / w)

    picture = frame.slide.shapes.add_picture(
        str(path),
        Inches(x),
        Inches(y),
        width=Inches(w),
        height=Inches(h),
    )
    picture.crop_left = crop_left_px / source_width
    picture.crop_right = (source_width - crop_right_px) / source_width
    picture.crop_top = 0.0
    picture.crop_bottom = (source_height - visible_height_px) / source_height
    picture.line.color.rgb = BLACK
    picture.line.width = Pt(0.75)
    return picture


def _add_route_line(
    frame: SlideFrame,
    points: tuple[tuple[float, float], ...],
) -> BaseShape:
    """Add one editable freeform polyline connecting the experience lanes."""
    start_x, start_y = points[0]
    builder = frame.slide.shapes.build_freeform(
        start_x=int(start_x * 1000),
        start_y=int(start_y * 1000),
        scale=Inches(1) / 1000,
    )
    builder.add_line_segments(
        [(int(x * 1000), int(y * 1000)) for x, y in points[1:]],
        close=False,
    )
    route = builder.convert_to_shape()
    route.fill.background()
    route.line.color.rgb = CORAL
    route.line.width = Pt(2.25)
    return route


def build_experience(
    prs: Presentation,
    *,
    assets_dir: Path,
) -> SlideFrame:
    """Build the role-specific patient, hospital, and admin experience slide."""
    copy = SLIDES[3]
    frame = add_slide(prs, copy.index, copy.section)

    assets_dir = Path(assets_dir)
    screenshot_paths = {
        name: required_screenshot(assets_dir / name)
        for name in _REQUIRED_SCREENSHOTS
    }

    add_text(
        frame,
        "EXPERIENCE / ONE IDENTITY, THREE OPERATING MODES",
        0.78,
        0.38,
        5.2,
        0.22,
        font=MONO_FONT,
        size=8.5,
        color=MUTED,
        bold=True,
    )
    add_text(
        frame,
        copy.title,
        0.76,
        0.64,
        7.8,
        0.62,
        font=DISPLAY_FONT,
        size=33,
        color=BLACK,
    )
    add_text(
        frame,
        copy.message,
        0.79,
        1.30,
        8.25,
        0.34,
        size=13.5,
        color=MUTED,
    )

    _add_route_line(
        frame,
        (
            (2.55, 2.31),
            (3.88, 1.78),
            (5.52, 1.78),
            (6.46, 2.02),
            (7.94, 2.02),
            (9.18, 1.79),
            (10.55, 2.39),
        ),
    )
    for x, y in ((2.55, 2.31), (6.46, 2.02), (10.55, 2.39)):
        node = frame.slide.shapes.add_shape(
            MSO_SHAPE.OVAL,
            Inches(x - 0.07),
            Inches(y - 0.07),
            Inches(0.14),
            Inches(0.14),
        )
        node.fill.solid()
        node.fill.fore_color.rgb = CORAL
        node.line.color.rgb = CORAL

    lanes = (
        {
            "screenshot": "patient.png",
            "x": 0.78,
            "y": 2.43,
            "w": 3.55,
            "h": 2.40,
            "label": "CARRY IT",
            "role": "PATIENT",
            "descriptor": "Emergency profile, consent, claims.",
            "label_y": 4.98,
        },
        {
            "screenshot": "hospital.png",
            "x": 4.62,
            "y": 2.15,
            "w": 3.68,
            "h": 2.49,
            "label": "USE IT",
            "role": "HOSPITAL",
            "descriptor": "Scan, write records, bill, respond.",
            "label_y": 4.80,
        },
        {
            "screenshot": "admin_trace.png",
            "x": 8.58,
            "y": 2.52,
            "w": 3.95,
            "h": 2.67,
            "label": "AUDIT IT",
            "role": "ADMIN",
            "descriptor": "Trace claims, integrations, SOS history.",
            "label_y": 5.36,
        },
    )
    for lane in lanes:
        _add_editorial_screenshot(
            frame,
            screenshot_paths[lane["screenshot"]],
            x=lane["x"],
            y=lane["y"],
            w=lane["w"],
            h=lane["h"],
        )
        add_text(
            frame,
            lane["label"],
            lane["x"],
            lane["label_y"],
            1.52,
            0.25,
            font=MONO_FONT,
            size=10.5,
            color=CORAL,
            bold=True,
        )
        add_text(
            frame,
            lane["role"],
            lane["x"],
            lane["label_y"] + 0.28,
            2.0,
            0.38,
            font=DISPLAY_FONT,
            size=18,
            color=BLACK,
            bold=True,
        )
        add_text(
            frame,
            lane["descriptor"],
            lane["x"],
            lane["label_y"] + 0.72,
            lane["w"] - 0.08,
            0.43,
            size=10.5,
            color=MUTED,
        )

    add_footer(frame)
    set_notes(frame, copy.notes)
    return frame


def build_architecture(prs: Presentation) -> SlideFrame:
    """Build the five-service architecture slide."""
    copy = SLIDES[4]
    frame = add_slide(prs, copy.index, copy.section, dark=True)

    add_text(
        frame,
        "ARCHITECTURE / SERVICE-OWNED DATA",
        0.78,
        0.38,
        4.7,
        0.22,
        font=MONO_FONT,
        size=8.5,
        color=BONE_2,
        bold=True,
    )
    add_text(
        frame,
        copy.title,
        0.76,
        0.66,
        5.8,
        0.72,
        font=DISPLAY_FONT,
        size=31,
        color=BONE,
    )
    add_text(
        frame,
        copy.message,
        0.79,
        1.42,
        5.25,
        0.54,
        size=13,
        color=BONE_2,
    )

    add_rect(frame, 6.15, 0.70, 5.85, 0.48, fill=OFF_WHITE, line=BONE)
    add_text(
        frame,
        "NEXT.JS FRONTEND",
        6.35,
        0.81,
        5.45,
        0.24,
        font=MONO_FONT,
        size=11,
        color=BLACK,
        bold=True,
        align=PP_ALIGN.CENTER,
    )
    add_rect(frame, 6.78, 1.36, 5.22, 0.48, fill=CORAL, line=CORAL)
    add_text(
        frame,
        "NGINX API GATEWAY",
        6.98,
        1.47,
        4.82,
        0.24,
        font=MONO_FONT,
        size=11,
        color=BLACK,
        bold=True,
        align=PP_ALIGN.CENTER,
    )
    add_line(frame, 9.39, 1.84, 9.39, 2.26, color=BONE_2, width=1.25)

    add_line(frame, 0.65, 2.18, 0.65, 6.48, color=CORAL, width=2.25)

    services = (
        ("Identity", "JWT · RBAC · eKYC · Consent", "identity.db", 0.92, 8.35),
        (
            "Records",
            "Profiles · FHIR records · AES-GCM · QR",
            "records.db",
            0.76,
            7.62,
        ),
        ("ABDM", "Care contexts · HL7 FHIR v4 · trace", "abdm.db", 1.15, 8.58),
        ("NHCX", "Bills · FHIR Claim · adjudication", "nhcx.db", 0.86, 7.20),
        ("SOS", "WebSocket · GPS · email", "sos.db", 1.05, 8.05),
    )
    layer_y = (2.26, 3.13, 4.00, 4.87, 5.74)
    for index, (service, capabilities, database, x, w) in enumerate(services):
        y = layer_y[index]
        add_line(frame, 0.65, y + 0.36, x, y + 0.36, color=CORAL, width=1.25)
        add_rect(
            frame,
            x,
            y,
            w,
            0.72,
            fill=OFF_WHITE if index % 2 == 0 else BONE_2,
            line=BLACK,
            width=0.75,
        )
        add_text(
            frame,
            service,
            x + 0.18,
            y + 0.14,
            1.15,
            0.38,
            font=DISPLAY_FONT,
            size=17,
            color=BLACK,
            bold=True,
        )
        add_text(
            frame,
            capabilities,
            x + 1.40,
            y + 0.19,
            w - 3.02,
            0.27,
            font=MONO_FONT,
            size=9.2,
            color=BLACK,
        )
        add_text(
            frame,
            database,
            x + w - 1.45,
            y + 0.19,
            1.25,
            0.27,
            font=MONO_FONT,
            size=9.2,
            color=CORAL,
            bold=True,
            align=PP_ALIGN.RIGHT,
        )

    add_rect(frame, 10.55, 2.22, 1.72, 4.25, fill=CORAL, line=CORAL)
    patient_view = add_text(
        frame,
        "ONE PATIENT VIEW",
        9.48,
        4.13,
        3.45,
        0.30,
        font=MONO_FONT,
        size=12,
        color=BLACK,
        bold=True,
        align=PP_ALIGN.CENTER,
    )
    patient_view.rotation = 270

    add_text(
        frame,
        (
            "5 FastAPI services  /  Next.js frontend  /  NGINX gateway  /  "
            "5 SQLite databases"
        ),
        1.00,
        6.61,
        9.25,
        0.22,
        font=MONO_FONT,
        size=8.2,
        color=BONE_2,
    )

    add_footer(frame)
    set_notes(frame, copy.notes)
    return frame


def _add_seal(frame: SlideFrame) -> None:
    """Draw the large native seal and an editable line-built lock."""
    seal = frame.slide.shapes.add_shape(
        MSO_SHAPE.OVAL,
        Inches(9.63),
        Inches(0.62),
        Inches(2.95),
        Inches(2.95),
    )
    seal.fill.background()
    seal.line.color.rgb = CORAL
    seal.line.width = Pt(2.5)

    shackle = frame.slide.shapes.add_shape(
        MSO_SHAPE.OVAL,
        Inches(10.47),
        Inches(1.27),
        Inches(1.27),
        Inches(1.34),
    )
    shackle.fill.background()
    shackle.line.color.rgb = CORAL
    shackle.line.width = Pt(2.0)

    add_rect(frame, 10.36, 1.86, 1.49, 0.54, fill=BONE, line=BONE)
    add_rect(frame, 10.47, 2.03, 1.27, 0.86, fill=BONE, line=CORAL, width=2.0)

    keyhole = frame.slide.shapes.add_shape(
        MSO_SHAPE.OVAL,
        Inches(11.00),
        Inches(2.25),
        Inches(0.20),
        Inches(0.20),
    )
    keyhole.fill.solid()
    keyhole.fill.fore_color.rgb = BLACK
    keyhole.line.color.rgb = BLACK
    add_line(frame, 11.10, 2.41, 11.10, 2.67, color=BLACK, width=1.5)

    add_text(
        frame,
        "CIPHERTEXT AT REST",
        9.91,
        3.06,
        2.40,
        0.24,
        font=MONO_FONT,
        size=9.3,
        color=CORAL,
        bold=True,
        align=PP_ALIGN.CENTER,
    )


def build_security(prs: Presentation) -> SlideFrame:
    """Build the technically accurate emergency-profile security slide."""
    copy = SLIDES[5]
    frame = add_slide(prs, copy.index, copy.section)

    add_text(
        frame,
        "SECURITY / VERIFY BEFORE DECRYPT",
        0.80,
        0.38,
        4.2,
        0.22,
        font=MONO_FONT,
        size=8.5,
        color=MUTED,
        bold=True,
    )
    add_text(
        frame,
        copy.title,
        0.78,
        0.66,
        8.35,
        0.72,
        font=DISPLAY_FONT,
        size=34,
        color=BLACK,
    )
    add_text(
        frame,
        copy.message,
        0.81,
        1.43,
        8.35,
        0.56,
        size=13.5,
        color=MUTED,
    )

    _add_seal(frame)

    add_text(
        frame,
        "PUBLIC EMERGENCY RESOLVER",
        0.84,
        2.38,
        3.45,
        0.24,
        font=MONO_FONT,
        size=9.5,
        color=CORAL,
        bold=True,
    )
    add_text(
        frame,
        "CONSENT IS NOT A STEP",
        5.42,
        2.38,
        3.42,
        0.24,
        font=MONO_FONT,
        size=9.5,
        color=MUTED,
        bold=True,
        align=PP_ALIGN.RIGHT,
    )

    step_x = (0.95, 2.92, 4.89, 6.86)
    add_line(frame, 1.03, 3.04, 8.70, 3.04, color=BLACK, width=1.25)
    steps = (
        ("01", "OPAQUE RANDOM TOKEN", "16 random bytes / 32 hex characters"),
        ("02", "PROFILE LOOKUP", "Locate the encrypted profile"),
        ("03", "HMAC VERIFY", "Integrity of stored encrypted profile"),
        ("04", "AES-GCM DECRYPT", "Open only after integrity passes"),
    )
    for index, (number, label, detail) in enumerate(steps):
        x = step_x[index]
        node = frame.slide.shapes.add_shape(
            MSO_SHAPE.OVAL,
            Inches(x),
            Inches(2.96),
            Inches(0.16),
            Inches(0.16),
        )
        node.fill.solid()
        node.fill.fore_color.rgb = CORAL
        node.line.color.rgb = CORAL
        add_text(
            frame,
            number,
            x,
            2.68,
            0.48,
            0.22,
            font=MONO_FONT,
            size=9,
            color=CORAL,
            bold=True,
        )
        add_text(
            frame,
            label,
            x,
            3.28,
            1.83,
            0.38,
            font=MONO_FONT,
            size=9.8,
            color=BLACK,
            bold=True,
        )
        add_text(
            frame,
            detail,
            x,
            3.78,
            1.83,
            0.62,
            size=9.2,
            color=MUTED,
        )

    stamp = frame.slide.shapes.add_shape(
        MSO_SHAPE.OVAL,
        Inches(8.30),
        Inches(4.42),
        Inches(1.45),
        Inches(1.45),
    )
    stamp.fill.background()
    stamp.line.color.rgb = CORAL
    stamp.line.width = Pt(1.75)
    add_text(
        frame,
        "TAMPER = REJECT",
        8.45,
        4.99,
        1.15,
        0.28,
        font=MONO_FONT,
        size=8.1,
        color=CORAL,
        bold=True,
        align=PP_ALIGN.CENTER,
    )

    add_rect(frame, 0.84, 5.57, 11.68, 0.78, fill=BLACK, line=BLACK)
    add_rect(frame, 0.84, 5.57, 0.12, 0.78, fill=CORAL, line=CORAL)
    add_text(
        frame,
        "LONGITUDINAL / HOSPITAL ACCESS",
        1.16,
        5.74,
        3.12,
        0.24,
        font=MONO_FONT,
        size=8.8,
        color=CORAL,
        bold=True,
    )
    add_text(
        frame,
        "HOSPITAL RECORDS  /  JWT + ROLE + CONSENT",
        4.16,
        5.70,
        6.15,
        0.31,
        font=MONO_FONT,
        size=11.8,
        color=BONE,
        bold=True,
    )
    add_text(
        frame,
        "NOT THE PUBLIC RESOLVER",
        9.55,
        5.76,
        2.55,
        0.22,
        font=MONO_FONT,
        size=7.6,
        color=BONE_2,
        bold=True,
        align=PP_ALIGN.RIGHT,
    )

    add_footer(frame)
    set_notes(frame, copy.notes)
    return frame


__all__ = ["build_architecture", "build_experience", "build_security"]
