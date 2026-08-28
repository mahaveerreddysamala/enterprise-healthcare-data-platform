"""CLI wrapper for building the patient-level Gold dataset."""
from __future__ import annotations

import argparse

from pyspark.sql import SparkSession

from src.transformations.gold import build_patient_gold


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    spark = SparkSession.builder.appName("healthcare-gold").getOrCreate()
    try:
        (
            build_patient_gold(spark.read.parquet(args.input))
            .write.mode("overwrite")
            .parquet(args.output)
        )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
