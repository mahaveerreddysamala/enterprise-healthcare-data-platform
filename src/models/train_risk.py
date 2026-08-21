"""Create unsupervised patient risk segments from numeric utilization features."""
from __future__ import annotations

import argparse
from pathlib import Path
import joblib
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

FEATURES = ["age", "encounter_count", "prior_readmissions", "avg_los", "total_cost"]


def train(input_path: str, output_path: str, model_path: str) -> None:
    df = pd.read_parquet(input_path)
    pipeline = Pipeline([("scale", StandardScaler()), ("cluster", MiniBatchKMeans(n_clusters=4, batch_size=2048, random_state=42, n_init=10))])
    labels = pipeline.fit_predict(df[FEATURES])
    result = df.copy()
    result["risk_cluster"] = labels
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(output_path, index=False)
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", default="data/gold/risk_segments.parquet")
    p.add_argument("--model", default="artifacts/risk_segmentation.joblib")
    a = p.parse_args()
    train(a.input, a.output, a.model)
