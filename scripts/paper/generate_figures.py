"""Generate clean, professional IJIRT figures for the ABHA health-card manuscript.

Figures are 900 px wide at 300 DPI = 3.0 in column width.
Text: 9-10pt body, 10-11pt headers, clean sans-serif.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "docs" / "paper" / "figures"

CANVAS_W = 900
MARGIN = 24
CONTENT_W = CANVAS_W - 2 * MARGIN

# Clean professional colors
INK = "#1a1a1a"
MUTED = "#4a4a4a"
RULE = "#1a1a1a"
BG = "#ffffff"
BOX_FILL = "#f7f7f7"
BOX_FILL_ALT = "#eef0f2"
ACCENT_FILL = "#e8ecf1"
ACCENT_LINE = "#2d5aa0"
DASHED_LINE = "#888888"
CHIP_FILL = "#e8ecef"
CHIP_FILL_GREEN = "#d4edda"
CHIP_FILL_RED = "#f8d7da"

FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

# Sizes in px (at 300 DPI: 1pt = 4.167px)
# Target: 9-10pt body = 37-42px, 10-11pt header = 42-46px
FS_HDR = 42      # 10pt - section headers
FS_BOX_TITLE = 38  # 9pt - box titles
FS_BODY = 34      # 8pt - body text
FS_SMALL = 30     # 7pt - annotations
FS_BADGE = 28     # 6.5pt - badges


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
         fill: str = BOX_FILL, line_color: str = RULE, line_w: int = 2,
         radius: int = 8, badge: str | None = None) -> None:
    """Clean rounded rectangle with title and optional detail."""
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill, outline=line_color, width=line_w)

    pad = 18
    inner_w = w - 2 * pad
    title_font = _font(FS_BOX_TITLE, bold=True)
    detail_font = _font(FS_BODY)
    badge_font = _font(FS_BADGE, bold=True)

    badge_w = 0
    if badge:
        bw = int(_width(draw, badge, badge_font)) + 16
        bx = x + w - pad - bw
        by = y + 12
        draw.rounded_rectangle((bx, by, bx + bw, by + 30), radius=4, fill=BG, outline=RULE, width=1)
        draw.text((bx + bw/2, by + 15), badge, font=badge_font, fill=INK, anchor="mm")
        badge_w = bw

    # Title
    title_lines = _wrap(draw, title, title_font, inner_w - badge_w)
    ty = y + 14
    for line in title_lines:
        draw.text((x + pad, ty), line, font=title_font, fill=INK)
        ty += int(FS_BOX_TITLE * 1.25)

    # Detail
    if detail:
        dy = ty + 6
        for line in _wrap(draw, detail, detail_font, inner_w):
            draw.text((x + pad, dy), line, font=detail_font, fill=MUTED)
            dy += int(FS_BODY * 1.35)


def _arrow_down(draw: ImageDraw.ImageDraw, cx: int, y0: int, y1: int) -> None:
    """Clean vertical arrow."""
    draw.line((cx, y0, cx, y1 - 14), fill=RULE, width=2)
    # Arrowhead
    draw.polygon([(cx, y1), (cx - 9, y1 - 14), (cx + 9, y1 - 14)], fill=RULE)


def _arrow_right(draw: ImageDraw.ImageDraw, x0: int, x1: int, y: int) -> None:
    draw.line((x0, y, x1 - 14, y), fill=RULE, width=2)
    draw.polygon([(x1, y), (x1 - 12, y - 9), (x1 - 12, y + 9)], fill=RULE)


def _chip(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
          text: str, fill: str = CHIP_FILL, line_color: str = RULE) -> None:
    draw.rounded_rectangle((x, y, x + w, y + h), radius=6, fill=fill, outline=line_color, width=2)
    font = _font(FS_BODY, bold=True)
    draw.text((x + w/2, y + h/2), text, font=font, fill=INK, anchor="mm")


def _dashed_box(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
                label: str | None = None) -> None:
    """Dashed boundary box with optional label."""
    dash, gap = 10, 6
    for xx in range(x, x + w, dash + gap):
        draw.line((xx, y, min(xx + dash, x + w), y), fill=DASHED_LINE, width=2)
        draw.line((xx, y + h, min(xx + dash, x + w), y + h), fill=DASHED_LINE, width=2)
    for yy in range(y, y + h, dash + gap):
        draw.line((x, yy, x, min(yy + dash, y + h)), fill=DASHED_LINE, width=2)
        draw.line((x + w, yy, x + w, min(yy + dash, y + h)), fill=DASHED_LINE, width=2)

    if label:
        font = _font(FS_SMALL, bold=True)
        lw = int(_width(draw, label, font)) + 16
        lx = x + 14
        draw.rectangle((lx, y - 12, lx + lw, y + 12), fill=BG)
        draw.text((lx + 8, y), label, font=font, fill=MUTED, anchor="lm")


def _note(draw: ImageDraw.ImageDraw, cx: int, y: int, text: str) -> None:
    font = _font(FS_SMALL)
    draw.text((cx, y), text, font=font, fill=MUTED, anchor="ma")


def _save(img: Image.Image, path: Path) -> None:
    img.save(path, "PNG", dpi=(300, 300), optimize=True)


# ============================================================
# FIGURE 1: Architecture
# ============================================================
def generate_architecture(path: Path) -> None:
    img = Image.new("RGB", (CANVAS_W, 1200), BG)
    draw = ImageDraw.Draw(img)

    y = MARGIN
    cx = CANVAS_W // 2

    # Frontends
    _box(draw, MARGIN, y, CONTENT_W, 70,
         "Next.js Frontends", "Patient · Hospital · Admin · Public Scanner",
         fill=ACCENT_FILL, line_color=ACCENT_LINE)
    y += 70 + 18
    _arrow_down(draw, cx, y, y + 28)
    y += 28 + 18

    # Gateway
    _box(draw, MARGIN, y, CONTENT_W, 66,
         "NGINX API Gateway", "Routing · Rate Limiting · Service Isolation",
         fill=BOX_FILL_ALT)
    y += 66 + 18
    _arrow_down(draw, cx, y, y + 28)
    y += 28 + 18

    # Services row
    services = [
        ("Identity & Auth", "JWT · bcrypt · RBAC · Consents · Sim. eKYC", "identity.db"),
        ("Records & Crypto", "AES-128-GCM · HMAC · QR Tokens · Records", "records.db"),
        ("ABDM / FHIR", "FHIR Bundles · Care Contexts · Trace", "abdm.db"),
        ("NHCX Claims", "Bills · FHIR Claim · Adjudication", "nhcx.db"),
        ("SOS & Notify", "WebSocket · GPS · SMTP Fallback", "sos.db"),
    ]
    row_h = 62
    for i, (title, detail, badge) in enumerate(services):
        x = MARGIN
        w = CONTENT_W
        _box(draw, x, y, w, row_h, title, detail, fill=BOX_FILL, badge=badge)
        y += row_h + 10
    y -= 10

    y += 18
    _arrow_down(draw, cx, y, y + 28)
    y += 28 + 18

    # Simulation boundary
    band_h = 140
    _dashed_box(draw, MARGIN, y, CONTENT_W, band_h, "LOCAL SIMULATION BOUNDARY")
    inner_y = y + 26
    inner_w = (CONTENT_W - 40) // 2
    _box(draw, MARGIN + 18, inner_y, inner_w, 94,
         "Simulated ABDM Gateway", "FHIR Conversion · Care Contexts · Trace Log", fill=BOX_FILL)
    _box(draw, MARGIN + 22 + inner_w, inner_y, inner_w, 94,
         "Simulated NHCX Gateway", "Claim Build · Adjudication · Transitions", fill=BOX_FILL)
    y += band_h + 22

    _note(draw, cx, y, "Five FastAPI services, each owning one SQLite database; no live national-gateway connectivity.")
    y += 30

    img = img.crop((0, 0, CANVAS_W, y + 8))
    _save(img, path)


# ============================================================
# FIGURE 2: Emergency Flow
# ============================================================
def generate_emergency_flow(path: Path) -> None:
    img = Image.new("RGB", (CANVAS_W, 1100), BG)
    draw = ImageDraw.Draw(img)

    y = MARGIN
    cx = CANVAS_W // 2

    steps = [
        ("1  Patient Health Card", "Rotating 32-byte QR token"),
        ("2  Responder Scan", "QR link or manual token entry"),
        ("3  Token Lookup", "Active-state check"),
        ("4  Integrity Check", "HMAC-SHA256 signature verified"),
        ("5  Decrypt", "AES-128-GCM sealed profile opened"),
    ]
    step_h = 62

    for i, (title, detail) in enumerate(steps):
        _box(draw, MARGIN, y, CONTENT_W, step_h, title, detail, fill=BOX_FILL)
        y += step_h
        if i < len(steps) - 1:
            _arrow_down(draw, cx, y + 6, y + 30)
            y += 36

    y += 14

    # Trauma profile box
    _box(draw, MARGIN, y, CONTENT_W, 104,
         "Displayed Trauma Profile",
         "Blood Group · Drug Allergies · Chronic Conditions · Medications · Emergency Contacts",
         fill=ACCENT_FILL, line_color=ACCENT_LINE)
    y += 104 + 24

    # Optional SOS (dashed)
    _box(draw, MARGIN, y, CONTENT_W, 78,
         "Optional SOS Dispatch",
         "WebSocket to Hospital Dashboard · SMTP to Registered Contacts",
         fill=BG, line_color=DASHED_LINE, line_w=2)
    y += 78 + 24

    # Control points
    controls = [
        "No login required for emergency resolution",
        "Integrity verified before ciphertext is opened",
        "Rotating token invalidates the previous QR link",
        "Only the five emergency fields are disclosed",
    ]
    font = _font(FS_BODY)
    for c in controls:
        draw.text((MARGIN + 8, y), "•", font=font, fill=INK)
        draw.text((MARGIN + 30, y), c, font=font, fill=MUTED)
        y += int(FS_BODY * 1.4)

    y += 14
    img = img.crop((0, 0, CANVAS_W, y + 8))
    _save(img, path)


# ============================================================
# FIGURE 3: Claim Flow
# ============================================================
def generate_claim_flow(path: Path) -> None:
    img = Image.new("RGB", (CANVAS_W, 1000), BG)
    draw = ImageDraw.Draw(img)

    y = MARGIN
    cx = CANVAS_W // 2

    steps = [
        ("1  Clinical Event", "Prescription or Diagnostic Report"),
        ("2  FHIR R4 Mapping", "MedicationRequest or DiagnosticReport"),
        ("3  Care Context", "Consent Artifact · Integration Trace"),
        ("4  Itemized Bill", "Description & Amount Line Items"),
        ("5  FHIR Claim Resource", "Status set to SUBMITTED"),
    ]
    step_h = 62

    for i, (title, detail) in enumerate(steps):
        _box(draw, MARGIN, y, CONTENT_W, step_h, title, detail, fill=BOX_FILL)
        y += step_h
        if i < len(steps) - 1:
            _arrow_down(draw, cx, y + 6, y + 30)
            y += 36

    y += 14

    # Adjudication header
    _box(draw, MARGIN, y, CONTENT_W, 60,
         "Adjudication State Machine", "Only defined transitions are accepted",
         fill=ACCENT_FILL, line_color=ACCENT_LINE)
    y += 60 + 22

    # State chips
    chip_h = 48
    chip_w = 180
    gap = 28
    x1 = MARGIN
    x2 = x1 + chip_w + gap
    x3 = x2 + chip_w + gap

    _chip(draw, x1, y, chip_w, chip_h, "SUBMITTED")
    _arrow_right(draw, x1 + chip_w, x2, y + chip_h // 2)
    _chip(draw, x2, y, chip_w, chip_h, "ADJUDICATED")
    _arrow_right(draw, x2 + chip_w, x3 - 8, y + chip_h // 2)
    _chip(draw, x3, y - 28, chip_w, chip_h, "APPROVED", fill=CHIP_FILL_GREEN, line_color="#28a745")
    _chip(draw, x3, y + 28, chip_w, chip_h, "REJECTED", fill=CHIP_FILL_RED, line_color="#dc3545")

    y += chip_h + 40

    _note(draw, cx, y, "Invalid transitions raise errors; the decision note and out-of-pocket estimate are persisted.")
    y += 28
    _note(draw, cx, y, "The NHCX exchange is locally simulated and logged for audit.")
    y += 24

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