from __future__ import annotations

from pathlib import Path

from src.dashboard import executive_kpis, load_dashboard_snapshot

ROOT = Path(__file__).parents[1]


def test_dashboard_loads_validated_benchmark_and_model_evidence() -> None:
    snapshot = load_dashboard_snapshot(ROOT)
    kpis = executive_kpis(snapshot)

    assert snapshot.benchmarks["rows"].max() == 50_000_000
    assert snapshot.benchmarks["status"].eq("success").all()
    assert set(snapshot.cohorts["dimension"]) == {"gender", "risk_segment", "age_band"}
    assert snapshot.sample_quality["null_cells"] == 0
    assert kpis["Largest Spark run"] == "50,000,000"
    assert kpis["Readmission PR-AUC"] == "0.1376"
