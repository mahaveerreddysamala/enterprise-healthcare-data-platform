"""Train a healthcare cost regression model."""
from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

NUMERIC = ["age", "encounter_count", "prior_readmissions", "avg_los"]
CATEGORICAL = ["gender", "risk_segment"]
TARGET = "total_cost"


def train(
    input_path: str,
    model_path: str,
    cutoff: str,
    time_column: str = "event_date",
) -> dict[str, float]:
    df = pd.read_parquet(input_path)
    required = NUMERIC + CATEGORICAL + [TARGET, time_column]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Missing Gold cost-model columns: {missing}")

    df[time_column] = pd.to_datetime(df[time_column])
    cutoff_ts = pd.Timestamp(cutoff)
    train_df = df[df[time_column] < cutoff_ts].copy()
    test_df = df[df[time_column] >= cutoff_ts].copy()
    if train_df.empty or test_df.empty:
        raise ValueError("Chronological cutoff must leave rows on both sides")

    X_train = train_df[NUMERIC + CATEGORICAL]
    y_train = train_df[TARGET].astype(float)
    X_test = test_df[NUMERIC + CATEGORICAL]
    y_test = test_df[TARGET].astype(float)
    prep = ColumnTransformer([
        ("num", SimpleImputer(strategy="median"), NUMERIC),
        ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), CATEGORICAL),
    ], sparse_threshold=0)
    model = Pipeline([("features", prep), ("regressor", HistGradientBoostingRegressor(max_iter=150, learning_rate=0.06, random_state=42))])
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    metrics = {
        "mae": float(mean_absolute_error(y_test, pred)),
        "rmse": float(mean_squared_error(y_test, pred) ** 0.5),
        "r2": float(r2_score(y_test, pred)),
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
    }
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--model", default="artifacts/cost_model.joblib")
    parser.add_argument("--time-column", default="event_date")
    parser.add_argument("--cutoff", required=True)
    args = parser.parse_args()
    print(train(args.input, args.model, args.cutoff, args.time_column))
