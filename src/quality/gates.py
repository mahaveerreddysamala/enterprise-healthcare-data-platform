"""Spark-native quality evidence used before publishing demo model inputs."""
from pyspark.sql import functions as F

from src.transformations.silver import SCHEMA


def inspect_events(df):
    missing = sorted(set(SCHEMA.fieldNames()) - set(df.columns))
    if missing:
        raise ValueError(f"Missing event columns: {missing}")
    stats = df.agg(
        F.count("*").alias("rows"),
        F.countDistinct("encounter_id").alias("distinct_encounters"),
        *[F.sum(F.col(c).isNull().cast("long")).alias(f"null_{c}")
          for c in SCHEMA.fieldNames()],
        F.sum((~F.col("age").between(18, 120)).cast("long")).alias("invalid_age"),
        F.sum((F.col("total_cost") < 0).cast("long")).alias("negative_cost"),
        F.sum((~F.col("readmitted_30d").isin(0, 1)).cast("long")).alias("invalid_target"),
    ).first().asDict()
    rows = int(stats["rows"])
    return {"row_count": rows, "duplicate_encounters": rows - stats["distinct_encounters"],
            "null_cells": sum(stats[f"null_{c}"] or 0 for c in SCHEMA.fieldNames()),
            **{key: int(stats[key] or 0) for key in
               ("invalid_age", "negative_cost", "invalid_target")}}


def enforce_events(report):
    if report["row_count"] == 0 or any(value for key, value in report.items()
                                       if key != "row_count"):
        raise ValueError(f"Event quality gate failed: {report}")
