"""Run synthetic Bronze-to-Gold preparation, readmission training, and cohort evaluation."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from pyspark.sql import SparkSession

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingestion.generate_data import generate
from src.models.train_readmission import train
from src.transformations.gold import build_patient_gold
from src.transformations.silver import SCHEMA, transform


def run(rows: int, cutoff: str, output_dir: Path, min_cohort_rows: int) -> dict[str, float | int]:
    """Execute the local synthetic model-validation path and persist evidence."""
    if rows <= 0:
        raise ValueError("rows must be positive")
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "bronze"
    gold_path = output_dir / "gold"
    model_path = output_dir / "readmission_model.joblib"
    cohort_path = output_dir / "readmission_cohorts.csv"
    metrics_path = output_dir / "readmission_metrics.json"

    generate(rows, str(raw_path), chunk_size=min(rows, 100_000), seed=42)
    os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
    spark = (
        SparkSession.builder.master("local[2]")
        .appName("healthcare-readmission-validation")
        .getOrCreate()
    )
    try:
        bronze = spark.read.schema(SCHEMA).parquet(str(raw_path.resolve()))
        gold = build_patient_gold(transform(bronze))
        gold.write.mode("overwrite").parquet(str(gold_path.resolve()))
    finally:
        spark.stop()

    metrics = train(
        str(gold_path),
        str(model_path),
        cutoff,
        cohort_output=str(cohort_path),
        min_cohort_rows=min_cohort_rows,
    )
    metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=20_000)
    parser.add_argument("--cutoff", default="2024-07-01")
    parser.add_argument("--min-cohort-rows", type=int, default=50)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/readmission-validation"))
    args = parser.parse_args()
    metrics = run(args.rows, args.cutoff, args.output_dir, args.min_cohort_rows)
    print(json.dumps(metrics, indent=2, sort_keys=True))
    print(f"Validation evidence written to: {args.output_dir}")


if __name__ == "__main__":
    main()
