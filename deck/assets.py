from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_H


def ensure_qr(url: str, output: Path) -> Path:
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
    if not path.exists():
        raise FileNotFoundError(f"Required project screenshot is missing: {path}")
    return path
