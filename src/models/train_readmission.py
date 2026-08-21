"""Train readmission classifier on the canonical patient Gold table."""
from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, classification_report, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC = ["age", "encounter_count", "prior_readmissions", "avg_los", "total_cost"]
CATEGORICAL = ["gender", "risk_segment"]
TARGET = "readmitted_30d"


def train(input_path: str, model_path: str) -> dict[str, float]:
    df = pd.read_parquet(input_path)
    missing = [c for c in NUMERIC + CATEGORICAL + [TARGET] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing Gold ML columns: {missing}")
    X = df[NUMERIC + CATEGORICAL]
    y = df[TARGET].astype(int)
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
    model = Pipeline(
        [
            ("features", prep),
            ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )
    model.fit(X, y)
    score = model.predict_proba(X)[:, 1]
    metrics = {
        "roc_auc": float(roc_auc_score(y, score)),
        "pr_auc": float(average_precision_score(y, score)),
    }
    print(classification_report(y, (score >= 0.5).astype(int)))
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--model", default="artifacts/readmission_model.joblib")
    args = parser.parse_args()
    print(train(args.input, args.model))
