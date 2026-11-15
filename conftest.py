"""Pytest configuration for the whole repository.

Each service is an independent application with its own package (identity_app,
records_app, ...). Adding every service directory to sys.path lets one pytest
session collect all service test suites without module-name collisions.
"""

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

for svc in ("identity", "records", "abdm", "nhcx", "sos"):
    path = os.path.join(ROOT, "services", svc)
    if path not in sys.path:
        sys.path.insert(0, path)

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
