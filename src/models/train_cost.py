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


def train(input_path: str, model_path: str) -> dict[str, float]:
    df = pd.read_parquet(input_path)
    X = df[NUMERIC + CATEGORICAL]
    y = df[TARGET].astype(float)
    prep = ColumnTransformer([
        ("num", SimpleImputer(strategy="median"), NUMERIC),
        ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), CATEGORICAL),
    ], sparse_threshold=0)
    model = Pipeline([("features", prep), ("regressor", HistGradientBoostingRegressor(max_iter=150, learning_rate=0.06, random_state=42))])
    model.fit(X, y)
    pred = model.predict(X)
    metrics = {"mae": float(mean_absolute_error(y, pred)), "rmse": float(mean_squared_error(y, pred) ** 0.5), "r2": float(r2_score(y, pred))}
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--model", default="artifacts/cost_model.joblib")
    args = parser.parse_args()
    print(train(args.input, args.model))
