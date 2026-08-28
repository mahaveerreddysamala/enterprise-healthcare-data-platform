"""Gold-layer patient aggregates for analytics and ML features."""
from __future__ import annotations

import argparse

from pyspark.sql import SparkSession, Window, functions as F


def build_patient_gold(df):
    """Build one patient row using only history before the latest encounter.

    The latest encounter supplies the prediction target and timestamp. Feature
    aggregates are computed strictly from prior encounters to avoid target
    leakage in chronological model evaluation.
    """
    window = Window.partitionBy("patient_id").orderBy(
        F.col("event_date").desc(), F.col("encounter_id").desc()
    )
    ordered = df.withColumn("_rn", F.row_number().over(window))

    latest = ordered.filter(F.col("_rn") == 1).select(
        "patient_id",
        F.col("event_date").alias("event_date"),
        F.col("age").alias("age"),
        F.col("gender").alias("gender"),
        F.col("readmitted_30d").alias("readmitted_30d"),
    )

    history = ordered.filter(F.col("_rn") > 1).groupBy("patient_id").agg(
        F.countDistinct("encounter_id").alias("encounter_count"),
        F.sum("emergency_visit").alias("emergency_visits"),
        F.sum("length_of_stay").alias("total_los"),
        F.round(F.avg("length_of_stay"), 2).alias("avg_los"),
        F.round(F.sum("total_cost"), 2).alias("total_cost"),
        F.sum("readmitted_30d").alias("prior_readmissions"),
        F.round(F.avg("risk_score"), 3).alias("avg_risk_score"),
        F.max("high_utilization").alias("high_utilization"),
    )

    result = latest.join(history, on="patient_id", how="left").select(
        "patient_id",
        "event_date",
        "age",
        "gender",
        F.coalesce(F.col("encounter_count"), F.lit(0)).cast("long").alias("encounter_count"),
        F.coalesce(F.col("emergency_visits"), F.lit(0)).cast("long").alias("emergency_visits"),
        F.coalesce(F.col("total_los"), F.lit(0)).cast("long").alias("total_los"),
        F.coalesce(F.col("avg_los"), F.lit(0.0)).alias("avg_los"),
        F.coalesce(F.col("total_cost"), F.lit(0.0)).alias("total_cost"),
        F.coalesce(F.col("prior_readmissions"), F.lit(0)).cast("long").alias("prior_readmissions"),
        F.coalesce(F.col("avg_risk_score"), F.lit(0.0)).alias("avg_risk_score"),
        F.coalesce(F.col("high_utilization"), F.lit(0)).cast("int").alias("high_utilization"),
        "readmitted_30d",
    )

    return result.withColumn(
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
