from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path

import pytest
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Inches

from deck.assets import required_screenshot
from deck import theme
from deck.content import SLIDES
from deck.slides.report import (
    build_close,
    build_evidence,
    build_emergency,
    build_interoperability,
)
from deck.text_metrics import measure_wrapped_text_height
from deck.theme import new_presentation


SCREENSHOT = (
    Path(__file__).resolve().parents[1]
    / "deck"
    / "assets"
    / "screenshots"
    / "hospital_sos.png"
)

BUILDERS = (build_interoperability, build_emergency, build_evidence, build_close)
REPORT_COPIES = SLIDES[6:10]


def _compose(screenshot_path: Path = SCREENSHOT) -> Presentation:
    """Compose the four report pages manually, without deck.builder."""
    prs = new_presentation()
    build_interoperability(prs)
    build_emergency(prs, screenshot_path)
    build_evidence(prs)
    build_close(prs)
    return prs


def _slide_texts(slide) -> list[str]:
    return [
        shape.text
        for shape in slide.shapes
        if shape.has_text_frame and shape.text
    ]


def _first_run_font(shape):
    paragraph = shape.text_frame.paragraphs[0]
    if paragraph.runs:
        run = paragraph.runs[0]
        return run.font.name, run.font.size, run.font.bold
    return paragraph.font.name, paragraph.font.size, paragraph.font.bold


def _assert_rotation_aware_bounds(slide, slide_width, slide_height) -> None:
    tolerance = Inches(0.01)
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
        assert center_x + half_width <= slide_width + tolerance
        assert center_y + half_height <= slide_height + tolerance


def test_report_builds_exactly_four_pages() -> None:
    prs = _compose()

    assert len(list(prs.slides)) == 4


@pytest.mark.parametrize(("slide_index", "copy"), enumerate(REPORT_COPIES))
def test_report_page_has_exact_title_and_notes(slide_index: int, copy) -> None:
    prs = _compose()
    slide = list(prs.slides)[slide_index]

    assert copy.title in _slide_texts(slide)

    notes_frame = slide.notes_slide.notes_text_frame
    assert notes_frame is not None
    assert notes_frame.text.strip() == copy.notes.strip()


def test_emergency_page_has_single_byte_identical_screenshot() -> None:
    prs = _compose()
    slide = list(prs.slides)[1]

    pictures = [
        shape
        for shape in slide.shapes
        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE
    ]
    assert len(pictures) == 1

    expected = hashlib.sha256(SCREENSHOT.read_bytes()).hexdigest()
    actual = hashlib.sha256(pictures[0].image.blob).hexdigest()
    assert actual == expected


def test_emergency_page_rejects_invalid_screenshot(tmp_path: Path) -> None:
    bad = tmp_path / "hospital_sos.png"
    bad.write_bytes(b"not an image")

    with pytest.raises(FileNotFoundError):
        _compose(screenshot_path=bad)


@pytest.mark.parametrize("slide_index", range(4))
def test_report_pages_use_zero_rounded_rectangles(slide_index: int) -> None:
    prs = _compose()
    slide = list(prs.slides)[slide_index]

    rounded = slide._element.xpath('.//p:spPr/a:prstGeom[@prst="roundRect"]')

    assert rounded == []


@pytest.mark.parametrize("slide_index", range(4))
def test_report_pages_contain_no_gradient_fill(slide_index: int) -> None:
    prs = _compose()
    slide = list(prs.slides)[slide_index]

    gradients = slide._element.xpath(".//a:gradFill")

    assert gradients == []


@pytest.mark.parametrize("slide_index", range(4))
def test_report_shapes_stay_within_rotation_aware_canvas(
    slide_index: int,
) -> None:
    prs = _compose()
    slide = list(prs.slides)[slide_index]

    _assert_rotation_aware_bounds(slide, prs.slide_width, prs.slide_height)


@pytest.mark.parametrize("slide_index", range(4))
def test_report_text_boxes_fit_their_content(slide_index: int) -> None:
    prs = _compose()
    slide = list(prs.slides)[slide_index]

    for shape in slide.shapes:
        if not shape.has_text_frame or not shape.text.strip():
            continue
        font_name, font_size, font_bold = _first_run_font(shape)
        assert font_name is not None
        assert font_size is not None
        measured = measure_wrapped_text_height(
            shape.text,
            width_inches=shape.width / Inches(1),
            font_name=font_name,
            font_size_pt=font_size.pt,
            bold=bool(font_bold),
            line_spacing=shape.text_frame.paragraphs[0].line_spacing or 1.0,
        )
        assert measured <= shape.height / Inches(1) + 0.005, shape.text


@pytest.mark.parametrize("slide_index", range(4))
def test_report_pages_avoid_disallowed_wording(slide_index: int) -> None:
    prs = _compose()
    slide = list(prs.slides)[slide_index]

    for text in _slide_texts(slide):
        lowered = text.lower()
        assert "60-second" not in lowered
        assert not re.search(r"60\s*seconds?", lowered)
        assert "signed" not in lowered
        assert not re.search(r"compose[^.\n]*frontend", lowered), text


