from pathlib import Path
from urllib.parse import urlparse

import qrcode
from PIL import Image, UnidentifiedImageError
from qrcode.constants import ERROR_CORRECT_H


def ensure_qr(url: str, output: Path) -> Path:
    if not url.strip():
        raise ValueError("QR URL must not be empty")
    parsed_url = urlparse(url)
    if parsed_url.scheme.lower() not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("QR URL must use the http or https scheme")

    if output.suffix.lower() != ".png":
        raise ValueError("QR output path must use a .PNG suffix")

    output.parent.mkdir(parents=True, exist_ok=True)
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_H,
        box_size=14,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr.make_image(fill_color="#101512", back_color="#FAF8F2").save(output)
    return output


def required_screenshot(path: Path) -> Path:
    if not path.is_file() or path.stat().st_size == 0:
        raise FileNotFoundError(
            f"Required project screenshot is missing or invalid: {path}"
        )

    try:
        with Image.open(path) as image:
            image.verify()
    except (OSError, UnidentifiedImageError) as exc:
        raise FileNotFoundError(
            f"Required project screenshot is missing or invalid: {path}"
        ) from exc

    return path
