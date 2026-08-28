"""Validate the patient-level Gold Parquet dataset."""
from __future__ import annotations

import argparse

from pyspark.sql import SparkSession


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Gold Parquet output")
    parser.add_argument(
        "--input",
        default="/opt/healthcare-benchmark/ml-data/gold",
        help="Gold Parquet directory",
    )
    args = parser.parse_args()

    spark = (
        SparkSession.builder.master("local[1]")
        .appName("gold-validation")
        .getOrCreate()
    )
    try:
        df = spark.read.parquet(args.input)
        row_count = df.count()
        patient_count = df.select("patient_id").distinct().count()
        duplicate_count = row_count - patient_count

        print(f"ROWS={row_count}")
        print(f"DISTINCT_PATIENTS={patient_count}")
        print(f"DUPLICATES={duplicate_count}")
        print(f"COLUMNS={len(df.columns)}")
        print("SCHEMA=")
        df.printSchema()

        if duplicate_count != 0:
            raise SystemExit(
                f"Gold validation failed: {duplicate_count} duplicate patient rows"
            )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
