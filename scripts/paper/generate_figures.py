"""Generate compact, publication-quality IJIRT figures.

900 px @ 300 DPI = 3.0 in column width.
Target height: ~400-500 px (1.3-1.7 in) per figure.
Clean academic style: minimal, structured, legible.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "docs" / "paper" / "figures"

CANVAS_W = 900
MARGIN = 20
CONTENT_W = CANVAS_W - 2 * MARGIN

# Professional academic colors
INK = "#111111"
MUTED = "#555555"
LIGHT = "#fafafa"
BOX_BG = "#ffffff"
BOX_LINE = "#cccccc"
BOX_LINE_STRONG = "#999999"
ACCENT = "#2c5aa0"
ACCENT_BG = "#eef2f7"
DASHED = "#aaaaaa"
GREEN = "#28a745"
GREEN_BG = "#e8f5e9"
RED = "#dc3545"
RED_BG = "#fdeaea"

FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

# Font sizes (px at 300 DPI)
# 10pt = 42px, 9pt = 38px, 8pt = 34px, 7pt = 29px
FS_HDR = 40      # 9.5pt - figure title (not used, caption is separate)
FS_TITLE = 36    # 8.5pt - box titles
FS_BODY = 32     # 7.5pt - body text
FS_SMALL = 28    # 6.5pt - annotations
FS_BADGE = 26    # 6pt - badges


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def _width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> float:
    return draw.textlength(text, font=font)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        cand = f"{cur} {w}".strip()
        if cur and _width(draw, cand, font) > max_w:
            lines.append(cur)
            cur = w
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


def _box(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
         title: str, detail: str | None = None,
         fill: str = BOX_BG, line_color: str = BOX_LINE, line_w: int = 2,
         radius: int = 4, badge: str | None = None) -> None:
    """Clean minimal box."""
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill, outline=line_color, width=line_w)

    pad = 12
    inner_w = w - 2 * pad
    title_font = _font(FS_TITLE, bold=True)
    detail_font = _font(FS_BODY)
    badge_font = _font(FS_BADGE, bold=True)

    badge_w = 0
    if badge:
        bw = int(_width(draw, badge, badge_font)) + 10
        bx = x + w - pad - bw
        by = y + 8
        draw.rounded_rectangle((bx, by, bx + bw, by + 22), radius=3, fill=LIGHT, outline=BOX_LINE, width=1)
        draw.text((bx + bw/2, by + 11), badge, font=badge_font, fill=MUTED, anchor="mm")
        badge_w = bw

    # Title
    title_lines = _wrap(draw, title, title_font, inner_w - badge_w)
    ty = y + 10
    for line in title_lines:
        draw.text((x + pad, ty), line, font=title_font, fill=INK)
        ty += int(FS_TITLE * 1.2)

    # Detail
    if detail:
        dy = ty + 3
        for line in _wrap(draw, detail, detail_font, inner_w):
            draw.text((x + pad, dy), line, font=detail_font, fill=MUTED)
            dy += int(FS_BODY * 1.25)


def _arrow_down(draw: ImageDraw.ImageDraw, cx: int, y0: int, y1: int) -> None:
    draw.line((cx, y0, cx, y1 - 10), fill=INK, width=2)
    draw.polygon([(cx, y1), (cx - 6, y1 - 10), (cx + 6, y1 - 10)], fill=INK)


def _arrow_right(draw: ImageDraw.ImageDraw, x0: int, x1: int, y: int) -> None:
    draw.line((x0, y, x1 - 10, y), fill=INK, width=2)
    draw.polygon([(x1, y), (x1 - 8, y - 6), (x1 - 8, y + 6)], fill=INK)


def _chip(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
          text: str, fill: str = LIGHT, line_color: str = BOX_LINE, text_color: str = INK) -> None:
    draw.rounded_rectangle((x, y, x + w, y + h), radius=4, fill=fill, outline=line_color, width=2)
    font = _font(FS_BODY, bold=True)
    draw.text((x + w/2, y + h/2), text, font=font, fill=text_color, anchor="mm")


def _dashed_box(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
                label: str | None = None) -> None:
    dash, gap = 8, 5
    for xx in range(x, x + w, dash + gap):
        draw.line((xx, y, min(xx + dash, x + w), y), fill=DASHED, width=1)
        draw.line((xx, y + h, min(xx + dash, x + w), y + h), fill=DASHED, width=1)
    for yy in range(y, y + h, dash + gap):
        draw.line((x, yy, x, min(yy + dash, y + h)), fill=DASHED, width=1)
        draw.line((x + w, yy, x + w, min(yy + dash, y + h)), fill=DASHED, width=1)

    if label:
        font = _font(FS_SMALL, bold=True)
        lw = int(_width(draw, label, font)) + 10
        lx = x + 10
        draw.rectangle((lx, y - 9, lx + lw, y + 9), fill=LIGHT)
        draw.text((lx + 5, y), label, font=font, fill=MUTED, anchor="lm")


def _note(draw: ImageDraw.ImageDraw, cx: int, y: int, text: str) -> None:
    font = _font(FS_SMALL)
    draw.text((cx, y), text, font=font, fill=MUTED, anchor="ma")


def _save(img: Image.Image, path: Path) -> None:
    img.save(path, "PNG", dpi=(300, 300), optimize=True)


# ============================================================
# FIGURE 1: Architecture
# ============================================================
def generate_architecture(path: Path) -> None:
    img = Image.new("RGB", (CANVAS_W, 1000), LIGHT)
    draw = ImageDraw.Draw(img)

    y = MARGIN
    cx = CANVAS_W // 2

    # Frontends
    _box(draw, MARGIN, y, CONTENT_W, 58,
         "Next.js Frontends", "Patient · Hospital · Admin · Scanner",
         fill=ACCENT_BG, line_color=ACCENT)
    y += 58 + 10
    _arrow_down(draw, cx, y, y + 18)
    y += 18 + 10

    # Gateway
    _box(draw, MARGIN, y, CONTENT_W, 54,
         "NGINX Gateway", "Routing · Rate Limiting · Isolation",
         fill=BOX_BG, line_color=BOX_LINE_STRONG)
    y += 54 + 10
    _arrow_down(draw, cx, y, y + 18)
    y += 18 + 10

    # Services
    services = [
        ("Identity & Auth", "JWT · bcrypt · RBAC · Consents · eKYC", "identity.db"),
        ("Records & Crypto", "AES-128-GCM · HMAC · QR Tokens · Records", "records.db"),
        ("ABDM / FHIR", "FHIR Bundles · Care Contexts · Trace", "abdm.db"),
        ("NHCX Claims", "Bills · FHIR Claim · Adjudication", "nhcx.db"),
        ("SOS & Notify", "WebSocket · GPS · SMTP Fallback", "sos.db"),
    ]
    for title, detail, badge in services:
        _box(draw, MARGIN, y, CONTENT_W, 50, title, detail, fill=BOX_BG, badge=badge)
        y += 50 + 6
    y -= 6

    y += 10
    _arrow_down(draw, cx, y, y + 18)
    y += 18 + 10

    # Simulation boundary
    band_h = 100
    _dashed_box(draw, MARGIN, y, CONTENT_W, band_h, "LOCAL SIMULATION BOUNDARY")
    inner_y = y + 20
    inner_w = (CONTENT_W - 30) // 2
    _box(draw, MARGIN + 12, inner_y, inner_w, 66,
         "Sim. ABDM", "FHIR · Care Contexts · Trace", fill=BOX_BG)
    _box(draw, MARGIN + 18 + inner_w, inner_y, inner_w, 66,
         "Sim. NHCX", "Claim · Adjudication · Transitions", fill=BOX_BG)
    y += band_h + 10

    _note(draw, cx, y, "Five FastAPI services, each owning one SQLite database; no live national-gateway connectivity.")
    y += 18

    img = img.crop((0, 0, CANVAS_W, y + 8))
    _save(img, path)


# ============================================================
# FIGURE 2: Emergency Flow
# ============================================================
def generate_emergency_flow(path: Path) -> None:
    img = Image.new("RGB", (CANVAS_W, 1000), LIGHT)
    draw = ImageDraw.Draw(img)

    y = MARGIN
    cx = CANVAS_W // 2

    steps = [
        ("1  Patient Card", "Rotating 32-byte QR token"),
        ("2  Responder Scan", "QR link or manual entry"),
        ("3  Token Lookup", "Active-state check"),
        ("4  Integrity Check", "HMAC-SHA256 verified"),
        ("5  Decrypt", "AES-128-GCM opened"),
    ]
    step_h = 48

    for i, (title, detail) in enumerate(steps):
        _box(draw, MARGIN, y, CONTENT_W, step_h, title, detail, fill=BOX_BG)
        y += step_h
        if i < len(steps) - 1:
            _arrow_down(draw, cx, y + 4, y + 16)
            y += 20

    y += 8

    # Trauma profile
    _box(draw, MARGIN, y, CONTENT_W, 72,
         "Trauma Profile", "Blood Group · Allergies · Conditions · Medications · Contacts",
         fill=ACCENT_BG, line_color=ACCENT)
    y += 72 + 12

    # Optional SOS (dashed)
    _box(draw, MARGIN, y, CONTENT_W, 56,
         "Optional SOS", "WebSocket → Hospital · SMTP → Contacts",
         fill=LIGHT, line_color=DASHED)
    y += 56 + 10

    # Control points
    controls = [
        "No login for emergency resolution",
        "HMAC verified before decryption",
        "Rotating token invalidates prior QR",
        "Only 5 emergency fields disclosed",
    ]
    font = _font(FS_BODY)
    for c in controls:
        draw.text((MARGIN + 6, y), "•", font=font, fill=INK)
        draw.text((MARGIN + 24, y), c, font=font, fill=MUTED)
        y += int(FS_BODY * 1.3)

    y += 8

    img = img.crop((0, 0, CANVAS_W, y + 8))
    _save(img, path)


# ============================================================
# FIGURE 3: Claim Flow
# ============================================================
def generate_claim_flow(path: Path) -> None:
    img = Image.new("RGB", (CANVAS_W, 800), LIGHT)
    draw = ImageDraw.Draw(img)

    y = MARGIN
    cx = CANVAS_W // 2

    steps = [
        ("1  Clinical Event", "Prescription or Diagnostic Report"),
        ("2  FHIR R4 Mapping", "MedicationRequest / DiagnosticReport"),
        ("3  Care Context", "Consent · Integration Trace"),
        ("4  Itemized Bill", "Description & Amount Lines"),
        ("5  FHIR Claim", "Status → SUBMITTED"),
    ]
    step_h = 48

    for i, (title, detail) in enumerate(steps):
        _box(draw, MARGIN, y, CONTENT_W, step_h, title, detail, fill=BOX_BG)
        y += step_h
        if i < len(steps) - 1:
            _arrow_down(draw, cx, y + 4, y + 16)
            y += 20

    y += 8

    # Adjudication
    _box(draw, MARGIN, y, CONTENT_W, 48,
         "Adjudication", "Only defined transitions accepted",
         fill=ACCENT_BG, line_color=ACCENT)
    y += 48 + 12

    # State machine
    chip_h = 38
    chip_w = 150
    gap = 20
    x1 = MARGIN
    x2 = x1 + chip_w + gap
    x3 = x2 + chip_w + gap

    _chip(draw, x1, y, chip_w, chip_h, "SUBMITTED")
    _arrow_right(draw, x1 + chip_w, x2, y + chip_h // 2)
    _chip(draw, x2, y, chip_w, chip_h, "ADJUDICATED")
    _arrow_right(draw, x2 + chip_w, x3 - 8, y + chip_h // 2)
    _chip(draw, x3, y - 24, chip_w, chip_h, "APPROVED", fill=GREEN_BG, line_color=GREEN, text_color=GREEN)
    _chip(draw, x3, y + 24, chip_w, chip_h, "REJECTED", fill=RED_BG, line_color=RED, text_color=RED)

    y += chip_h + 28

    _note(draw, cx, y, "Invalid transitions raise errors; decision note & out-of-pocket persisted.")
    y += 20
    _note(draw, cx, y, "NHCX exchange locally simulated; logged for audit.")
    y += 16

    img = img.crop((0, 0, CANVAS_W, y + 8))
    _save(img, path)


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    generate_architecture(FIGURES / "architecture.png")
    generate_emergency_flow(FIGURES / "emergency_flow.png")
    generate_claim_flow(FIGURES / "claim_flow.png")
    for p in sorted(FIGURES.glob("*.png")):
        with Image.open(p) as im:
            print(f"{p.name} {im.size[0]}x{im.size[1]}")


if __name__ == "__main__":
    main()