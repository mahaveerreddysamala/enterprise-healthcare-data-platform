"""Spark Silver transformation for the canonical healthcare event contract."""
from __future__ import annotations

import argparse

from pyspark.sql import SparkSession, functions as F, types as T

SCHEMA = T.StructType(
    [
        T.StructField("encounter_id", T.LongType(), False),
        T.StructField("patient_id", T.LongType(), False),
        T.StructField("provider_id", T.LongType(), False),
        T.StructField("facility_id", T.LongType(), False),
        T.StructField("event_date", T.DateType(), False),
        T.StructField("age", T.IntegerType(), False),
        T.StructField("gender", T.StringType(), False),
        T.StructField("chronic_condition", T.IntegerType(), False),
        T.StructField("emergency_visit", T.IntegerType(), False),
        T.StructField("length_of_stay", T.IntegerType(), False),
        T.StructField("total_cost", T.DoubleType(), False),
        T.StructField("readmitted_30d", T.IntegerType(), False),
        T.StructField("diagnosis_code", T.StringType(), False),
        T.StructField("payer_type", T.StringType(), False),
    ]
)


def transform(df):
    return (
        df.dropDuplicates(["encounter_id"])
        .filter(F.col("age").between(18, 120) & (F.col("total_cost") >= 0))
        .withColumn(
            "cost_per_day",
            F.round(
                F.col("total_cost") / F.greatest(F.col("length_of_stay"), F.lit(1)),
                2,
            ),
        )
        .withColumn("high_utilization", (F.col("length_of_stay") >= 7).cast("int"))
        .withColumn(
            "risk_score",
            F.round(
                F.col("chronic_condition") * 0.35
                + F.col("emergency_visit") * 0.25
                + F.when(F.col("length_of_stay") >= 7, 0.25).otherwise(0)
                + F.when(F.col("age") >= 65, 0.15).otherwise(0),
                3,
            ),
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    spark = SparkSession.builder.appName("healthcare-silver").getOrCreate()
    (
        transform(spark.read.schema(SCHEMA).parquet(args.input))
        .write.mode("overwrite")
        .partitionBy("event_date")
        .parquet(args.output)
    )
    spark.stop()


if __name__ == "__main__":
    main()
