from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.dashboard import (
    cohort_governance_summary,
    executive_kpis,
    load_dashboard_snapshot,
)

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

    governance = cohort_governance_summary(snapshot.cohorts)
    assert set(governance["dimension"]) == {"gender", "risk_segment", "age_band"}
    assert governance["supported_row_coverage"].between(0.0, 1.0).all()
    assert governance["pr_auc_range"].ge(0.0).all()
    gender = governance.loc[governance["dimension"].eq("gender")].iloc[0]
    assert gender["supported_cohorts"] == 2
    assert gender["total_cohorts"] == 3


def test_cohort_governance_rejects_incomplete_evidence() -> None:
    with pytest.raises(ValueError, match="missing columns"):
        cohort_governance_summary(pd.DataFrame({"dimension": ["gender"]}))
