import math
from io import BytesIO
from pathlib import Path

import pytest
import zxingcpp
from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.slide import Slide
from pptx.util import Inches

from deck.builder import build_presentation
from deck.content import SLIDES
from deck.text_metrics import measure_wrapped_text_height
from deck.theme import CORAL


APPROVED_TITLES = (
    "At 03:12, the ambulance doesn’t need a login.",
    "Critical context arrives fragmented.",
    "One scan. The right context. Immediately.",
)
VALID_SCAN_TOKEN = "0123456789abcdef0123456789abcdef"


def _texts(slide: Slide) -> list[str]:
    return [shape.text for shape in slide.shapes if hasattr(shape, "text")]


def _decoded_picture_urls(slide: Slide) -> list[str]:
    urls: list[str] = []
    for shape in slide.shapes:
        if shape.shape_type != MSO_SHAPE_TYPE.PICTURE:
            continue
        with Image.open(BytesIO(shape.image.blob)) as image:
            urls.extend(barcode.text for barcode in zxingcpp.read_barcodes(image))
    return urls


@pytest.fixture(autouse=True)
def _without_ambient_scan_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ABHA_SCAN_TOKEN", raising=False)


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


def _rotated_corners(shape) -> list[tuple[float, float]]:
    angle = math.radians(shape.rotation or 0.0)
    center_x = shape.left + shape.width / 2
    center_y = shape.top + shape.height / 2
    half_width = shape.width / 2
    half_height = shape.height / 2
    offsets = (
        (-half_width, -half_height),
        (half_width, -half_height),
        (half_width, half_height),
        (-half_width, half_height),
    )
    return [
        (
            center_x + dx * math.cos(angle) - dy * math.sin(angle),
            center_y + dx * math.sin(angle) + dy * math.cos(angle),
        )
        for dx, dy in offsets
    ]


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


def test_tokenized_qr_is_embedded_on_cover_and_solution(tmp_path: Path) -> None:
    output = tmp_path / "tokenized.pptx"

    build_presentation(output, scan_token=VALID_SCAN_TOKEN)

    prs = Presentation(output)
    expected_url = f"http://localhost:3000/scan?t={VALID_SCAN_TOKEN}"
    assert _decoded_picture_urls(prs.slides[0]) == [expected_url]
    assert _decoded_picture_urls(prs.slides[2]) == [expected_url]
    assert "SCAN TO RESOLVE" in _texts(prs.slides[0])
    assert "SCAN TO RESOLVE" in _texts(prs.slides[2])


def test_scan_token_can_come_from_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ABHA_SCAN_TOKEN", VALID_SCAN_TOKEN)
    output = tmp_path / "environment-token.pptx"

    build_presentation(output)

    prs = Presentation(output)
    expected_url = f"http://localhost:3000/scan?t={VALID_SCAN_TOKEN}"
    assert _decoded_picture_urls(prs.slides[0]) == [expected_url]
    assert _decoded_picture_urls(prs.slides[2]) == [expected_url]


@pytest.mark.parametrize(
    "invalid_token",
    (
        "",
        "0123456789abcdef",
        "0123456789abcdef0123456789abcde",
        "0123456789abcdef0123456789abcdef0",
        "0123456789ABCDEF0123456789ABCDEF",
        "0123456789abcdefg123456789abcdef",
        123,
    ),
)
def test_invalid_scan_tokens_are_rejected(
    tmp_path: Path, invalid_token: object
) -> None:
    with pytest.raises(ValueError, match="32 lowercase hexadecimal"):
        build_presentation(tmp_path / "invalid.pptx", scan_token=invalid_token)


def test_invalid_environment_scan_token_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ABHA_SCAN_TOKEN", "not-a-token")

    with pytest.raises(ValueError, match="32 lowercase hexadecimal"):
        build_presentation(tmp_path / "invalid-environment.pptx")


