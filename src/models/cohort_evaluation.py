"""Cohort-level diagnostics for readmission model evaluation."""
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

DEFAULT_DIMENSIONS = ("gender", "risk_segment", "age_band")


def add_default_cohorts(frame: pd.DataFrame) -> pd.DataFrame:
    """Add stable age bands while retaining operational cohorts already present."""
    if "age" not in frame.columns:
        raise ValueError("Missing cohort source column: age")
    result = frame.copy()
    result["age_band"] = pd.cut(
        result["age"],
        bins=[0, 39, 64, np.inf],
        labels=["18-39", "40-64", "65+"],
        include_lowest=True,
    ).astype("string")
    return result


def evaluate_cohorts(
    frame: pd.DataFrame,
    targets: Sequence[int],
    probabilities: Sequence[float],
    dimensions: Sequence[str] = DEFAULT_DIMENSIONS,
    *,
    threshold: float = 0.5,
    min_rows: int = 50,
) -> pd.DataFrame:
    """Calculate classification metrics by cohort with explicit support guards."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between zero and one")
    if min_rows <= 0:
        raise ValueError("min_rows must be positive")
    missing = sorted(set(dimensions).difference(frame.columns))
    if missing:
        raise ValueError(f"Missing cohort columns: {missing}")

    y_true = np.asarray(targets, dtype=int)
    scores = np.asarray(probabilities, dtype=float)
    if len(frame) != len(y_true) or len(y_true) != len(scores):
        raise ValueError("frame, targets, and probabilities must have equal length")
    if not np.isfinite(scores).all() or ((scores < 0) | (scores > 1)).any():
        raise ValueError("probabilities must be finite values between zero and one")

    rows = []
    for dimension in dimensions:
        labels = frame[dimension].astype("string").fillna("<missing>")
        for cohort in sorted(labels.unique()):
            mask = labels.eq(cohort).to_numpy()
            cohort_target = y_true[mask]
            cohort_scores = scores[mask]
            row_count = int(mask.sum())
            positives = int(cohort_target.sum())
            base = {
                "dimension": dimension,
                "cohort": str(cohort),
                "rows": row_count,
                "positives": positives,
                "prevalence": positives / row_count,
            }
            if row_count < min_rows:
                rows.append(
                    {
                        **base,
                        "status": f"insufficient_rows<{min_rows}",
                        "roc_auc": np.nan,
                        "pr_auc": np.nan,
                        "precision": np.nan,
                        "recall": np.nan,
                        "f1": np.nan,
                    }
                )
                continue
            if np.unique(cohort_target).size < 2:
                rows.append(
                    {
                        **base,
                        "status": "single_class",
                        "roc_auc": np.nan,
                        "pr_auc": np.nan,
                        "precision": np.nan,
                        "recall": np.nan,
                        "f1": np.nan,
                    }
                )
                continue

            predictions = (cohort_scores >= threshold).astype(int)
            rows.append(
                {
                    **base,
                    "status": "ok",
                    "roc_auc": float(roc_auc_score(cohort_target, cohort_scores)),
                    "pr_auc": float(average_precision_score(cohort_target, cohort_scores)),
                    "precision": float(
                        precision_score(cohort_target, predictions, zero_division=0)
                    ),
                    "recall": float(recall_score(cohort_target, predictions, zero_division=0)),
                    "f1": float(f1_score(cohort_target, predictions, zero_division=0)),
                }
            )
    return pd.DataFrame(rows)


def _format_metric(value: object, *, percent: bool = False) -> str:
    if pd.isna(value):
        return "—"
    return f"{float(value):.2%}" if percent else f"{float(value):.4f}"


def render_cohort_report(
    results: pd.DataFrame, *, threshold: float, min_rows: int
) -> str:
    """Create a human-readable model-slice report with disparity ranges."""
    if results.empty:
        raise ValueError("Cohort results must not be empty")
    eligible = results[results["status"].eq("ok")]
    lines = [
        "# Readmission Model Cohort Evaluation",
        "",
        f"Classification threshold: **{threshold:.2f}**. Minimum supported cohort: "
        f"**{min_rows:,} rows**.",
        "",
        "| Dimension | Cohort | Rows | Prevalence | ROC-AUC | PR-AUC | Precision | Recall | F1 | Status |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for _, row in results.iterrows():
        lines.append(
            f'| {row["dimension"]} | {row["cohort"]} | {int(row["rows"]):,} | '
            f'{_format_metric(row["prevalence"], percent=True)} | '
            f'{_format_metric(row["roc_auc"])} | {_format_metric(row["pr_auc"])} | '
            f'{_format_metric(row["precision"], percent=True)} | '
            f'{_format_metric(row["recall"], percent=True)} | '
            f'{_format_metric(row["f1"])} | {row["status"]} |'
        )

    lines.extend(["", "## Diagnostic ranges", ""])
    for dimension in results["dimension"].unique():
        supported = eligible[eligible["dimension"].eq(dimension)]
        if len(supported) < 2:
            lines.append(f"- `{dimension}`: insufficient supported cohorts for a range.")
            continue
        recall_gap = float(supported["recall"].max() - supported["recall"].min())
        pr_auc_gap = float(supported["pr_auc"].max() - supported["pr_auc"].min())
        lines.append(
            f"- `{dimension}`: recall range **{recall_gap:.2%}**; "
            f"PR-AUC range **{pr_auc_gap:.4f}**."
        )

    lines.extend(
        [
            "",
            "Rows below the support threshold and single-class cohorts are retained but not "
            "assigned potentially misleading performance metrics.",
            "",
            "> This synthetic-data diagnostic helps find uneven model behavior. It is not a "
            "clinical fairness certification or evidence of real-world subgroup performance.",
            "",
        ]
    )
    return "\n".join(lines)


def write_cohort_evidence(
    results: pd.DataFrame,
    csv_output: Path,
    *,
    threshold: float,
    min_rows: int,
) -> Path:
    """Write detailed CSV metrics and a companion Markdown report."""
    csv_output.parent.mkdir(parents=True, exist_ok=True)
    report_output = csv_output.with_suffix(".md")
    results.to_csv(csv_output, index=False)
    report_output.write_text(
        render_cohort_report(results, threshold=threshold, min_rows=min_rows),
        encoding="utf-8",
    )
    return report_output
