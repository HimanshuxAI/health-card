#!/usr/bin/env python3
"""Generate report figures used by the Annexure 6 project report."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "report" / "figures"
FONT = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
NAVY = "#17324D"
BLUE = "#DCEAF6"
GREEN = "#DCE9E2"
GREEN_DARK = "#2F6B4F"
GOLD = "#C7A34A"
INK = "#1D252C"
MUTED = "#5F6B76"
WHITE = "#FFFFFF"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT
    if bold:
        bold_candidates = [
            "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        ]
        for candidate in bold_candidates:
            if Path(candidate).exists():
                path = candidate
                break
    return ImageFont.truetype(path, size)


def centered(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, fnt, fill=INK):
    left, top, right, bottom = box
    bbox = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=6, align="center")
    width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.multiline_text(
        ((left + right - width) / 2, (top + bottom - height) / 2),
        text,
        font=fnt,
        fill=fill,
        spacing=6,
        align="center",
    )


def rounded_box(draw: ImageDraw.ImageDraw, box, fill, outline=NAVY, radius=18, width=3):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def arrow(draw: ImageDraw.ImageDraw, start, end, fill=NAVY, width=4):
    draw.line([start, end], fill=fill, width=width)
    x, y = end
    draw.polygon([(x, y), (x - 14, y - 9), (x - 14, y + 9)], fill=fill)


def project_plan() -> Image.Image:
    image = Image.new("RGB", (1600, 820), WHITE)
    draw = ImageDraw.Draw(image)
    draw.text((70, 42), "Figure 4.1  Waterfall-Style Project Plan", font=font(48, True), fill=NAVY)
    draw.line((70, 112, 1530, 112), fill=GOLD, width=5)

    steps = [
        ("1\nREQUIREMENTS", "Synopsis analysis\nScope and non-goals"),
        ("2\nDESIGN", "Architecture\nData model and API contract"),
        ("3\nIMPLEMENTATION", "Five backend services\nRole-based frontend"),
        ("4\nTESTING", "Unit and integration tests\nEnd-to-end workflow"),
        ("5\nDOCUMENTATION", "Report, research paper\nReview and handoff"),
    ]
    left, top, width, height, gap = 70, 220, 270, 250, 35
    fills = [BLUE, BLUE, GREEN, GREEN, BLUE]
    for index, ((title, detail), fill) in enumerate(zip(steps, fills)):
        x1 = left + index * (width + gap)
        x2 = x1 + width
        rounded_box(draw, (x1, top, x2, top + height), fill)
        centered(draw, (x1 + 12, top + 18, x2 - 12, top + 100), title, font(27, True), NAVY)
        centered(draw, (x1 + 15, top + 100, x2 - 15, top + height - 20), detail, font(23), INK)
        if index < len(steps) - 1:
            arrow(draw, (x2 + 5, top + height / 2), (x2 + gap - 5, top + height / 2))

    draw.text((70, 545), "Review artifact produced at each phase", font=font(31, True), fill=GREEN_DARK)
    artifacts = ["Approved scope", "Design specification", "Working prototype", "Test evidence", "Submission package"]
    y = 610
    for artifact in artifacts:
        draw.ellipse((76, y + 8, 94, y + 26), fill=GOLD)
        draw.text((115, y), artifact, font=font(28), fill=INK)
        y += 42
    draw.text((930, 610), "Backend and frontend work proceeded in parallel\nafter the API contract was stable.", font=font(27), fill=MUTED, spacing=8)
    return image


def service_ownership() -> Image.Image:
    image = Image.new("RGB", (1600, 960), WHITE)
    draw = ImageDraw.Draw(image)
    draw.text((70, 38), "Figure 6.1  Service Ownership and Data Boundaries", font=font(46, True), fill=NAVY)
    draw.line((70, 105, 1530, 105), fill=GOLD, width=5)

    rounded_box(draw, (250, 145, 1350, 245), GREEN, outline=GREEN_DARK)
    centered(draw, (270, 150, 1330, 238), "Next.js Frontend\nPatient  |  Hospital  |  Admin  |  Public Scanner", font(32, True), NAVY)
    arrow(draw, (800, 245), (800, 305))

    rounded_box(draw, (455, 305, 1145, 385), BLUE)
    centered(draw, (475, 308, 1125, 382), "NGINX Gateway  |  Routing and Rate Limiting", font(31, True), NAVY)

    service_names = ["IDENTITY", "RECORDS", "ABDM / FHIR", "NHCX", "SOS"]
    db_names = ["identity.db", "records.db", "abdm.db", "nhcx.db", "sos.db"]
    fills = [BLUE, GREEN, BLUE, GREEN, BLUE]
    left, top, width, height, gap = 55, 455, 270, 125, 30
    for index, (name, db, fill) in enumerate(zip(service_names, db_names, fills)):
        x1 = left + index * (width + gap)
        x2 = x1 + width
        arrow(draw, (800, 385), ((x1 + x2) // 2, top - 12), fill=MUTED, width=3)
        rounded_box(draw, (x1, top, x2, top + height), fill, radius=14)
        centered(draw, (x1 + 10, top + 12, x2 - 10, top + height - 10), f"{index + 1}  {name}", font(28, True), NAVY)
        arrow(draw, ((x1 + x2) // 2, top + height), ((x1 + x2) // 2, top + height + 48), fill=MUTED, width=3)
        rounded_box(draw, (x1 + 35, top + height + 48, x2 - 35, top + height + 118), WHITE, outline=GREEN_DARK, radius=12, width=2)
        centered(draw, (x1 + 40, top + height + 51, x2 - 40, top + height + 115), db, font(25), INK)

    draw.rounded_rectangle((95, 800, 1505, 900), radius=16, fill="#F6F2E8", outline=GOLD, width=3)
    centered(
        draw,
        (115, 805, 1485, 895),
        "Each service owns one database and validates authorization independently.\nABDM and NHCX exchanges are locally simulated; no national gateway is called.",
        font(27),
        NAVY,
    )
    return image


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    project_plan().save(OUT / "project_plan.png", optimize=True)
    service_ownership().save(OUT / "service_ownership.png", optimize=True)
    print(f"Generated report figures in {OUT}")


if __name__ == "__main__":
    main()
