from pathlib import Path

import pytest
import zxingcpp
from PIL import Image

from deck.assets import ensure_qr, required_screenshot


def test_ensure_qr_creates_readable_square_png(tmp_path: Path) -> None:
    url = "http://localhost:3000"
    output = tmp_path / "nested" / "directory" / "qr.png"

    result = ensure_qr(url, output)

    assert result == output
    assert output.is_file()
    with Image.open(output) as image:
        assert image.width == image.height
        assert image.width >= 512
        assert image.format == "PNG"
        decoded = zxingcpp.read_barcodes(image)
    assert [barcode.text for barcode in decoded] == [url]


def test_ensure_qr_accepts_png_suffix_case_insensitively(tmp_path: Path) -> None:
    output = tmp_path / "qr.PNG"

    result = ensure_qr("https://example.com/health-card", output)

    assert result == output
    assert output.is_file()


@pytest.mark.parametrize(
    "url",
    ["", "   ", "ftp://example.com/qr", "file:///tmp/qr", "localhost:3000"],
)
def test_ensure_qr_rejects_empty_or_non_http_urls(
    tmp_path: Path, url: str
) -> None:
    with pytest.raises(ValueError, match="URL"):
        ensure_qr(url, tmp_path / "qr.png")


def test_ensure_qr_requires_png_output_suffix(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="PNG"):
        ensure_qr("https://example.com/health-card", tmp_path / "qr.jpg")


def test_required_screenshot_accepts_valid_image(tmp_path: Path) -> None:
    screenshot = tmp_path / "patient.png"
    Image.new("RGB", (2, 2), "white").save(screenshot)

    result = required_screenshot(screenshot)

    assert result == screenshot


@pytest.mark.parametrize("asset_kind", ["missing", "directory", "empty", "corrupt"])
def test_required_screenshot_rejects_invalid_assets(
    tmp_path: Path, asset_kind: str
) -> None:
    screenshot = tmp_path / "patient.png"
    if asset_kind == "directory":
        screenshot.mkdir()
    elif asset_kind == "empty":
        screenshot.touch()
    elif asset_kind == "corrupt":
        screenshot.write_bytes(b"not an image")

    with pytest.raises(FileNotFoundError) as exc:
        required_screenshot(screenshot)

    assert "patient.png" in str(exc.value)
