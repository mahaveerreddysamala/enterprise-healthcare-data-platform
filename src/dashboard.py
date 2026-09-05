"""Validated data loader and view model for the healthcare portfolio dashboard."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import pandas as pd

from src.quality.validation import quality_summary


@dataclass(frozen=True)
class HealthcareDashboardSnapshot:
    """Dashboard-ready evidence from committed synthetic benchmark snapshots."""

    benchmarks: pd.DataFrame
    partition_tuning: pd.DataFrame
    cohorts: pd.DataFrame
    model_metrics: dict[str, float | int | str]
    sample_quality: dict[str, int]
    sample_rows: int


def _read_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(f"Dashboard data file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_dashboard_snapshot(repository_root: Path) -> HealthcareDashboardSnapshot:
    """Load AWS, quality, and model evidence and validate required dashboard fields."""
    benchmark_payload = _read_json(repository_root / "benchmark" / "aws_spark_results.json")
    metrics = _read_json(repository_root / "dashboard" / "data" / "readmission_metrics.json")
    cohorts = pd.read_csv(repository_root / "dashboard" / "data" / "readmission_cohorts.csv")
    sample = pd.read_csv(repository_root / "data" / "sample" / "events.csv")

    benchmarks = pd.DataFrame(benchmark_payload["benchmarks"])
    partition_tuning = pd.DataFrame(benchmark_payload["partition_tuning_10m"])
    required_benchmark = {"rows", "partitions", "runtime_seconds", "rows_per_second", "status"}
    required_cohort = {
        "dimension",
        "cohort",
        "rows",
        "prevalence",
        "status",
        "roc_auc",
        "pr_auc",
        "precision",
        "recall",
        "f1",
    }
    if missing := sorted(required_benchmark.difference(benchmarks.columns)):
        raise ValueError(f"AWS benchmark evidence missing columns: {missing}")
    if missing := sorted(required_cohort.difference(cohorts.columns)):
        raise ValueError(f"Cohort evidence missing columns: {missing}")
    if not {"roc_auc", "pr_auc", "precision", "recall", "f1"}.issubset(metrics):
        raise ValueError("Readmission metrics are incomplete")

    return HealthcareDashboardSnapshot(
        benchmarks=benchmarks.sort_values("rows").reset_index(drop=True),
        partition_tuning=partition_tuning.sort_values("partitions").reset_index(drop=True),
        cohorts=cohorts,
        model_metrics=metrics,
        sample_quality=quality_summary(sample),
        sample_rows=len(sample),
    )


def executive_kpis(snapshot: HealthcareDashboardSnapshot) -> dict[str, str]:
    """Return the small set of defensible headline metrics shown above the fold."""
    largest = snapshot.benchmarks.loc[snapshot.benchmarks["rows"].idxmax()]
    return {
        "Largest Spark run": f'{int(largest["rows"]):,}',
        "Peak throughput": f'{float(largest["rows_per_second"]):,.0f} rows/s',
        "Sample quality issues": str(sum(snapshot.sample_quality.values()) - snapshot.sample_rows),
        "Readmission PR-AUC": f'{float(snapshot.model_metrics["pr_auc"]):.4f}',
        "Future test rows": f'{int(snapshot.model_metrics["test_rows"]):,}',
    }
