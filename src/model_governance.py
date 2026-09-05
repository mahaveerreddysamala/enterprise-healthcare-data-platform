"""Subgroup model-governance summaries for the healthcare dashboard."""
from __future__ import annotations

import pandas as pd


def cohort_governance_summary(cohorts: pd.DataFrame) -> pd.DataFrame:
    """Summarize supported coverage and metric ranges for each cohort dimension."""
    required = {"dimension", "cohort", "rows", "status", "pr_auc", "recall"}
    if missing := sorted(required.difference(cohorts.columns)):
        raise ValueError(f"Cohort governance evidence missing columns: {missing}")
    if cohorts.empty:
        raise ValueError("cohorts must not be empty")

    records: list[dict[str, float | int | str]] = []
    for dimension, dimension_rows in cohorts.groupby("dimension", sort=False):
        supported = dimension_rows[dimension_rows["status"].eq("ok")]
        total_rows = int(dimension_rows["rows"].sum())
        supported_rows = int(supported["rows"].sum())

        def metric_range(metric: str) -> float:
            values = supported[metric].dropna().astype(float)
            return float(values.max() - values.min()) if len(values) >= 2 else 0.0

        records.append(
            {
                "dimension": str(dimension),
                "supported_cohorts": len(supported),
                "total_cohorts": len(dimension_rows),
                "supported_row_coverage": supported_rows / total_rows if total_rows else 0.0,
                "pr_auc_range": metric_range("pr_auc"),
                "recall_range": metric_range("recall"),
            }
        )
    return pd.DataFrame(records)
