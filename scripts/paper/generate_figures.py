"""Generate column-width IJIRT figures for the ABHA health-card manuscript.

Every figure is drawn on a 900 px canvas that is placed at 3.0 in in the
DOCX, i.e. exactly one 3.0 in column of the IJIRT two-column layout.
At 300 dpi the conversion is ``pt = px * 0.24``, so 32 px == 7.7 pt and
36 px == 8.6 pt. Nothing below 30 px (7.2 pt) is used for body text.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "docs" / "paper" / "figures"

CANVAS_W = 900
MARGIN = 22
BOX_W = CANVAS_W - 2 * MARGIN

INK = "#111111"
RULE = "#111111"
FILL = "#f2f2f2"
FILL_SOFT = "#fafafa"
FILL_ACCENT = "#e4e4e4"
WHITE = "#ffffff"

FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

PX_TITLE = 36  # 8.6 pt
PX_LABEL = 32  # 7.7 pt
PX_BODY = 30  # 7.2 pt
PX_SMALL = 28  # 6.7 pt (annotations only)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size)


def _width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> float:
    return draw.textlength(text, font=font)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and _width(draw, candidate, font) > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _box(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    *,
    title: str,
    detail: str | None = None,
    fill: str = FILL,
    dashed: bool = False,
    badge: str | None = None,
) -> None:
    """Draw one rounded-free rectangular node."""
    if dashed:
        _dashed_rect(draw, x, y, x + w, y + h)
    else:
        draw.rectangle((x, y, x + w, y + h), fill=fill, outline=RULE, width=3)

    pad = 16
    inner_w = w - 2 * pad
    title_font = _font(PX_TITLE, bold=True)
    detail_font = _font(PX_BODY)
    badge_font = _font(PX_SMALL, bold=True)

    badge_w = 0
    if badge:
        badge_w = int(_width(draw, badge, badge_font)) + 22
        bx = x + w - pad - badge_w
        draw.rectangle((bx, y + 14, bx + badge_w, y + 14 + 38), fill=WHITE, outline=RULE, width=2)
        draw.text((bx + badge_w / 2, y + 33), badge, font=badge_font, fill=INK, anchor="mm")

    title_lines = _wrap(draw, title, title_font, inner_w - badge_w)
    title_y = y + 14
    for line in title_lines:
        draw.text((x + pad, title_y), line, font=title_font, fill=INK)
        title_y += int(PX_TITLE * 1.18)

    if detail:
        detail_y = title_y + 4
        for line in _wrap(draw, detail, detail_font, inner_w):
            draw.text((x + pad, detail_y), line, font=detail_font, fill=INK)
            detail_y += int(PX_BODY * 1.22)


def _dashed_rect(draw: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int, dash: int = 14, gap: int = 9) -> None:
    for x in range(x0, x1, dash + gap):
        draw.line((x, y0, min(x + dash, x1), y0), fill=RULE, width=3)
        draw.line((x, y1, min(x + dash, x1), y1), fill=RULE, width=3)
    for y in range(y0, y1, dash + gap):
        draw.line((x0, y, x0, min(y + dash, y1)), fill=RULE, width=3)
        draw.line((x1, y, x1, min(y + dash, y1)), fill=RULE, width=3)


def _arrow_down(draw: ImageDraw.ImageDraw, x: int, y0: int, y1: int, label: str | None = None) -> None:
    draw.line((x, y0, x, y1 - 12), fill=RULE, width=3)
    draw.polygon([(x, y1), (x - 10, y1 - 16), (x + 10, y1 - 16)], fill=RULE)
    if label:
        font = _font(PX_SMALL)
        draw.text((x + 14, (y0 + y1) / 2), label, font=font, fill=INK, anchor="lm")


def _arrow_right(draw: ImageDraw.ImageDraw, x0: int, x1: int, y: int) -> None:
    draw.line((x0, y, x1 - 12, y), fill=RULE, width=3)
    draw.polygon([(x1, y), (x1 - 16, y - 10), (x1 - 16, y + 10)], fill=RULE)


def _chip(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, text: str, *, fill: str = FILL) -> None:
    draw.rectangle((x, y, x + w, y + h), fill=fill, outline=RULE, width=3)
    font = _font(PX_BODY, bold=True)
    draw.text((x + w / 2, y + h / 2), text, font=font, fill=INK, anchor="mm")


def _note(draw: ImageDraw.ImageDraw, y: int, text: str) -> None:
    font = _font(PX_SMALL)
    draw.text((CANVAS_W / 2, y), text, font=font, fill=INK, anchor="ma")


def _save(image: Image.Image, path: Path) -> None:
    image.save(path, "PNG", dpi=(300, 300), optimize=True)


def generate_architecture(path: Path) -> None:
    height = 900
    image = Image.new("RGB", (CANVAS_W, height), WHITE)
    draw = ImageDraw.Draw(image)

    y = MARGIN
    _box(draw, MARGIN, y, BOX_W, 84, title="Next.js role-based frontends", detail="Patient · Hospital · Admin · Public scanner", fill=FILL_ACCENT)
    y += 84
    _arrow_down(draw, CANVAS_W // 2, y + 6, y + 44, label="HTTPS / JSON")
    y += 50

    _box(draw, MARGIN, y, BOX_W, 78, title="NGINX API gateway", detail="Routing · rate limiting · service isolation", fill=FILL)
    y += 78
    _arrow_down(draw, CANVAS_W // 2, y + 6, y + 42)
    y += 48

    services = [
        ("Identity & auth", "JWT, bcrypt, RBAC, consents, simulated eKYC", "identity.db"),
        ("Records & crypto", "AES-128-GCM sealing, HMAC, QR tokens, records", "records.db"),
        ("ABDM / FHIR engine", "FHIR bundles, care contexts, integration trace", "abdm.db"),
        ("NHCX claims hub", "Bills, FHIR Claim conversion, adjudication", "nhcx.db"),
        ("SOS & notification", "WebSocket broadcast, GPS tags, SMTP fallback", "sos.db"),
    ]
    row_h = 74
    for title, detail, db in services:
        _box(draw, MARGIN, y, BOX_W, row_h, title=title, detail=detail, fill=FILL_SOFT, badge=db)
        y += row_h + 8
    y -= 8

    _arrow_down(draw, CANVAS_W // 2, y + 6, y + 40)
    y += 46

    band_h = 176
    _dashed_rect(draw, MARGIN, y, CANVAS_W - MARGIN, y + band_h)
    band_label = _font(PX_SMALL, bold=True)
    label_w = int(_width(draw, "LOCAL SIMULATION BOUNDARY", band_label)) + 24
    draw.rectangle((MARGIN + 14, y - 15, MARGIN + 14 + label_w, y + 15), fill=WHITE)
    draw.text((MARGIN + 26, y), "LOCAL SIMULATION BOUNDARY", font=band_label, fill=INK, anchor="lm")

    inner_x = MARGIN + 18
    inner_w = (BOX_W - 36 - 18) // 2
    inner_top = y + 26
    _box(draw, inner_x, inner_top, inner_w, 126, title="Simulated ABDM gateway", detail="FHIR conversion, care contexts, trace log", fill=FILL)
    _box(draw, inner_x + inner_w + 18, inner_top, inner_w, 126, title="Simulated NHCX gateway", detail="Claim build, adjudication, transitions", fill=FILL)
    y += band_h + 10

    _note(draw, y, "Five FastAPI services, each owning one SQLite database; no live national-gateway connectivity.")
    y += 34

    image = image.crop((0, 0, CANVAS_W, y + 8))
    _save(image, path)


def generate_emergency_flow(path: Path) -> None:
    image = Image.new("RGB", (CANVAS_W, 1000), WHITE)
    draw = ImageDraw.Draw(image)

    y = MARGIN
    steps = [
        ("1  Patient health card", "Rotating 32-byte QR token"),
        ("2  Responder scan", "QR link or manual token entry"),
        ("3  Token lookup", "Active-state check"),
        ("4  Integrity check", "HMAC-SHA256 signature verified"),
        ("5  Decrypt", "AES-128-GCM sealed profile opened"),
    ]
    step_h = 70
    for title, detail in steps:
        _box(draw, MARGIN, y, BOX_W, step_h, title=title, detail=detail, fill=FILL)
        y += step_h
        if title != steps[-1][0]:
            _arrow_down(draw, CANVAS_W // 2, y + 4, y + 34)
            y += 38

    y += 6
    _box(
        draw,
        MARGIN,
        y,
        BOX_W,
        118,
        title="Displayed trauma profile",
        detail="Blood group · Drug allergies · Chronic conditions · Medications · Emergency contacts",
        fill=FILL_ACCENT,
    )
    y += 118

    y += 34
    _box(
        draw,
        MARGIN,
        y,
        BOX_W,
        92,
        title="Optional SOS dispatch",
        detail="WebSocket to hospital dashboard · SMTP to registered contacts",
        fill=WHITE,
        dashed=True,
    )
    y += 92

    y += 32
    controls = [
        "No login required for emergency resolution",
        "Integrity verified before ciphertext is opened",
        "Rotating token invalidates the previous QR link",
        "Only the five emergency fields are disclosed",
    ]
    control_font = _font(PX_BODY)
    for control in controls:
        draw.text((MARGIN + 6, y), "•", font=control_font, fill=INK)
        draw.text((MARGIN + 30, y), control, font=control_font, fill=INK)
        y += int(PX_BODY * 1.32)

    image = image.crop((0, 0, CANVAS_W, y + 10))
    _save(image, path)


def generate_claim_flow(path: Path) -> None:
    image = Image.new("RGB", (CANVAS_W, 1000), WHITE)
    draw = ImageDraw.Draw(image)

    y = MARGIN
    steps = [
        ("1  Clinical event", "Prescription or diagnostic report"),
        ("2  FHIR R4 mapping", "MedicationRequest or DiagnosticReport"),
        ("3  Care context", "Consent artifact and integration trace"),
        ("4  Itemized bill", "Description and amount line items"),
        ("5  FHIR Claim resource", "Status set to SUBMITTED"),
    ]
    step_h = 70
    for title, detail in steps:
        _box(draw, MARGIN, y, BOX_W, step_h, title=title, detail=detail, fill=FILL)
        y += step_h
        if title != steps[-1][0]:
            _arrow_down(draw, CANVAS_W // 2, y + 4, y + 34)
            y += 38

    y += 6
    _box(draw, MARGIN, y, BOX_W, 74, title="Adjudication state machine", detail="Only defined transitions are accepted", fill=FILL_ACCENT)
    y += 74

    chip_y = y + 30
    chip_h = 56
    chip_w = 196
    x1 = MARGIN
    x2 = MARGIN + chip_w + 46
    x3 = MARGIN + 2 * (chip_w + 46)
    _chip(draw, x1, chip_y, chip_w, chip_h, "SUBMITTED")
    _arrow_right(draw, x1 + chip_w, x2, chip_y + chip_h // 2)
    _chip(draw, x2, chip_y, chip_w, chip_h, "ADJUDICATED")
    _arrow_right(draw, x2 + chip_w, x3 - 8, chip_y + chip_h // 2)
    _chip(draw, x3, chip_y - 26, chip_w, chip_h, "APPROVED", fill=FILL_SOFT)
    _chip(draw, x3, chip_y + 30, chip_w, chip_h, "REJECTED", fill=FILL_SOFT)
    y = chip_y + chip_h + 56

    _note(draw, y, "Invalid transitions raise errors; the decision note and out-of-pocket estimate are persisted.")
    y += 34
    _note(draw, y, "The NHCX exchange is locally simulated and logged for audit.")
    y += 30

    image = image.crop((0, 0, CANVAS_W, y + 8))
    _save(image, path)


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    generate_architecture(FIGURES / "architecture.png")
    generate_emergency_flow(FIGURES / "emergency_flow.png")
    generate_claim_flow(FIGURES / "claim_flow.png")
    for path in sorted(FIGURES.glob("*.png")):
        with Image.open(path) as image:
            print(f"{path} {image.size[0]}x{image.size[1]}")


if __name__ == "__main__":
    main()
