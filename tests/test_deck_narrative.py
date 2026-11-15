import math
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Inches

from deck.builder import build_presentation
from deck.content import SLIDES


APPROVED_TITLES = (
    "At 03:12, the ambulance doesn’t need a login.",
    "Critical context arrives fragmented.",
    "One scan. The right context. Immediately.",
)


def _texts(slide) -> list[str]:
    return [shape.text for shape in slide.shapes if hasattr(shape, "text")]


def _assert_rotation_aware_bounds(prs: Presentation) -> None:
    tolerance = Inches(0.01)
    for slide in prs.slides:
        for shape in slide.shapes:
            angle = math.radians(shape.rotation or 0.0)
            half_width = (
                abs(shape.width * math.cos(angle))
                + abs(shape.height * math.sin(angle))
            ) / 2
            half_height = (
                abs(shape.width * math.sin(angle))
                + abs(shape.height * math.cos(angle))
            ) / 2
            center_x = shape.left + shape.width / 2
            center_y = shape.top + shape.height / 2

            assert center_x - half_width >= -tolerance
            assert center_y - half_height >= -tolerance
            assert center_x + half_width <= prs.slide_width + tolerance
            assert center_y + half_height <= prs.slide_height + tolerance


def test_builds_three_native_narrative_slides_with_exact_copy(tmp_path: Path) -> None:
    output = tmp_path / "nested" / "deck.pptx"

    result = build_presentation(output)

    assert result == output
    assert output.is_file()
    assert output.stat().st_size > 0

    prs = Presentation(output)
    assert len(prs.slides) == 3

    for slide, copy, title in zip(prs.slides, SLIDES[:3], APPROVED_TITLES, strict=True):
        assert title in _texts(slide)
        assert slide.notes_slide.notes_text_frame.text == copy.notes.strip()

    assert {
        "EMERGENCY ACCESS / SY1512",
        "Aarav Mehta",
        "14-XXXX-XXXX-XXXX",
        "BLOOD GROUP  O+",
        "ALLERGY  Penicillin",
        "CONSENT  Active",
        "Group SY1512 · School of Computing · MIT-ADT University",
    }.issubset(set(_texts(prs.slides[0])))

    assert {
        "03:12",
        "AM · CITY HOSPITAL",
        "Allergies?",
        "Medications?",
        "Conditions?",
        "Coverage?",
        "CONTEXT GAP",
        (
            "The responder gets a login screen while the patient gets an "
            "emergency."
        ),
    }.issubset(set(_texts(prs.slides[1])))

    assert {
        "TOKEN LOOKUP",
        "HMAC VERIFY",
        "AES-GCM OPEN",
        "CONSENT GATE",
        "BLOOD GROUP",
        "O+",
        "ALLERGIES",
        "03",
        "CONDITIONS",
        "05",
        "RETRIEVAL TARGET",
        "<800 ms",
    }.issubset(set(_texts(prs.slides[2])))


def test_narrative_slides_use_only_native_qr_images_and_one_card_corner(
    tmp_path: Path,
) -> None:
    output = tmp_path / "deck.pptx"
    build_presentation(output)
    prs = Presentation(output)

    for index, slide in enumerate(prs.slides, start=1):
        pictures = sum(
            shape.shape_type == MSO_SHAPE_TYPE.PICTURE for shape in slide.shapes
        )
        expected_pictures = 1 if index in {1, 3} else 0
        assert pictures == expected_pictures
        assert all(shape.shape_type != MSO_SHAPE_TYPE.GROUP for shape in slide.shapes)

    rounded_rectangles = [
        len(slide._element.xpath('.//p:spPr/a:prstGeom[@prst="roundRect"]'))
        for slide in prs.slides
    ]
    assert rounded_rectangles == [1, 0, 0]


def test_narrative_slides_contain_no_gradients_and_stay_in_bounds(
    tmp_path: Path,
) -> None:
    output = tmp_path / "deck.pptx"
    build_presentation(output)

    prs = Presentation(output)
    for slide in prs.slides:
        assert not slide._element.xpath(".//a:gradFill")
    _assert_rotation_aware_bounds(prs)
