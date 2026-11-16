from __future__ import annotations

from pathlib import Path

from PIL import ImageFont


DPI = 96
PPT_POINTS_PER_INCH = 72
HEIGHT_SAFETY_FACTOR = 1.08
MINIMUM_HEIGHT_MARGIN_INCHES = 0.02
FALLBACK_WIDTH_FACTOR = 1.08

_FONT_PATHS: dict[str, dict[bool, Path]] = {
    "Georgia": {
        False: Path("/System/Library/Fonts/Supplemental/Georgia.ttf"),
        True: Path("/System/Library/Fonts/Supplemental/Georgia Bold.ttf"),
    },
    "Arial": {
        False: Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        True: Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
    },
    "Courier New": {
        False: Path("/System/Library/Fonts/Supplemental/Courier New.ttf"),
        True: Path("/System/Library/Fonts/Supplemental/Courier New Bold.ttf"),
    },
}
_FALLBACK_FONT_PATHS = {
    False: Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    True: Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
}


def _load_font(
    *, font_name: str, font_size_pt: float, bold: bool
) -> tuple[ImageFont.FreeTypeFont, bool]:
    """Load the requested macOS font, or a documented conservative fallback."""
    font_px = max(1, round(font_size_pt / PPT_POINTS_PER_INCH * DPI))
    requested_path = _FONT_PATHS.get(font_name, {}).get(bold)
    if requested_path is not None and requested_path.is_file():
        return ImageFont.truetype(str(requested_path), font_px), False

    fallback_path = _FALLBACK_FONT_PATHS[bold]
    if fallback_path.is_file():
        return ImageFont.truetype(str(fallback_path), font_px), True

    return ImageFont.load_default(size=font_px), True


def _wrap_paragraph(
    text: str, *, font: ImageFont.FreeTypeFont, max_width_px: int
) -> list[str]:
    if not text:
        return [""]

    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if not current or font.getlength(candidate) <= max_width_px:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def measure_wrapped_text_height(
    text: str,
    *,
    width_inches: float,
    font_name: str,
    font_size_pt: float,
    bold: bool = False,
    line_spacing: float = 1.0,
) -> float:
    """Measure wrapped PowerPoint text height in inches.

    Font sizes use PowerPoint points, rendered at 96 DPI. Explicit newlines
    start new lines and long paragraphs wrap at word boundaries. The returned
    height includes an 8% safety factor plus a 0.02-inch minimum margin.

    If a requested macOS font file is absent, matching-weight Arial is used
    and measured at 108% width to remain conservative. If no fallback font file
    exists, Pillow's default font is used with the same conservative factors.
    """
    if width_inches <= 0:
        raise ValueError("Text width must be positive")
    if font_size_pt <= 0:
        raise ValueError("Font size must be positive")
    if not text:
        return 0.0

    font, used_fallback = _load_font(
        font_name=font_name,
        font_size_pt=font_size_pt,
        bold=bold,
    )
    width_factor = FALLBACK_WIDTH_FACTOR if used_fallback else 1.0
    max_width_px = max(1, round(width_inches * DPI / width_factor))

    line_count = 0
    for paragraph in text.split("\n"):
        line_count += len(_wrap_paragraph(paragraph, font=font, max_width_px=max_width_px))

    ascent, descent = font.getmetrics()
    raw_height_inches = (
        line_count * (ascent + descent) * max(0.1, line_spacing) / DPI
    )
    return (
        raw_height_inches * HEIGHT_SAFETY_FACTOR
        + MINIMUM_HEIGHT_MARGIN_INCHES
    )


__all__ = ["measure_wrapped_text_height"]