def test_generic_qr_is_labelled_as_open_scanner(tmp_path: Path) -> None:
    output = tmp_path / "generic.pptx"

    build_presentation(output)

    prs = Presentation(output)
    generic_url = "http://localhost:3000/scan"
    assert _decoded_picture_urls(prs.slides[0]) == [generic_url]
    assert _decoded_picture_urls(prs.slides[2]) == [generic_url]
    assert "OPEN SCANNER" in _texts(prs.slides[0])
    assert "OPEN SCANNER" in _texts(prs.slides[2])
    assert "SCAN TO RESOLVE" not in _texts(prs.slides[0])
    assert "SCAN TO RESOLVE" not in _texts(prs.slides[2])


def test_every_nonempty_text_shape_has_enough_fixed_height(tmp_path: Path) -> None:
    output = tmp_path / "text-fit.pptx"
    build_presentation(output)
    prs = Presentation(output)

    for slide_index, slide in enumerate(list(prs.slides)[:3], start=1):
        for shape in slide.shapes:
            if not shape.has_text_frame or not shape.text.strip():
                continue
            paragraph = shape.text_frame.paragraphs[0]
            assert paragraph.runs, f"slide {slide_index} text has no styled run"
            run = paragraph.runs[0]
            assert run.font.size is not None
            font_size_pt = run.font.size.pt
            font_name = run.font.name or "Arial"
            line_spacing = (
                paragraph.line_spacing
                if isinstance(paragraph.line_spacing, (int, float))
                else 1.0
            )
            available_width = (
                shape.width
                - (shape.text_frame.margin_left or 0)
                - (shape.text_frame.margin_right or 0)
            ) / Inches(1)
            available_height = (
                shape.height
                - (shape.text_frame.margin_top or 0)
                - (shape.text_frame.margin_bottom or 0)
            ) / Inches(1)
            measured_height = measure_wrapped_text_height(
                shape.text,
                width_inches=available_width,
                font_name=font_name,
                font_size_pt=font_size_pt,
                bold=bool(run.font.bold),
                line_spacing=float(line_spacing),
            )

            assert measured_height <= available_height + 0.02, (
                f"slide {slide_index} text overflows: "
                f"{shape.text!r} needs {measured_height:.3f}in, "
                f"has {available_height:.3f}in"
            )


def test_solution_evidence_is_split_for_layout_slack(tmp_path: Path) -> None:
    output = tmp_path / "evidence.pptx"
    build_presentation(output)
    prs = Presentation(output)

    for evidence in SLIDES[2].evidence:
        assert evidence in _texts(prs.slides[2])


def test_patient_card_header_is_inset_within_rounded_card(tmp_path: Path) -> None:
    output = tmp_path / "card-header.pptx"
    build_presentation(output)
    prs = Presentation(output)
    slide = prs.slides[0]

    cards = [
        shape
        for shape in slide.shapes
        if shape._element.xpath(
            './/p:spPr/a:prstGeom[@prst="roundRect"]'
        )
    ]
    assert len(cards) == 1
    card = cards[0]

    coral_headers = [
        shape
        for shape in slide.shapes
        if shape.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE
        and shape.fill.fore_color.rgb == CORAL
        and shape.height <= Inches(0.2)
        and shape.width > Inches(4.0)
    ]
    assert len(coral_headers) == 1
    header = coral_headers[0]

    assert header.width < card.width
    assert card.width - header.width >= Inches(0.2)

    card_top_left, card_top_right, *_ = _rotated_corners(card)
    header_top_left, header_top_right, *_ = _rotated_corners(header)
    edge_x_span = card_top_right[0] - card_top_left[0]
    for header_x, header_y in (header_top_left, header_top_right):
        assert card_top_left[0] <= header_x <= card_top_right[0]
        edge_y = card_top_left[1] + (
            (header_x - card_top_left[0]) / edge_x_span
        ) * (card_top_right[1] - card_top_left[1])
        assert header_y >= edge_y - Inches(0.01)
