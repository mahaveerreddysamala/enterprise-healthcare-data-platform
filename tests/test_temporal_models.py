from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.models.train_cost import train as train_cost
from src.models.train_readmission import train as train_readmission
from src.models.readmission import train_readmission_model


def _gold_frame(rows: int = 40) -> pd.DataFrame:
    index = np.arange(rows)
    return pd.DataFrame(
        {
            "event_date": pd.date_range("2024-01-01", periods=rows, freq="D"),
            "age": 30 + index,
            "current_chronic_condition": index % 2,
            "current_emergency_visit": (index // 2) % 2,
            "current_length_of_stay": 1 + index % 8,
            "current_risk_score": (index % 10) / 10,
            "encounter_count": 1 + index % 5,
            "emergency_visits": index % 4,
            "total_los": 2 + index % 12,
            "prior_readmissions": index % 3,
            "avg_los": 1.5 + index % 6,
            "avg_risk_score": (index % 8) / 8,
            "high_utilization": (index % 5 == 0).astype(int),
            "total_cost": 1000.0 + index * 125.0,
            "gender": np.where(index % 2 == 0, "F", "M"),
            "risk_segment": np.where(index % 3 == 0, "high", "low"),
            "readmitted_30d": index % 2,
        }
    )


def test_readmission_training_uses_chronological_holdout(tmp_path) -> None:
    data = tmp_path / "gold.parquet"
    model = tmp_path / "readmission.joblib"
    _gold_frame().to_parquet(data, index=False)

    metrics = train_readmission(str(data), str(model), "2024-01-21")

    assert metrics["train_rows"] == 20
    assert metrics["test_rows"] == 20
    assert 0.0 <= metrics["roc_auc"] <= 1.0
    assert model.is_file()


def test_cost_training_reports_holdout_metrics(tmp_path) -> None:
    data = tmp_path / "gold.parquet"
    model = tmp_path / "cost.joblib"
    _gold_frame().to_parquet(data, index=False)

    metrics = train_cost(str(data), str(model), "2024-01-21")

    assert metrics["train_rows"] == 20
    assert metrics["test_rows"] == 20
    assert metrics["mae"] >= 0.0
    assert model.is_file()


def test_nonlinear_readmission_baseline_uses_chronological_holdout() -> None:
    _, metrics = train_readmission_model(_gold_frame(), "2024-01-21")

    assert 0.0 <= metrics["roc_auc"] <= 1.0
    assert 0.0 <= metrics["pr_auc"] <= 1.0


@pytest.mark.parametrize("trainer", [train_readmission, train_cost])
def test_temporal_training_rejects_empty_split(tmp_path, trainer) -> None:
    data = tmp_path / "gold.parquet"
    _gold_frame().to_parquet(data, index=False)

    with pytest.raises(ValueError, match="both sides"):
        trainer(str(data), str(tmp_path / "model.joblib"), "2030-01-01")
