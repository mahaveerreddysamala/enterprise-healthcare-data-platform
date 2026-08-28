"""CLI entry point for validating a Parquet dataset."""
from __future__ import annotations

import argparse
import json

from pyspark.sql import SparkSession

from src.quality.validation import quality_summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--max-duplicates", type=int, default=0)
    parser.add_argument("--max-invalid-age", type=int, default=0)
    parser.add_argument("--max-negative-cost", type=int, default=0)
    args = parser.parse_args()

    spark = SparkSession.builder.appName("healthcare-quality").getOrCreate()
    try:
        result = quality_summary(spark.read.parquet(args.input).toPandas())
    finally:
        spark.stop()

    print(json.dumps(result, indent=2, sort_keys=True))
    failures = {
        "duplicate_encounters": args.max_duplicates,
        "invalid_age": args.max_invalid_age,
        "negative_cost": args.max_negative_cost,
    }
    violations = {
        key: result[key]
        for key, limit in failures.items()
        if result[key] > limit
    }
    if violations:
        raise SystemExit(f"Data-quality checks failed: {violations}")


if __name__ == "__main__":
    main()
