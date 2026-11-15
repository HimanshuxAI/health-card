#!/usr/bin/env python3
"""Orchestrates seeding across all five services, in dependency order.

Run from the repo root:  python scripts/seed.py
Reset the demo data:     python scripts/seed.py --reset
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV_PY = ROOT / ".venv" / "bin" / "python"
PYTHON = str(VENV_PY) if VENV_PY.exists() else sys.executable

ORDER = ["identity", "records", "abdm", "nhcx", "sos"]

DB_FILES = {
    "identity": "identity.db",
    "records": "records.db",
    "abdm": "abdm.db",
    "nhcx": "nhcx.db",
    "sos": "sos.db",
}


def reset_databases():
    """Drop every service database (and any SQLite side-car files).

    The deletion happens in whichever process runs this script. Inside the
    Docker seed container that means the bind-mounted directory is edited from
    the same filesystem view the services use — deleting the files from the
    host and recreating them in a container straight afterwards can fail with
    "unable to open database file" while Docker Desktop catches up.
    """
    for svc, filename in DB_FILES.items():
        db = ROOT / "services" / svc / filename
        for path in (db, Path(f"{db}-journal"), Path(f"{db}-wal"), Path(f"{db}-shm")):
            if path.exists():
                path.unlink()
                print(f"[{svc}] removed {path.name}")


def main():
    if "--reset" in sys.argv[1:]:
        reset_databases()

    for svc in ORDER:
        r = subprocess.run(
            [PYTHON, "seed.py"],
            cwd=ROOT / "services" / svc,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": str(ROOT / "services")},
        )
        out = (r.stdout + r.stderr).strip()
        tag = out.splitlines()[-1] if out else svc
        print(f"[{svc}] {tag}")
        if r.returncode != 0:
            sys.exit(1)
    print("Seed complete.")


if __name__ == "__main__":
    main()
