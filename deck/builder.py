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


def build_presentation(output: Path) -> Path:
    """Build and save the currently implemented narrative slides."""
    output = Path(output)
    prs = new_presentation()

    with TemporaryDirectory(prefix="abha-health-card-") as temporary_directory:
        qr_path = ensure_qr(
            QR_URL,
            Path(temporary_directory) / "scan-qr.png",
        )
        build_cover(prs, qr_path=qr_path)
        build_problem(prs)
        build_solution(prs, qr_path=qr_path)

        output.parent.mkdir(parents=True, exist_ok=True)
        prs.save(output)

    return output


__all__ = ["build_presentation"]
