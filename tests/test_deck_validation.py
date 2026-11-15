from pptx import Presentation

from deck.validation import validate_presentation


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
