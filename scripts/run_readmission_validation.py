"""Run synthetic Bronze-to-Gold preparation, readmission training, and cohort evaluation."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone

from pyspark.sql import SparkSession

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingestion.generate_data import generate
from src.models.train_readmission import train
from src.transformations.gold import build_patient_gold
from src.transformations.silver import SCHEMA, transform
from src.quality.gates import inspect_events, enforce_events


def run(rows: int, cutoff: str, output_dir: Path, min_cohort_rows: int,
        evaluation_as_of: str | None = None) -> dict:
    """Execute the local synthetic model-validation path and persist evidence."""
    if rows <= 0:
        raise ValueError("rows must be positive")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("Use a new empty output directory for each run to avoid stale evidence")
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "bronze"
    gold_path = output_dir / "gold"
    model_path = output_dir / "readmission_model.joblib"
    cohort_path = output_dir / "readmission_cohorts.csv"
    metrics_path = output_dir / "readmission_metrics.json"
    manifest_path = output_dir / "pipeline-run.json"
    manifest = {"started_at": datetime.now(timezone.utc).isoformat(), "status": "running",
                "synthetic": True, "execution": "local[2]", "rows_requested": rows,
                "stages": [], "quality": {}, "lineage": [
                    {"input": "seed42 generator", "output": "bronze"},
                    {"input": "bronze", "output": "silver", "transform": "transform"},
                    {"input": "silver", "output": "gold", "transform": "build_patient_gold"},
                    {"input": "gold", "output": "model + cohort metrics"}]}

    def save_manifest():
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    @contextmanager
    def stage(name):
        started = time.perf_counter()
        record = {"name": name, "status": "running"}
        manifest["stages"].append(record)
        save_manifest()
        try:
            yield
            record["status"] = "passed"
        except Exception as exc:
            record["status"] = "failed"
            record["error_type"] = type(exc).__name__
            manifest["status"] = "failed"
            raise
        finally:
            record["elapsed_seconds"] = round(time.perf_counter() - started, 3)
            save_manifest()

    with stage("generate_bronze"):
        generate(rows, str(raw_path), chunk_size=min(rows, 100_000), seed=42)
    os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
    with stage("start_spark"):
        spark = (
            SparkSession.builder.master("local[2]")
            .appName("healthcare-readmission-validation")
            .getOrCreate()
        )
    try:
        with stage("validate_bronze"):
            bronze = spark.read.schema(SCHEMA).parquet(str(raw_path.resolve()))
            manifest["quality"]["bronze"] = inspect_events(bronze)
            enforce_events(manifest["quality"]["bronze"])
        with stage("build_and_validate_silver"):
            silver = transform(bronze)
            manifest["quality"]["silver"] = inspect_events(silver)
            enforce_events(manifest["quality"]["silver"])
        with stage("write_and_validate_gold"):
            gold = build_patient_gold(silver)
            gold.write.mode("overwrite").parquet(str(gold_path.resolve()))
            persisted = spark.read.parquet(str(gold_path.resolve()))
            count = persisted.count()
            duplicates = count - persisted.select("patient_id").distinct().count()
            manifest["quality"]["gold"] = {"row_count": count, "duplicate_patients": duplicates}
            if count == 0 or duplicates:
                raise ValueError("Gold must contain nonempty unique patient rows")
    finally:
        spark.stop()

    with stage("train_and_evaluate"):
        metrics = train(
            str(gold_path), str(model_path), cutoff, cohort_output=str(cohort_path),
            min_cohort_rows=min_cohort_rows, evaluation_as_of=evaluation_as_of,
        )
        metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
    manifest["status"] = "passed"
    manifest["stage_elapsed_seconds"] = round(sum(s["elapsed_seconds"] for s in manifest["stages"]), 3)
    manifest["rows_per_stage_second"] = rows / manifest["stage_elapsed_seconds"]
    save_manifest()
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=20_000)
    parser.add_argument("--cutoff", default="2024-07-01")
    parser.add_argument("--min-cohort-rows", type=int, default=50)
    parser.add_argument("--evaluation-as-of", help="Defaults to latest observed discharge date")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/readmission-validation"))
    args = parser.parse_args()
    metrics = run(args.rows, args.cutoff, args.output_dir, args.min_cohort_rows,
                  args.evaluation_as_of)
    print(json.dumps(metrics, indent=2, sort_keys=True))
    print(f"Validation evidence written to: {args.output_dir}")


if __name__ == "__main__":
    main()