@pytest.mark.parametrize(
    ("slide_index", "required_strings"),
    [
        (0, ["PRESCRIPTION -> HL7 FHIR MedicationRequest"]),
        (0, ["DIAGNOSTIC REPORT -> HL7 FHIR DiagnosticReport"]),
        (0, ["ITEMIZED BILL -> NHCX FHIR Claim"]),
        (0, ["ABDM TRACE  /  ENDPOINT · STATUS · LATENCY"]),
        (0, ["GATEWAYS INTERNALLY SIMULATED  /  DETERMINISTIC OFFLINE DEMO"]),
        (1, ["PANIC", "PANEL", "PEOPLE"]),
        (1, ["One authenticated action"]),
        (1, ["WebSocket broadcast to hospital dashboards"]),
        (1, ["GPS coordinates + SMTP contact email"]),
        (1, ["EMAIL FAILURE NEVER BLOCKS THE LIVE ALERT"]),
        (2, ["19 automated service tests"]),
        (2, ["16-step end-to-end scenario"]),
        (2, ["5 FastAPI services"]),
        (2, ["5 SQLite databases"]),
        (2, ["One-command service startup"]),
        (2, ["SIMULATED GATEWAYS · NO PRODUCTION HARDENING · SMTP OPTIONAL"]),
        (3, ["Open card", "Scan QR", "Write FHIR", "Push claim", "Trigger SOS"]),
        (3, ["NEXT STEPS"]),
        (3, ["PostgreSQL deployment"]),
        (3, ["Controlled clinical pilot"]),
    ],
)
def test_report_pages_contain_required_strings(
    slide_index: int, required_strings: list[str]
) -> None:
    prs = _compose()
    slide = list(prs.slides)[slide_index]
    combined = "\n".join(_slide_texts(slide))

    for required in required_strings:
        assert required in combined, required


def test_report_pages_run_evidence_wording_is_accurate() -> None:
    prs = _compose()
    evidence_slide = list(prs.slides)[2]
    combined = "\n".join(_slide_texts(evidence_slide))

    assert "ALL PASS: 16/16" in combined
    assert "19 passed" in combined
    assert "COMPOSE STARTS GATEWAY + 5 SERVICES + SEED" in combined
    assert "THE NEXT.JS FRONTEND RUNS SEPARATELY" in combined


def test_composed_report_saves_nonempty_file(tmp_path: Path) -> None:
    prs = _compose()
    output = tmp_path / "report.pptx"

    prs.save(str(output))

    assert output.is_file()
    assert output.stat().st_size > 0


@pytest.mark.parametrize("slide_index", [0, 2, 3])
def test_report_pages_other_than_emergency_have_zero_pictures(
    slide_index: int,
) -> None:
    prs = _compose()
    slide = list(prs.slides)[slide_index]

    pictures = [
        shape
        for shape in slide.shapes
        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE
    ]

    assert pictures == []


@pytest.mark.parametrize("slide_index", range(4))
def test_report_text_shapes_do_not_overlap(slide_index: int) -> None:
    prs = _compose()
    slide = list(prs.slides)[slide_index]

    boxes = [
        (shape.left, shape.top, shape.width, shape.height, shape.text)
        for shape in slide.shapes
        if shape.has_text_frame and shape.text.strip()
    ]
    slack = Inches(0.02)
    for a_index, (ax, ay, aw, ah, a_text) in enumerate(boxes):
        for bx, by, bw, bh, b_text in boxes[a_index + 1 :]:
            horizontal = ax < bx + bw - slack and bx < ax + aw - slack
            vertical = ay < by + bh - slack and by < ay + ah - slack
            assert not (horizontal and vertical), (a_text, b_text)


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_evidence_terminal_commands_reference_real_repo_paths() -> None:
    prs = _compose()
    evidence_slide = list(prs.slides)[2]

    commands = [
        text
        for text in _slide_texts(evidence_slide)
        if text.startswith("$ ")
    ]
    pytest_commands = [c for c in commands if "pytest" in c]
    python_commands = [c for c in commands if c.startswith("$ python")]

    assert pytest_commands == ["$ pytest services/*/tests -q"]
    assert python_commands == ["$ python scripts/e2e.py"]

    for command in python_commands:
        script_path = command.removeprefix("$ python ").split()[0]
        assert (REPO_ROOT / script_path).is_file(), command


THEME_FONTS = {"Georgia", "Arial", "Courier New"}
THEME_COLORS = {"BLACK", "BONE", "BONE_2", "CORAL", "GREEN", "OFF_WHITE", "MUTED"}


def _run_color_name(run) -> str | None:
    color_format = run.font.color
    if color_format.type is None:
        return None
    rgb = color_format.rgb
    for name in THEME_COLORS:
        if rgb == getattr(theme, name):
            return name
    raise AssertionError(f"color {rgb} is not a theme constant")


def test_report_runs_use_theme_fonts_and_colors_only() -> None:
    prs = _compose()
    for slide in prs.slides:
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for paragraph in shape.text_frame.paragraphs:
                for run in paragraph.runs:
                    if not run.text.strip():
                        continue
                    assert run.font.name in THEME_FONTS, run.text
                    color_name = _run_color_name(run)
                    if color_name is None:
                        # Unset colors resolve to the theme default:
                        # BONE on dark slides, BLACK on light slides.
                        assert (
                            slide.background.fill.fore_color.rgb
                            in (theme.BLACK, theme.BONE)
                        ), run.text
                    else:
                        assert color_name in THEME_COLORS


@pytest.mark.parametrize(("slide_index", "copy"), enumerate(REPORT_COPIES))
def test_report_page_has_standard_footer(slide_index: int, copy) -> None:
    prs = _compose()
    slide = list(prs.slides)[slide_index]
    texts = _slide_texts(slide)

    assert "ABHA HEALTH CARD  /  SY1512" in texts
    assert f"{copy.index:02d}" in texts


def test_screenshot_asset_validates() -> None:
    assert required_screenshot(SCREENSHOT) == SCREENSHOT
