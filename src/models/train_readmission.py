"""Train and evaluate a readmission classifier with chronological holdout."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Support both `python -m src.models.train_readmission` and direct script execution.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.models.feature_contract import CATEGORICAL, NUMERIC, TARGET
from src.models.cohort_evaluation import (
    DEFAULT_DIMENSIONS,
    add_default_cohorts,
    evaluate_cohorts,
    write_cohort_evidence,
)


def build_model() -> Pipeline:
    prep = ColumnTransformer(
        [
            (
                "num",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler()),
                    ]
                ),
                NUMERIC,
            ),
            (
                "cat",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                CATEGORICAL,
            ),
        ]
    )
    return Pipeline(
        [
            ("features", prep),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    solver="liblinear",
                    random_state=42,
                ),
            ),
        ]
    )


def _metrics(y: pd.Series, score) -> dict[str, float]:
    pred = (score >= 0.5).astype(int)
    return {
        "roc_auc": float(roc_auc_score(y, score)),
        "pr_auc": float(average_precision_score(y, score)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
    }


def train(
    input_path: str,
    model_path: str,
    cutoff: str,
    time_column: str = "event_date",
    cohort_output: str | None = None,
    min_cohort_rows: int = 50,
) -> dict[str, float | int]:
    df = pd.read_parquet(input_path)
    required = NUMERIC + CATEGORICAL + [TARGET, time_column]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing Gold ML columns: {missing}")

    df[time_column] = pd.to_datetime(df[time_column])
    cutoff_ts = pd.Timestamp(cutoff)
    train_df = df[df[time_column] < cutoff_ts].copy()
    test_df = df[df[time_column] >= cutoff_ts].copy()
    if train_df.empty or test_df.empty:
        raise ValueError("Chronological cutoff must leave rows on both sides")

    model = build_model()
    X_train = train_df[NUMERIC + CATEGORICAL]
    y_train = train_df[TARGET].astype(int)
    X_test = test_df[NUMERIC + CATEGORICAL]
    y_test = test_df[TARGET].astype(int)

    if y_train.nunique() < 2 or y_test.nunique() < 2:
        raise ValueError("Readmission target must contain both classes in train and test sets")

    model.fit(X_train, y_train)
    score = model.predict_proba(X_test)[:, 1]
    metrics = {
        **_metrics(y_test, score),
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
    }
    print(classification_report(y_test, (score >= 0.5).astype(int), zero_division=0))
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    if cohort_output:
        cohort_frame = add_default_cohorts(test_df)
        cohort_results = evaluate_cohorts(
            cohort_frame,
            y_test.to_numpy(),
            score,
            DEFAULT_DIMENSIONS,
            min_rows=min_cohort_rows,
        )
        report_path = write_cohort_evidence(
            cohort_results,
            Path(cohort_output),
            threshold=0.5,
            min_rows=min_cohort_rows,
        )
        print(f"Cohort metrics written to: {cohort_output}")
        print(f"Cohort report written to: {report_path}")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--model", default="artifacts/readmission_model.joblib")
    parser.add_argument("--time-column", default="event_date")
    parser.add_argument("--cutoff", required=True)
    parser.add_argument("--cohort-output", default="artifacts/readmission_cohorts.csv")
    parser.add_argument("--min-cohort-rows", type=int, default=50)
    args = parser.parse_args()
    print(
        train(
            args.input,
            args.model,
            args.cutoff,
            args.time_column,
            args.cohort_output,
            args.min_cohort_rows,
        )
    )
