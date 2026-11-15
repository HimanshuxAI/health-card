from pathlib import Path

from PIL import Image

from deck.assets import ensure_qr, required_screenshot


def test_ensure_qr_creates_readable_square_png(tmp_path: Path) -> None:
    output = tmp_path / "qr.png"
    ensure_qr("http://localhost:3000", output)
    with Image.open(output) as image:
        assert image.width == image.height
        assert image.width >= 512
        assert image.format == "PNG"


def test_required_screenshot_rejects_missing_file(tmp_path: Path) -> None:
    try:
        required_screenshot(tmp_path / "patient.png")
    except FileNotFoundError as exc:
        assert "patient.png" in str(exc)
    else:
        raise AssertionError("missing screenshot must raise FileNotFoundError")
