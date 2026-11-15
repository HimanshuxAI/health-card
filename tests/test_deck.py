from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

from deck.builder import build_presentation
from deck.validation import validate_presentation


EXPECTED_TITLES = [
    "At 03:12, the ambulance doesn’t need a login.",
    "Critical context arrives fragmented.",
    "One scan. The right context. Immediately.",
    "One patient. Three workspaces.",
    "Anatomy of a health card.",
    "Sealed by default. Opened by need.",
    "Native data. No translation drama.",
    "Panic → panel → people.",
    "Measured, not marketed.",
    "A health record that arrives before the ambulance does.",
]


def test_deck_has_ten_slides_with_expected_titles(tmp_path: Path) -> None:
    output = tmp_path / "deck.pptx"
    build_presentation(output)

    prs = Presentation(output)
    assert len(prs.slides) == 10
    all_text = [
        "\n".join(shape.text for shape in slide.shapes if hasattr(shape, "text"))
        for slide in prs.slides
    ]
    for title, slide_text in zip(EXPECTED_TITLES, all_text, strict=True):
        assert title in slide_text


def test_deck_has_notes_and_no_out_of_bounds_shapes(tmp_path: Path) -> None:
    output = tmp_path / "deck.pptx"
    build_presentation(output)
    prs = Presentation(output)

    for index, slide in enumerate(prs.slides, start=1):
        assert slide.notes_slide.notes_text_frame.text.strip(), (
            f"slide {index} missing notes"
        )
        for shape in slide.shapes:
            assert shape.left >= 0
            assert shape.top >= 0
            assert shape.left + shape.width <= prs.slide_width + Inches(0.01)
            assert shape.top + shape.height <= prs.slide_height + Inches(0.01)


def test_deck_avoids_gradient_and_template_shapes(tmp_path: Path) -> None:
    output = tmp_path / "deck.pptx"
    build_presentation(output)
    prs = Presentation(output)
    errors = validate_presentation(prs)
    assert errors == []
