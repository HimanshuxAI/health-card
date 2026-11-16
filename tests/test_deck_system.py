import hashlib
import math
from pathlib import Path

import pytest
from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.slide import Slide
from pptx.util import Inches

from deck.assets import required_screenshot
from deck.builder import build_presentation
from deck.content import SLIDES
from deck.text_metrics import measure_wrapped_text_height
from deck.theme import BONE_2, CORAL, OFF_WHITE


SCREENSHOT_NAMES = (
    "patient.png",
    "hospital.png",
    "hospital_sos.png",
    "admin.png",
    "admin_trace.png",
)
SCREENSHOT_DIR = Path(__file__).resolve().parents[1] / "deck" / "assets" / "screenshots"
EXPECTED_SYSTEM_TITLES = (
    "One patient. Three workspaces.",
    "Anatomy of a health card.",
    "Sealed by default. Opened by need.",
)


def _texts(slide: Slide) -> list[str]:
    return [shape.text for shape in slide.shapes if hasattr(shape, "text")]


def _picture_blobs(slide: Slide) -> list[bytes]:
    return [
        shape.image.blob
        for shape in slide.shapes
        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE
    ]


def _assert_rotation_aware_bounds(prs: Presentation) -> None:
    tolerance = Inches(0.01)
    for slide_index, slide in enumerate(prs.slides, start=1):
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

            assert center_x - half_width >= -tolerance, (
                f"slide {slide_index} shape starts outside the canvas"
            )
            assert center_y - half_height >= -tolerance, (
                f"slide {slide_index} shape starts outside the canvas"
            )
            assert center_x + half_width <= prs.slide_width + tolerance, (
                f"slide {slide_index} shape exceeds the right canvas edge"
            )
            assert center_y + half_height <= prs.slide_height + tolerance, (
                f"slide {slide_index} shape exceeds the bottom canvas edge"
            )


def _assert_every_text_shape_fits(prs: Presentation) -> None:
    for slide_index, slide in enumerate(prs.slides, start=1):
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
                f"slide {slide_index} text overflows: {shape.text!r} needs "
                f"{measured_height:.3f}in, has {available_height:.3f}in"
            )


@pytest.fixture
def full_deck(tmp_path: Path) -> tuple[Path, Presentation]:
    output = tmp_path / "ten-slide-deck.pptx"

    build_presentation(output)

    assert output.is_file()
    assert output.stat().st_size > 0
    return output, Presentation(output)


def test_system_builder_builds_ten_slides_with_system_pages_four_to_six(
    full_deck: tuple[Path, Presentation],
) -> None:
    _, prs = full_deck

    assert len(prs.slides) == 10


def test_system_slides_have_exact_titles_messages_and_notes(
    full_deck: tuple[Path, Presentation],
) -> None:
    _, prs = full_deck

    for slide, copy, title in zip(
        list(prs.slides)[3:6], SLIDES[3:6], EXPECTED_SYSTEM_TITLES, strict=True
    ):
        texts = _texts(slide)
        assert title in texts
        assert copy.message in texts
        assert slide.notes_slide.notes_text_frame.text == copy.notes.strip()
        assert slide.notes_slide.notes_text_frame.text.strip()


def test_experience_slide_uses_exactly_three_real_project_screenshots(
    full_deck: tuple[Path, Presentation],
) -> None:
    _, prs = full_deck
    slide = prs.slides[3]
    texts = _texts(slide)

    assert {"CARRY IT", "USE IT", "AUDIT IT", "PATIENT", "HOSPITAL", "ADMIN"}.issubset(
        set(texts)
    )

    blobs = _picture_blobs(slide)
    assert len(blobs) == 3

    expected_hashes = {
        hashlib.sha256((SCREENSHOT_DIR / name).read_bytes()).hexdigest()
        for name in ("patient.png", "hospital.png", "admin_trace.png")
    }
    actual_hashes = {hashlib.sha256(blob).hexdigest() for blob in blobs}
    assert actual_hashes == expected_hashes


def test_experience_lanes_are_unequal_and_joined_by_one_coral_route(
    full_deck: tuple[Path, Presentation],
) -> None:
    _, prs = full_deck
    slide = prs.slides[3]
    pictures = [
        shape
        for shape in slide.shapes
        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE
    ]
    routes = [
        shape
        for shape in slide.shapes
        if shape.shape_type == MSO_SHAPE_TYPE.FREEFORM
    ]

    assert len(pictures) == 3
    assert len({picture.width for picture in pictures}) == 3
    assert len(routes) == 1
    assert routes[0].line.color.rgb == CORAL


def test_experience_screenshots_are_tightly_cropped_to_product_content(
    full_deck: tuple[Path, Presentation],
) -> None:
    _, prs = full_deck
    pictures = [
        shape
        for shape in prs.slides[3].shapes
        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE
    ]

    assert len(pictures) == 3
    for picture in pictures:
        assert picture.crop_left >= 0.04
        assert picture.crop_right >= 0.30
        assert picture.crop_bottom >= 0.20


