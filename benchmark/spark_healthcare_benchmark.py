#!/usr/bin/env python3
"""Generate and benchmark a synthetic healthcare dataset with PySpark.

This script is designed for the EC2/S3 benchmark environment in this repository.
It avoids storing the full dataset in driver memory and writes partitioned Parquet
outputs to S3 so the workload demonstrates distributed processing behavior.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, IntegerType


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=1_000_000)
    parser.add_argument("--output", required=True)
    parser.add_argument("--partitions", type=int, default=16)
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.rows <= 0:
        raise ValueError("--rows must be positive")

    # EC2 benchmark instances can have a small /tmp filesystem even when the
    # root EBS volume has plenty of free space. Keep Spark's local files on the
    # persistent benchmark volume instead of filling /tmp with dependency jars.
    local_dir = Path("/opt/healthcare-benchmark/spark-local")
    local_dir.mkdir(parents=True, exist_ok=True)
    os.environ["SPARK_LOCAL_DIRS"] = str(local_dir)
    os.environ["TMPDIR"] = str(local_dir)
    os.environ["TMP"] = str(local_dir)
    os.environ["TEMP"] = str(local_dir)

    spark = (
        SparkSession.builder
        .appName("EnterpriseHealthcareBenchmark")
        .config("spark.local.dir", str(local_dir))
        .config(
            "spark.hadoop.fs.s3a.impl",
            "org.apache.hadoop.fs.s3a.S3AFileSystem",
        )
        .config(
            "spark.hadoop.fs.s3a.aws.credentials.provider",
            "com.amazonaws.auth.InstanceProfileCredentialsProvider",
        )
        .config("spark.sql.adaptive.enabled", "true")
        .config(
            "spark.sql.shuffle.partitions",
            str(max(args.partitions, 4)),
        )
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")
    started = time.perf_counter()

    patients = (
        spark.range(
            0,
            args.rows,
            1,
            numPartitions=args.partitions,
        )
        .withColumnRenamed("id", "patient_id")
        .withColumn(
            "age",
            (
                F.pmod(
                    F.col("patient_id") * F.lit(37),
                    F.lit(83),
                )
                + 18
            ).cast(IntegerType()),
        )
        .withColumn(
            "gender",
            F.when(
                F.pmod(F.col("patient_id"), 2) == 0,
                F.lit("F"),
            ).otherwise(F.lit("M")),
        )
        .withColumn(
            "region",
            F.element_at(
                F.array(
                    F.lit("Northeast"),
                    F.lit("South"),
                    F.lit("Midwest"),
                    F.lit("West"),
                ),
                (
                    F.pmod(F.col("patient_id"), 4) + 1
                ).cast(IntegerType()),
            ),
        )
        .withColumn(
            "diagnosis",
            F.element_at(
                F.array(
                    F.lit("Diabetes"),
                    F.lit("Hypertension"),
                    F.lit("Asthma"),
                    F.lit("CHF"),
                    F.lit("COPD"),
                    F.lit("Arthritis"),
                ),
                (
                    F.pmod(F.col("patient_id"), 6) + 1
                ).cast(IntegerType()),
            ),
        )
        .withColumn(
            "annual_cost",
            (
                F.pmod(
                    F.col("patient_id") * F.lit(7919),
                    F.lit(120000),
                )
                + 2000
            ).cast(DoubleType()),
        )
        .withColumn(
            "risk_score",
            F.round(
                F.col("age") * F.lit(0.35)
                + F.pmod(
                    F.col("patient_id"),
                    100,
                )
                * F.lit(0.65),
                2,
            ),
        )
        .withColumn(
            "event_date",
            F.expr(
                "date_add("
                "date'2024-01-01', "
                "cast(patient_id % 730 as int)"
                ")"
            ),
        )
        .select(
            "patient_id",
            "age",
            "gender",
            "region",
            "diagnosis",
            "annual_cost",
            "risk_score",
            "event_date",
        )
    )

    summary = (
        patients
        .groupBy("region", "diagnosis")
        .agg(
            F.count("*").alias("patient_count"),
            F.round(
                F.avg("annual_cost"),
                2,
            ).alias("avg_annual_cost"),
            F.round(
                F.avg("risk_score"),
                2,
            ).alias("avg_risk_score"),
        )
        .orderBy("region", "diagnosis")
    )

    output_path = args.output.rstrip("/")

    (
        patients.write
        .mode("overwrite")
        .partitionBy("region")
        .parquet(f"{output_path}/patients")
    )

    (
        summary.write
        .mode("overwrite")
        .parquet(f"{output_path}/summary")
    )

    elapsed = time.perf_counter() - started

    metrics = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "rows": args.rows,
        "partitions": args.partitions,
        "elapsed_seconds": round(elapsed, 3),
        "rows_per_second": round(args.rows / elapsed, 2),
        "spark_version": spark.version,
        "output": output_path,
    }

    print(json.dumps(metrics, sort_keys=True))
    spark.stop()


if __name__ == "__main__":
    main()
