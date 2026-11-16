import os
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
from deck.theme import new_presentation


_SCAN_TOKEN_PATTERN = re.compile(r"[0-9a-f]{32}")


def _resolve_scan_token(scan_token: str | None) -> str | None:
    resolved_token = (
        scan_token if scan_token is not None else os.environ.get("ABHA_SCAN_TOKEN")
    )
    if resolved_token is None:
        return None
    if (
        not isinstance(resolved_token, str)
        or _SCAN_TOKEN_PATTERN.fullmatch(resolved_token) is None
    ):
        raise ValueError(
            "Scan token must be exactly 32 lowercase hexadecimal characters."
        )
    return resolved_token


def build_presentation(
    output: Path, *, scan_token: str | None = None
) -> Path:
    """Build and save the currently implemented narrative slides."""
    output = Path(output)
    resolved_token = _resolve_scan_token(scan_token)
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

        output.parent.mkdir(parents=True, exist_ok=True)
        prs.save(output)

    return output


__all__ = ["build_presentation"]
