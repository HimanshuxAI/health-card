#!/usr/bin/env python3
"""Orchestrates seeding across all five services, in dependency order.

Run from the repo root:  python scripts/seed.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = str(ROOT / ".venv" / "bin" / "python")

ORDER = ["identity", "records", "abdm", "nhcx", "sos"]


def main():
    for svc in ORDER:
        r = subprocess.run(
            [PYTHON, "seed.py"],
            cwd=ROOT / "services" / svc,
            capture_output=True,
            text=True,
        )
        out = (r.stdout + r.stderr).strip()
        tag = out.splitlines()[-1] if out else svc
        print(f"[{svc}] {tag}")
        if r.returncode != 0:
            sys.exit(1)
    print("Seed complete.")


if __name__ == "__main__":
    main()