def test_all_required_screenshots_are_valid_nonempty_png_files() -> None:
    for name in SCREENSHOT_NAMES:
        path = required_screenshot(SCREENSHOT_DIR / name)

        assert path.is_file()
        assert path.stat().st_size > 0
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            assert image.format == "PNG"
            assert image.width >= 1440
            assert image.height >= 900


def test_architecture_slide_names_all_services_rails_and_patient_view(
    full_deck: tuple[Path, Presentation],
) -> None:
    _, prs = full_deck
    texts = set(_texts(prs.slides[4]))

    assert {
        "NEXT.JS FRONTEND",
        "NGINX API GATEWAY",
        "ONE PATIENT VIEW",
        "Identity",
        "JWT · RBAC · eKYC · Consent",
        "identity.db",
        "Records",
        "Profiles · FHIR records · AES-GCM · QR",
        "records.db",
        "ABDM",
        "Care contexts · HL7 FHIR v4 · trace",
        "abdm.db",
        "NHCX",
        "Bills · FHIR Claim · adjudication",
        "nhcx.db",
        "SOS",
        "WebSocket · GPS · email",
        "sos.db",
    }.issubset(texts)


def test_architecture_slide_uses_varied_rows_and_coral_patient_view_block(
    full_deck: tuple[Path, Presentation],
) -> None:
    _, prs = full_deck
    slide = prs.slides[4]
    autoshapes = [
        shape
        for shape in slide.shapes
        if shape.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE
    ]
    service_rows = [
        shape
        for shape in autoshapes
        if shape.height == Inches(0.72)
        and shape.fill.fore_color.rgb in {OFF_WHITE, BONE_2}
    ]
    patient_view_blocks = [
        shape
        for shape in autoshapes
        if shape.fill.fore_color.rgb == CORAL
        and shape.width < Inches(2.0)
        and shape.height > Inches(4.0)
    ]

    assert len(service_rows) == 5
    assert len({row.width for row in service_rows}) == 5
    assert len(patient_view_blocks) == 1


def test_security_slide_keeps_emergency_resolver_technically_accurate(
    full_deck: tuple[Path, Presentation],
) -> None:
    _, prs = full_deck
    texts = _texts(prs.slides[5])

    assert {
        "OPAQUE RANDOM TOKEN",
        "PROFILE LOOKUP",
        "HMAC VERIFY",
        "AES-GCM DECRYPT",
        "16 random bytes / 32 hex characters",
        "HOSPITAL RECORDS  /  JWT + ROLE + CONSENT",
        "TAMPER = REJECT",
        "CIPHERTEXT AT REST",
    }.issubset(set(texts))
    assert "CONSENT GATE" not in texts


def test_security_slide_orders_resolver_steps_and_separates_consent_access(
    full_deck: tuple[Path, Presentation],
) -> None:
    _, prs = full_deck
    texts = _texts(prs.slides[5])
    resolver_steps = (
        "OPAQUE RANDOM TOKEN",
        "PROFILE LOOKUP",
        "HMAC VERIFY",
        "AES-GCM DECRYPT",
    )

    assert tuple(text for text in texts if text in resolver_steps) == resolver_steps
    assert "CONSENT IS NOT A STEP" in texts
    assert "HOSPITAL RECORDS  /  JWT + ROLE + CONSENT" in texts
    assert "NOT THE PUBLIC RESOLVER" in texts


def test_explicit_assets_directory_is_used_without_ambient_state(
    tmp_path: Path,
) -> None:
    assets_dir = tmp_path / "project-screenshots"
    assets_dir.mkdir()
    for name in SCREENSHOT_NAMES:
        (assets_dir / name).write_bytes((SCREENSHOT_DIR / name).read_bytes())

    output = tmp_path / "explicit-assets.pptx"
    build_presentation(output, assets_dir=assets_dir)

    prs = Presentation(output)
    assert len(prs.slides) == 10
    assert len(_picture_blobs(prs.slides[3])) == 3
    assert len(_picture_blobs(prs.slides[7])) == 1


def test_full_deck_has_no_gradients_out_of_bounds_or_text_overflow(
    full_deck: tuple[Path, Presentation],
) -> None:
    _, prs = full_deck

    for slide in prs.slides:
        assert not slide._element.xpath(".//a:gradFill")
    _assert_rotation_aware_bounds(prs)
    _assert_every_text_shape_fits(prs)


def test_total_rounded_rectangle_count_stays_at_or_below_four(
    full_deck: tuple[Path, Presentation],
) -> None:
    _, prs = full_deck

    rounded_rectangles = sum(
        len(slide._element.xpath('.//p:spPr/a:prstGeom[@prst="roundRect"]'))
        for slide in prs.slides
    )

    assert rounded_rectangles <= 4
