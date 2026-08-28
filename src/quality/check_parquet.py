"""Spark-native CLI entry point for validating a Parquet dataset."""
from __future__ import annotations

import argparse
import json

from pyspark.sql import SparkSession, functions as F

REQUIRED_COLUMNS = {
    "encounter_id",
    "patient_id",
    "age",
    "chronic_condition",
    "emergency_visit",
    "length_of_stay",
    "total_cost",
    "readmitted_30d",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--max-duplicates", type=int, default=0)
    parser.add_argument("--max-invalid-age", type=int, default=0)
    parser.add_argument("--max-negative-cost", type=int, default=0)
    args = parser.parse_args()

    spark = SparkSession.builder.appName("healthcare-quality").getOrCreate()
    try:
        df = spark.read.parquet(args.input)
        missing = sorted(REQUIRED_COLUMNS - set(df.columns))
        if missing:
            raise SystemExit(f"Missing required columns: {missing}")

        row_count = df.count()
        duplicate_encounters = (
            df.groupBy("encounter_id")
            .count()
            .filter(F.col("count") > 1)
            .agg(F.coalesce(F.sum(F.col("count") - 1), F.lit(0)).alias("n"))
            .first()["n"]
        )
        null_cells = df.select(
            *[
                F.sum(F.col(column).isNull().cast("long")).alias(column)
                for column in REQUIRED_COLUMNS
            ]
        ).first()
        null_cells_count = int(sum(value or 0 for value in null_cells))
        invalid_age = df.filter(~F.col("age").between(18, 120)).count()
        negative_cost = df.filter(F.col("total_cost") < 0).count()

        result = {
            "row_count": row_count,
            "null_cells": null_cells_count,
            "duplicate_encounters": int(duplicate_encounters or 0),
            "invalid_age": invalid_age,
            "negative_cost": negative_cost,
        }
        print(json.dumps(result, indent=2, sort_keys=True))

        limits = {
            "duplicate_encounters": args.max_duplicates,
            "invalid_age": args.max_invalid_age,
            "negative_cost": args.max_negative_cost,
        }
        violations = {
            key: result[key] for key, limit in limits.items() if result[key] > limit
        }
        if violations:
            raise SystemExit(f"Data-quality checks failed: {violations}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
