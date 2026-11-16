import re
from pathlib import Path
from tempfile import TemporaryDirectory

from deck.assets import ensure_qr
from deck.slides.narrative import (
    QR_URL,
    build_cover,
    build_problem,
    build_solution,
)
from deck.slides.report import (
    build_close,
    build_evidence,
    build_emergency,
    build_interoperability,
)
from deck.slides.system import build_architecture, build_experience, build_security
from deck.theme import new_presentation


_SCAN_TOKEN_PATTERN = re.compile(r"[0-9a-f]{32}")


def _validate_scan_token(scan_token: str | None) -> str | None:
    if scan_token is None:
        return None
    if (
        not isinstance(scan_token, str)
        or _SCAN_TOKEN_PATTERN.fullmatch(scan_token) is None
    ):
        raise ValueError(
            "Scan token must be exactly 32 lowercase hexadecimal characters."
        )
    return scan_token


def build_presentation(
    output: Path,
    *,
    scan_token: str | None = None,
    assets_dir: Path | None = None,
) -> Path:
    """Build and save the complete ten-slide presentation."""
    output = Path(output)
    resolved_token = _validate_scan_token(scan_token)
    resolved_assets_dir = (
        Path(assets_dir)
        if assets_dir is not None
        else Path(__file__).resolve().parent / "assets" / "screenshots"
    )
    qr_url = (
        f"{QR_URL}?t={resolved_token}"
        if resolved_token is not None
        else QR_URL
    )
    prs = new_presentation()

    with TemporaryDirectory(prefix="abha-health-card-") as temporary_directory:
        qr_path = ensure_qr(
            qr_url,
            Path(temporary_directory) / "scan-qr.png",
        )
        build_cover(
            prs,
            qr_path=qr_path,
            qr_url=qr_url,
            scan_token=resolved_token,
        )
        build_problem(prs)
        build_solution(
            prs,
            qr_path=qr_path,
            qr_url=qr_url,
            scan_token=resolved_token,
        )
        build_experience(prs, assets_dir=resolved_assets_dir)
        build_architecture(prs)
        build_security(prs)
        build_interoperability(prs)
        build_emergency(
            prs,
            screenshot_path=resolved_assets_dir / "hospital_sos.png",
        )
        build_evidence(prs)
        build_close(prs)

        output.parent.mkdir(parents=True, exist_ok=True)
        prs.save(output)

    return output


__all__ = ["build_presentation"]
