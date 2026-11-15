from __future__ import annotations

from dataclasses import dataclass

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

SLIDE_W = 13.333
SLIDE_H = 7.5
MARGIN = 0.65
COLUMN_GAP = 0.18

BLACK = RGBColor(0x10, 0x15, 0x12)
BONE = RGBColor(0xEE, 0xE9, 0xDE)
BONE_2 = RGBColor(0xD8, 0xD2, 0xC4)
CORAL = RGBColor(0xFF, 0x56, 0x38)
GREEN = RGBColor(0x00, 0xA8, 0x78)
OFF_WHITE = RGBColor(0xFA, 0xF8, 0xF2)
MUTED = RGBColor(0x65, 0x70, 0x69)

DISPLAY_FONT = "Georgia"
BODY_FONT = "Arial"
MONO_FONT = "Courier New"


@dataclass(frozen=True)
class SlideFrame:
    slide: object
    index: int
    section: str
    dark: bool = False


def new_presentation() -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(SLIDE_W)
    prs.slide_height = Inches(SLIDE_H)
    return prs


def add_slide(
    prs: Presentation, index: int, section: str, *, dark: bool = False
) -> SlideFrame:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    background = slide.background.fill
    background.solid()
    background.fore_color.rgb = BLACK if dark else BONE
    return SlideFrame(slide=slide, index=index, section=section, dark=dark)


def add_text(
    frame: SlideFrame,
    text: str,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    font: str = BODY_FONT,
    size: float = 18,
    color: RGBColor | None = None,
    bold: bool = False,
    align: PP_ALIGN = PP_ALIGN.LEFT,
    valign: MSO_ANCHOR = MSO_ANCHOR.TOP,
    margin: float = 0.0,
    line_spacing: float = 1.0,
) -> object:
    shape = frame.slide.shapes.add_textbox(
        Inches(x), Inches(y), Inches(w), Inches(h)
    )
    text_frame = shape.text_frame
    text_frame.clear()
    text_frame.margin_left = Inches(margin)
    text_frame.margin_right = Inches(margin)
    text_frame.margin_top = Inches(margin)
    text_frame.margin_bottom = Inches(margin)
    text_frame.word_wrap = True
    text_frame.vertical_anchor = valign

    paragraph = text_frame.paragraphs[0]
    paragraph.text = text
    paragraph.alignment = align
    paragraph.line_spacing = line_spacing

    run = paragraph.runs[0]
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color or (BONE if frame.dark else BLACK)
    return shape


def add_rect(
    frame: SlideFrame,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    fill: RGBColor,
    line: RGBColor | None = None,
    width: float = 0.75,
    radius: bool = False,
) -> object:
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shape = frame.slide.shapes.add_shape(
        shape_type, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = line or fill
    shape.line.width = Pt(width)
    if radius:
        shape.adjustments[0] = 0.08
    return shape


def add_line(
    frame: SlideFrame,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    color: RGBColor | None = None,
    width: float = 0.75,
) -> object:
    shape = frame.slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT,
        Inches(x1),
        Inches(y1),
        Inches(x2),
        Inches(y2),
    )
    shape.line.color.rgb = color or (BONE_2 if frame.dark else BLACK)
    shape.line.width = Pt(width)
    return shape


def add_footer(frame: SlideFrame) -> None:
    ink = BONE if frame.dark else BLACK
    add_text(
        frame,
        "ABHA HEALTH CARD  /  SY1512",
        MARGIN,
        7.13,
        4.0,
        0.18,
        size=7.5,
        color=ink,
        bold=True,
    )
    add_text(
        frame,
        f"{frame.index:02d}",
        12.25,
        7.08,
        0.43,
        0.22,
        font=MONO_FONT,
        size=9,
        color=ink,
        align=PP_ALIGN.RIGHT,
    )
    add_line(frame, MARGIN, 7.02, 12.68, 7.02, color=ink, width=0.5)


def set_notes(frame: SlideFrame, notes: str) -> None:
    frame.slide.notes_slide.notes_text_frame.text = notes.strip()
