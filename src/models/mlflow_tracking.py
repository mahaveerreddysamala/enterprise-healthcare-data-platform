"""Optional MLflow wrapper for reproducible experiment tracking."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import mlflow


def log_metrics(metrics_path: str, experiment: str, run_name: str) -> None:
    metrics = json.loads(Path(metrics_path).read_text())
    mlflow.set_experiment(experiment)
    with mlflow.start_run(run_name=run_name):
        numeric = {k: v for k, v in metrics.items() if isinstance(v, (int, float))}
        mlflow.log_metrics(numeric)
        mlflow.log_artifact(metrics_path, artifact_path="evaluation")
        mlflow.set_tags({"domain": "healthcare", "data_policy": "synthetic-only"})


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--metrics", required=True)
    p.add_argument("--experiment", default="healthcare-readmission")
    p.add_argument("--run-name", default="time-aware-evaluation")
    a = p.parse_args()
    log_metrics(a.metrics, a.experiment, a.run_name)
