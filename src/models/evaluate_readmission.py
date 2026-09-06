"""Time-aware evaluation utilities for readmission models."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import joblib
import pandas as pd
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score, roc_auc_score
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.models.label_availability import available_split


def evaluate(input_path: str, model_path: str, time_column: str, cutoff: str, output_path: str,
             evaluation_as_of=None) -> dict:
    df = pd.read_parquet(input_path)
    if time_column not in df.columns:
        raise ValueError(f"Missing time column: {time_column}")
    _, test, coverage = available_split(df, cutoff, time_column, evaluation_as_of)
    if test.empty or test["readmitted_30d"].nunique() < 2:
        raise ValueError("Mature holdout must contain both classes")
    y = test["readmitted_30d"].astype(int)
    model = joblib.load(model_path)
    p = model.predict_proba(test)[:, 1]
    pred = (p >= 0.5).astype(int)
    metrics = {
        **coverage,
        "roc_auc": float(roc_auc_score(y, p)),
        "pr_auc": float(average_precision_score(y, p)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "test_rows": int(len(test)),
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--time-column", default="event_date")
    p.add_argument("--cutoff", required=True)
    p.add_argument("--output", default="artifacts/readmission_metrics.json")
    p.add_argument("--evaluation-as-of")
    a = p.parse_args()
    print(evaluate(a.input, a.model, a.time_column, a.cutoff, a.output, a.evaluation_as_of))
