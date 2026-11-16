import math
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from scripts.paper.evidence import capture_environment, percentile, save_json, summarize


def test_percentile_interpolates_p95():
    values = list(range(1, 101))
    assert math.isclose(percentile(values, 0.95), 95.05)


def test_summarize_reports_exact_order_statistics():
    values = [4.0, 1.0, 3.0, 2.0, 10.0]
    result = summarize(values)
    assert result["samples"] == 5
    assert result["min_ms"] == 1.0
    assert result["p50_ms"] == 3.0
    assert result["mean_ms"] == 4.0
    assert result["p95_ms"] == 8.8
    assert result["max_ms"] == 10.0


def test_environment_capture_is_json_safe(tmp_path):
    data = capture_environment(["python3", "--version"])
    save_json(tmp_path / "environment.json", data)
    assert data["machine"]
    assert data["python_version_output"].startswith("Python")
