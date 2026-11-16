"""Run a reproducible local benchmark for public emergency QR-token resolution."""
from __future__ import annotations

import os
import statistics
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.paper.evidence import capture_environment, summarize


def benchmark(resolutions: int = 1000, warmups: int = 50) -> dict:
    if resolutions < 10 or warmups < 1:
        raise ValueError("use at least 10 resolutions and one warmup")

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "records"))
    with tempfile.TemporaryDirectory(prefix="abha-benchmark-") as td:
        os.environ["RECORDS_DB"] = str(Path(td) / "records-benchmark.db")
        os.environ.setdefault("TRAUMA_KEY", "abha-demo-key-16b")
        os.environ["TRAUMA_KEY"] = os.environ["TRAUMA_KEY"]

        from records_app.main import app
        from services.shared import security
        from fastapi.testclient import TestClient

        profile = {
            "full_name": "Benchmark Patient",
            "blood_group": "O+",
            "allergies": ["Penicillin"],
            "chronic_conditions": ["Asthma"],
            "medications": ["Salbutamol"],
            "emergency_contacts": [{"name": "Mother", "phone": "+910000000000", "relation": "Mother"}],
        }
        wall_ms: list[float] = []
        server_ms: list[int] = []
        statuses: list[int] = []

        with TestClient(app) as client:
            token = security.create_token(sub="99001", role="patient", abha_id="11001100110001")
            auth = {"Authorization": f"Bearer {token}"}
            saved = client.put("/emergency/profile", json=profile, headers=auth)
            assert saved.status_code == 200, saved.text
            qr = client.post("/emergency/qr", headers=auth)
            assert qr.status_code == 200, qr.text
            emergency_token = qr.json()["token"]

            for _ in range(warmups):
                response = client.get(f"/emergency/resolve/{emergency_token}")
                assert response.status_code == 200, response.text

            for _ in range(resolutions):
                started = time.perf_counter_ns()
                response = client.get(f"/emergency/resolve/{emergency_token}")
                elapsed = (time.perf_counter_ns() - started) / 1_000_000
                assert response.status_code == 200, response.text
                body = response.json()
                assert body["profile"]["blood_group"] == "O+"
                assert "Penicillin" in body["profile"]["allergies"]
                wall_ms.append(elapsed)
                server_ms.append(int(body["retrieved_in_ms"]))
                statuses.append(response.status_code)

        environment = capture_environment([sys.executable, "--version"])
        return {
            "benchmark_name": "emergency_qr_token_resolution",
            "protocol": "FastAPI TestClient against isolated temporary records service",
            "warmup_requests": warmups,
            "measured_requests": resolutions,
            "all_http_statuses": sorted(set(statuses)),
            "wall_time": summarize(wall_ms),
            "service_reported_resolution": {
                "samples": len(server_ms),
                "min_ms": min(server_ms),
                "p50_ms": int(statistics.median(server_ms)),
                "mean_ms": round(statistics.mean(server_ms), 3),
                "p95_ms": int(statistics.quantiles(server_ms, n=20, method="inclusive")[18]),
                "max_ms": max(server_ms),
            },
            "environment": environment,
            "interpretation": "Local in-process timing; excludes TLS, browser, QR capture, and network latency.",
        }


def main() -> None:
    output = benchmark()
    destination = Path(__file__).resolve().parents[2] / "docs" / "paper" / "benchmark.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(__import__("json").dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(destination)
    print(__import__("json").dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
