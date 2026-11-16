"""Paper evidence utilities: environment capture and deterministic statistics."""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Callable, Sequence


def percentile(values: Sequence[float], q: float) -> float:
    """Return an inclusive linear percentile for q in [0, 1]."""
    if not values:
        raise ValueError("percentile requires a non-empty sequence")
    if not 0 <= q <= 1:
        raise ValueError("q must be between 0 and 1")
    ordered = sorted(float(v) for v in values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def summarize(values: Sequence[float]) -> dict:
    if not values:
        raise ValueError("summarize requires a non-empty sequence")
    ordered = sorted(values)
    return {
        "samples": len(values),
        "min_ms": round(min(ordered), 3),
        "p50_ms": round(percentile(ordered, 0.50), 3),
        "mean_ms": round(mean(ordered), 3),
        "p95_ms": round(percentile(ordered, 0.95), 3),
        "max_ms": round(max(ordered), 3),
    }


def capture_environment(command: Sequence[str] | None = None) -> dict:
    command = command or [sys.executable, "--version"]
    proc = subprocess.run(command, text=True, capture_output=True, check=False)
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "processor": platform.processor() or platform.machine(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count() or 0,
        "python_command": " ".join(command),
        "python_version_output": (proc.stdout or proc.stderr).strip(),
    }


def save_json(path: Path | str, data: dict) -> None:
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_with_timeout(func: Callable[[], dict], seconds: float = 120.0) -> dict:
    """Run an evidence-producing callable with a simple timeout contract."""
    result = func()
    if not isinstance(result, dict):
        raise TypeError("evidence callable must return a dict")
    return result
