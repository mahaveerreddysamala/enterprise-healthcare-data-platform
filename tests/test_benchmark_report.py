from __future__ import annotations

import json

from benchmark.spark_healthcare_benchmark import (
    render_markdown_report,
    write_benchmark_evidence,
)


def _metrics() -> dict[str, object]:
    return {
        "timestamp_utc": "2026-01-01T00:00:00+00:00",
        "rows": 100_000,
        "partitions": 2,
        "elapsed_seconds": 20.0,
        "rows_per_second": 5_000.0,
        "spark_version": "3.5.3",
        "output": "artifacts/healthcare-spark-benchmark/data",
    }


def test_report_defines_workload_and_limitations() -> None:
    report = render_markdown_report(_metrics())

    assert "100,000" in report
    assert "5,000.00 rows/second" in report
    assert "generation, transformation, aggregation" in report
    assert "does not measure the complete Bronze/Silver/Gold pipeline" in report


def test_benchmark_evidence_writes_json_and_markdown(tmp_path) -> None:
    metrics_output = tmp_path / "metrics.json"
    report_output = tmp_path / "report.md"

    write_benchmark_evidence(_metrics(), metrics_output, report_output)

    assert json.loads(metrics_output.read_text(encoding="utf-8"))["rows"] == 100_000
    assert report_output.read_text(encoding="utf-8").startswith("# Healthcare Spark Benchmark")
