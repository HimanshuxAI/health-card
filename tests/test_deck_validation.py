from io import BytesIO
from typing import get_type_hints

import pytest
from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.presentation import Presentation as PresentationClass
from pptx.util import Inches

from deck.content import SLIDES
from deck.validation import validate_presentation


def _png_bytes() -> bytes:
    image = BytesIO()
    Image.new("RGB", (2, 2), "white").save(image, format="PNG")
    return image.getvalue()


def _add_text(slide, text: str, y: float = 0.2) -> None:
    shape = slide.shapes.add_textbox(
        Inches(0.2), Inches(y), Inches(9.5), Inches(0.5)
    )
    shape.text_frame.text = text


def _add_notes(slide) -> None:
    notes_frame = slide.notes_slide.notes_text_frame
    assert notes_frame is not None
    notes_frame.text = "Speaker notes"


def _add_picture(slide, x: float) -> None:
    slide.shapes.add_picture(
        BytesIO(_png_bytes()),
        Inches(x),
        Inches(0.2),
        width=Inches(0.5),
        height=Inches(0.5),
    )


def _valid_presentation(
    *,
    slide_count: int = 10,
    slide4_pictures: int = 3,
    slide8_pictures: int = 1,
    split_first_title: bool = False,
    missing_notes_slide: int | None = None,
):
    prs = Presentation()
    for index in range(slide_count):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        title = SLIDES[index].title if index < len(SLIDES) else "Additional slide"

        if split_first_title and index == 0:
            split_at = len(title) // 2
            _add_text(slide, title[:split_at])
            _add_text(slide, title[split_at:], y=0.8)
        else:
            _add_text(slide, title)

        if missing_notes_slide != index:
            _add_notes(slide)

        if index == 3:
            for picture_index in range(slide4_pictures):
                _add_picture(slide, 0.2 + picture_index * 0.6)
        if index == 7:
            for picture_index in range(slide8_pictures):
                _add_picture(slide, 0.2 + picture_index * 0.6)

    return prs


def test_validation_accepts_exact_title_in_individual_shape() -> None:
    prs = _valid_presentation()
    slide = prs.slides[0]

    assert SLIDES[0].title in [shape.text for shape in slide.shapes]
    assert validate_presentation(prs) == []


def test_validation_rejects_title_concatenated_across_shapes() -> None:
    prs = _valid_presentation(split_first_title=True)

    errors = validate_presentation(prs)

    assert "slide 1: missing approved title" in errors


def test_validation_reports_missing_notes() -> None:
    prs = _valid_presentation(missing_notes_slide=0)

    errors = validate_presentation(prs)

    assert "slide 1: missing speaker notes" in errors


def test_validation_does_not_create_missing_notes_parts() -> None:
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    has_notes_before = slide.part.has_notes_slide
    package_parts_before = len(list(prs.part.package.iter_parts()))
    assert has_notes_before is False

    errors = validate_presentation(prs)

    assert "slide 1: missing speaker notes" in errors
    assert slide.part.has_notes_slide is has_notes_before
    assert len(list(prs.part.package.iter_parts())) == package_parts_before


@pytest.mark.parametrize(
    ("edge", "expected_error"),
    [
        ("left", "slide 1: shape starts outside the canvas"),
        ("top", "slide 1: shape starts outside the canvas"),
        ("right", "slide 1: shape exceeds the right canvas edge"),
        ("bottom", "slide 1: shape exceeds the bottom canvas edge"),
    ],
)
def test_validation_catches_each_canvas_edge(edge: str, expected_error: str) -> None:
    prs = _valid_presentation()
    slide = prs.slides[0]
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(1), Inches(1), Inches(1), Inches(1)
    )
    if edge == "left":
        shape.left = -Inches(0.5)
    elif edge == "top":
        shape.top = -Inches(0.5)
    elif edge == "right":
        shape.left = prs.slide_width - Inches(0.25)
    elif edge == "bottom":
        shape.top = prs.slide_height - Inches(0.25)

    errors = validate_presentation(prs)

    assert expected_error in errors


def test_validation_catches_rotated_shape_overflow() -> None:
    prs = _valid_presentation()
    slide = prs.slides[0]
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(8.9), Inches(0.5), Inches(1), Inches(2)
    )
    shape.rotation = 45

    errors = validate_presentation(prs)

    assert "slide 1: shape exceeds the right canvas edge" in errors


def test_validation_detects_gradient_fill() -> None:
    prs = _valid_presentation()
    slide = prs.slides[0]
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(1), Inches(1), Inches(1), Inches(1)
    )
    shape.fill.gradient()

    errors = validate_presentation(prs)

    assert "slide 1: gradient fill is not allowed" in errors


def test_validation_enforces_rounded_rectangle_limit() -> None:
    prs = _valid_presentation()
    for index in range(5):
        slide = prs.slides[index]
        slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(2),
            Inches(2),
            Inches(1),
            Inches(1),
        )

    errors = validate_presentation(prs)

    assert "expected at most 4 rounded rectangles, found 5" in errors


@pytest.mark.parametrize("slide_count", [9, 11])
def test_validation_reports_slide_count(slide_count: int) -> None:
    prs = _valid_presentation(slide_count=slide_count)

    errors = validate_presentation(prs)

    assert f"expected 10 slides, found {slide_count}" in errors


@pytest.mark.parametrize(
    ("slide4_pictures", "slide8_pictures", "slide_number", "required", "found"),
    [
        (1, 1, 4, 3, 1),
        (2, 1, 4, 3, 2),
        (4, 1, 4, 3, 4),
        (3, 0, 8, 1, 0),
        (3, 2, 8, 1, 2),
    ],
)
def test_validation_requires_exact_project_screenshot_counts(
    slide4_pictures: int,
    slide8_pictures: int,
    slide_number: int,
    required: int,
    found: int,
) -> None:
    prs = _valid_presentation(
        slide4_pictures=slide4_pictures,
        slide8_pictures=slide8_pictures,
    )

    errors = validate_presentation(prs)

    noun = "project screenshot" if required == 1 else "project screenshots"
    assert (
        f"slide {slide_number}: expected exactly {required} {noun}, found {found}"
        in errors
    )


def test_validate_presentation_uses_presentation_class_annotation() -> None:
    assert get_type_hints(validate_presentation)["prs"] is PresentationClass
