from types import SimpleNamespace
from typing import get_type_hints
from unittest.mock import PropertyMock, patch

import pytest
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.presentation import Presentation
from pptx.shapes.autoshape import Shape
from pptx.shapes.connector import Connector
from pptx.slide import Slide
from pptx.util import Pt

from deck import theme
from deck.theme import (
    BLACK,
    BONE,
    BONE_2,
    CORAL,
    DISPLAY_FONT,
    add_line,
    add_rect,
    add_slide,
    add_text,
    new_presentation,
    set_notes,
)


def test_add_text_formats_every_run() -> None:
    frame = add_slide(new_presentation(), 1, "opening")

    shape = add_text(
        frame,
        "First line\nSecond line",
        1,
        1,
        4,
        1,
        font=DISPLAY_FONT,
        size=12,
        color=CORAL,
        bold=True,
    )

    runs = shape.text_frame.paragraphs[0].runs
    assert len(runs) == 2
    for run in runs:
        assert run.font.name == DISPLAY_FONT
        assert run.font.size == Pt(12)
        assert run.font.bold is True
        assert run.font.color.rgb == CORAL


def test_add_text_styles_empty_text_without_error() -> None:
    frame = add_slide(new_presentation(), 1, "opening")

    shape = add_text(
        frame,
        "",
        1,
        1,
        4,
        1,
        font=DISPLAY_FONT,
        size=12,
        color=CORAL,
        bold=True,
    )

    assert shape.text == ""
    paragraph = shape.text_frame.paragraphs[0]
    assert paragraph.font.name == DISPLAY_FONT
    assert paragraph.font.size == Pt(12)
    assert paragraph.font.bold is True
    assert paragraph.font.color.rgb == CORAL


def test_add_text_disables_autofit() -> None:
    frame = add_slide(new_presentation(), 1, "opening")

    shape = add_text(frame, "Fixed layout", 1, 1, 4, 1)

    assert shape.text_frame.auto_size == MSO_AUTO_SIZE.NONE


def test_add_slide_uses_bone_by_default_and_black_when_dark() -> None:
    prs = new_presentation()

    light = add_slide(prs, 1, "light")
    dark = add_slide(prs, 2, "dark", dark=True)

    assert light.slide.background.fill.fore_color.rgb == BONE
    assert dark.slide.background.fill.fore_color.rgb == BLACK


def test_add_text_defaults_to_bone_on_dark_and_black_otherwise() -> None:
    prs = new_presentation()
    light = add_slide(prs, 1, "light")
    dark = add_slide(prs, 2, "dark", dark=True)

    light_text = add_text(light, "Light", 1, 1, 2, 1)
    dark_text = add_text(dark, "Dark", 1, 1, 2, 1)

    light_run = light_text.text_frame.paragraphs[0].runs[0]
    dark_run = dark_text.text_frame.paragraphs[0].runs[0]
    assert light_run.font.color.rgb == BLACK
    assert dark_run.font.color.rgb == BONE


def test_add_line_defaults_to_bone_2_on_dark_and_black_otherwise() -> None:
    prs = new_presentation()
    light = add_slide(prs, 1, "light")
    dark = add_slide(prs, 2, "dark", dark=True)

    light_line = add_line(light, 1, 1, 2, 1)
    dark_line = add_line(dark, 1, 1, 2, 1)

    assert light_line.line.color.rgb == BLACK
    assert dark_line.line.color.rgb == BONE_2


def test_theme_helpers_return_actual_pptx_types() -> None:
    frame = add_slide(new_presentation(), 1, "opening")

    text_shape = add_text(frame, "Text", 1, 1, 2, 1)
    rect_shape = add_rect(frame, 1, 2, 2, 1, fill=CORAL)
    connector = add_line(frame, 1, 3, 3, 3)

    assert isinstance(text_shape, Shape)
    assert isinstance(rect_shape, Shape)
    assert isinstance(connector, Connector)
    assert get_type_hints(theme.SlideFrame)["slide"] is Slide
    assert get_type_hints(theme.new_presentation)["return"] is Presentation
    assert get_type_hints(theme.add_slide)["prs"] is Presentation
    assert get_type_hints(theme.add_text)["return"] is Shape
    assert get_type_hints(theme.add_rect)["return"] is Shape
    assert get_type_hints(theme.add_line)["return"] is Connector


def test_set_notes_raises_clear_error_when_notes_frame_is_unavailable() -> None:
    frame = add_slide(new_presentation(), 1, "opening")

    with patch.object(Slide, "notes_slide", new_callable=PropertyMock) as notes_slide:
        notes_slide.return_value = SimpleNamespace(notes_text_frame=None)
        with pytest.raises(RuntimeError, match="notes text frame is unavailable"):
            set_notes(frame, "Speaker notes")


def test_helper_docstrings_document_units_and_color_defaults() -> None:
    add_slide_doc = (theme.add_slide.__doc__ or "").lower()
    add_text_doc = (theme.add_text.__doc__ or "").lower()
    add_rect_doc = (theme.add_rect.__doc__ or "").lower()
    add_line_doc = (theme.add_line.__doc__ or "").lower()

    assert "dark=false" in add_slide_doc
    assert "bone" in add_slide_doc
    assert "dark=true" in add_slide_doc
    assert "black" in add_slide_doc
    assert "inches" in add_text_doc
    assert "margin" in add_text_doc
    assert "points" in add_text_doc
    assert "multiplier" in add_text_doc
    assert "color=none" in add_text_doc
    assert "bone" in add_text_doc
    assert "black" in add_text_doc
    assert "dark slides" in add_text_doc
    assert "otherwise" in add_text_doc
    assert "inches" in add_rect_doc
    assert "points" in add_rect_doc
    assert "fill" in add_rect_doc
    assert "inches" in add_line_doc
    assert "points" in add_line_doc
    assert "color=none" in add_line_doc
    assert "bone_2" in add_line_doc
    assert "black" in add_line_doc
    assert "dark slides" in add_line_doc
    assert "otherwise" in add_line_doc
