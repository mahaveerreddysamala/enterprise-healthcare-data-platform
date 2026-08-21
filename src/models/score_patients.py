"""Score patients using a persisted readmission model."""
from __future__ import annotations

import argparse
from pathlib import Path
import joblib
import pandas as pd


def score(input_path: str, model_path: str, output_path: str) -> None:
    df = pd.read_parquet(input_path)
    model = joblib.load(model_path)
    probability = model.predict_proba(df)[:, 1]
    result = df.copy()
    result["readmission_probability"] = probability
    result["risk_band"] = pd.cut(probability, bins=[-0.01, 0.20, 0.50, 0.80, 1.01], labels=["low", "moderate", "high", "critical"])
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(output_path, index=False)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--output", default="data/gold/patient_scores.parquet")
    a = p.parse_args()
    score(a.input, a.model, a.output)
