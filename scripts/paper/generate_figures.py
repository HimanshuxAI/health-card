"""Generate grayscale IJIRT figures for the ABHA health-card manuscript."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "docs" / "paper" / "figures"

INK = "#1c1917"
LIGHT = "#f5f2ea"
PAPER = "#ffffff"
MID = "#d6d3d1"
DARK = "#a8a29e"
ACCENT = "#57534e"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    font_path = "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf"
    return ImageFont.truetype(font_path, size)


def _rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, outline: str = INK, radius: int = 14, width: int = 3) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _text_center(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, size: int, fill: str = INK, bold: bool = False) -> None:
    font = _font(size, bold)
    draw.text(xy, text, font=font, fill=fill, anchor="mm")


def _arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], width: int = 5, fill: str = INK, head: int = 18) -> None:
    draw.line([start, end], fill=fill, width=width)
    x1, y1 = start
    x2, y2 = end
    angle = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    if angle == 0:
        return
    ux, uy = (x2 - x1) / angle, (y2 - y1) / angle
    left = (x2 - head * ux + head * 0.55 * uy, y2 - head * uy - head * 0.55 * ux)
    right = (x2 - head * ux - head * 0.55 * uy, y2 - head * uy + head * 0.55 * ux)
    draw.polygon([(x2, y2), left, right], fill=fill)


def generate_architecture(path: Path) -> None:
    width, height = 2400, 1360
    image = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(image)
    _text_center(draw, (width // 2, 100), "Next.js Role-Based Frontend: Patient, Hospital, Admin, Public Scanner", 36, bold=True)
    _rounded(draw, (270, 170, 2130, 270), LIGHT)
    _text_center(draw, (width // 2, 220), "HTTPS API Calls  /api/identity, /api/records, /api/abdm, /api/nhcx, /api/sos", 26)

    _rounded(draw, (1050, 350, 1350, 460), MID)
    _text_center(draw, (width // 2, 405), "NGINX Gateway", 30, bold=True)
    _text_center(draw, (width // 2, 520), "Routing, rate limiting, service isolation", 24)

    service_boxes = [
        ("Identity & Auth", "JWT, bcrypt, RBAC, eKYC, consent", "identity.db", 270),
        ("Records & Encryption", "AES-128-GCM, HMAC, QR, records", "records.db", 690),
        ("ABDM & FHIR Engine", "FHIR bundles, care contexts, trace", "abdm.db", 1110),
        ("NHCX Claims Hub", "Bills, FHIR Claim, adjudication", "nhcx.db", 1530),
        ("SOS & Notification", "WebSocket alerts, GPS, SMTP", "sos.db", 1950),
    ]
    _arrow(draw, (1200, 460), (1200, 540), width=6)
    for title, sub, db, left in service_boxes:
        top, bottom = 650, 810
        _rounded(draw, (left, top, left + 180, bottom), LIGHT)
        _text_center(draw, (left + 90, top + 48), title, 24, bold=True)
        _text_center(draw, (left + 90, top + 104), sub, 15)
        _arrow(draw, (1200, 550), (left + 90, top - 10), width=4)
        _rounded(draw, (left + 20, 880, left + 160, 940), MID)
        _text_center(draw, (left + 90, 910), db, 22)
        _arrow(draw, (left + 90, 810), (left + 90, 875), width=4)

    _text_center(draw, (width // 2, 1090), "Simulation Boundaries", 30, bold=True)
    _rounded(draw, (270, 1130, 1080, 1250), MID)
    _text_center(draw, (675, 1170), "Locally simulated ABDM gateway", 25, bold=True)
    _text_center(draw, (675, 1215), "FHIR conversion, care context, trace log", 20)
    _rounded(draw, (1320, 1130, 2130, 1250), MID)
    _text_center(draw, (1725, 1170), "Locally simulated NHCX gateway", 25, bold=True)
    _text_center(draw, (1725, 1215), "Claim, adjudication, state transition", 20)
    image.save(path, "PNG", dpi=(300, 300), optimize=True)


def generate_emergency_flow(path: Path) -> None:
    width, height = 2400, 1180
    image = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(image)
    steps = [
        ("Patient Card", "Rotating QR token", 180),
        ("Responder Scan", "Token or QR link", 630),
        ("Token Lookup", "Active token check", 1080),
        ("Integrity Check", "HMAC-SHA256", 1530),
        ("AES-128-GCM", "Decrypt profile", 1980),
    ]
    for title, sub, left in steps:
        _rounded(draw, (left, 180, left + 240, 320), LIGHT)
        _text_center(draw, (left + 120, 225), title, 25, bold=True)
        _text_center(draw, (left + 120, 280), sub, 20)
    for i in range(len(steps) - 1):
        _arrow(draw, (steps[i][2] + 240, 250), (steps[i + 1][2] - 10, 250), width=5)

    profile_fields = ["Blood group", "Drug allergies", "Chronic conditions", "Medications", "Emergency contacts"]
    _rounded(draw, (180, 480, 1080, 810), MID)
    _text_center(draw, (630, 530), "Displayed Trauma Profile", 28, bold=True)
    for i, field in enumerate(profile_fields):
        draw.text((240, 585 + i * 45), field, font=_font(23), fill=INK)

    _rounded(draw, (1320, 480, 2220, 810), MID)
    _text_center(draw, (1770, 530), "Optional Emergency Response", 28, bold=True)
    _text_center(draw, (1770, 590), "GPS-tagged SOS alert", 24)
    _arrow(draw, (1080, 620), (1315, 620), width=6)
    _rounded(draw, (1420, 630, 1970, 720), LIGHT)
    _text_center(draw, (1695, 675), "WebSocket broadcast to hospital dashboard", 23)
    _arrow(draw, (1695, 720), (1695, 745), width=4)
    _rounded(draw, (1420, 750, 1970, 840), LIGHT)
    _text_center(draw, (1695, 795), "SMTP email to registered contacts", 23)

    _text_center(draw, (width // 2, 940), "Control points", 28, bold=True)
    controls = [
        "No login for emergency profile resolution",
        "HMAC verification precedes ciphertext handling",
        "Token replacement invalidates prior QR links",
        "Disclosed profile limited to emergency fields",
    ]
    for i, control in enumerate(controls):
        col = i % 2
        row = i // 2
        x = 330 if col == 0 else 1330
        y = 995 + row * 55
        draw.text((x, y), "•  " + control, font=_font(23), fill=INK)
    image.save(path, "PNG", dpi=(300, 300), optimize=True)


def generate_claim_flow(path: Path) -> None:
    width, height = 2400, 1160
    image = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(image)
    _text_center(draw, (width // 2, 85), "Hospital Record and Claim Synchronization", 34, bold=True)

    boxes = [
        ("Clinical Event", "Prescription or diagnostic report", 220),
        ("FHIR R4 Mapping", "MedicationRequest or DiagnosticReport", 810),
        ("ABDM Care Context", "Consent and trace log", 1400),
        ("Itemized Bill", "Hospital ledger", 1990),
    ]
    for title, sub, left in boxes:
        _rounded(draw, (left, 180, left + 200, 320), LIGHT)
        _text_center(draw, (left + 100, 225), title, 24, bold=True)
        _text_center(draw, (left + 100, 280), sub, 18)
    for i in range(len(boxes) - 1):
        _arrow(draw, (boxes[i][2] + 200, 250), (boxes[i + 1][2] - 10, 250), width=5)

    _rounded(draw, (570, 440, 1830, 610), MID)
    _text_center(draw, (1200, 495), "FHIR Claim Resource", 30, bold=True)
    _text_center(draw, (1200, 555), "resourceType: Claim  |  itemized line entries  |  bill total", 24)
    _arrow(draw, (2090, 320), (1810, 445), width=6)

    states = [("SUBMITTED", 420), ("ADJUDICATED", 900), ("APPROVED", 1380), ("REJECTED", 1860)]
    for state, left in states:
        _rounded(draw, (left, 720, left + 280, 820), MID if state not in ("APPROVED", "REJECTED") else DARK)
        _text_center(draw, (left + 140, 770), state, 24, bold=True)
    _arrow(draw, (700, 820), (895, 820), width=5)
    _arrow(draw, (1180, 820), (1375, 820), width=5)
    _arrow(draw, (1660, 820), (1855, 820), width=5)

    _text_center(draw, (width // 2, 920), "Transition validation and outcome", 28, bold=True)
    rules = [
        "Only valid state transitions accepted",
        "Administrative adjudication produces decision",
        "Insurer note and out-of-pocket estimate persisted",
        "Simulated NHCX exchange is logged for audit",
    ]
    for i, rule in enumerate(rules):
        col = i % 2
        row = i // 2
        x = 390 if col == 0 else 1330
        y = 975 + row * 55
        draw.text((x, y), "•  " + rule, font=_font(23), fill=INK)
    image.save(path, "PNG", dpi=(300, 300), optimize=True)


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    generate_architecture(FIGURES / "architecture.png")
    generate_emergency_flow(FIGURES / "emergency_flow.png")
    generate_claim_flow(FIGURES / "claim_flow.png")
    for path in sorted(FIGURES.glob("*.png")):
        print(path)


if __name__ == "__main__":
    main()
