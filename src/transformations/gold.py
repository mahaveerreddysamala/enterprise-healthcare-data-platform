"""Gold-layer patient aggregates for analytics and ML features."""
from __future__ import annotations

import argparse

from pyspark.sql import SparkSession, functions as F


def build_patient_gold(df):
    return df.groupBy("patient_id").agg(
        F.first("age", ignorenulls=True).alias("age"),
        F.first("gender", ignorenulls=True).alias("gender"),
        F.countDistinct("encounter_id").alias("encounter_count"),
        F.sum("emergency_visit").alias("emergency_visits"),
        F.sum("length_of_stay").alias("total_los"),
        F.round(F.avg("length_of_stay"), 2).alias("avg_los"),
        F.round(F.sum("total_cost"), 2).alias("total_cost"),
        F.sum("readmitted_30d").alias("prior_readmissions"),
        F.round(F.avg("risk_score"), 3).alias("avg_risk_score"),
        F.max("high_utilization").alias("high_utilization"),
        F.max("readmitted_30d").alias("readmitted_30d"),
        F.max("event_date").alias("event_date"),
    ).withColumn(
        "risk_segment",
        F.when(F.col("avg_risk_score") >= 0.70, "critical")
        .when(F.col("avg_risk_score") >= 0.45, "high")
        .when(F.col("avg_risk_score") >= 0.20, "medium")
        .otherwise("low"),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    spark = SparkSession.builder.appName("healthcare-gold").getOrCreate()
    try:
        silver = spark.read.parquet(args.input)
        gold = build_patient_gold(silver)
        gold.write.mode("overwrite").parquet(args.output)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
