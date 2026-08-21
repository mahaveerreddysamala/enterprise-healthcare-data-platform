"""Gold-layer patient aggregates for analytics and ML features."""
from pyspark.sql import functions as F


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
    ).withColumn(
        "risk_segment",
        F.when(F.col("avg_risk_score") >= 0.70, "critical")
         .when(F.col("avg_risk_score") >= 0.45, "high")
         .when(F.col("avg_risk_score") >= 0.20, "medium")
         .otherwise("low")
    )
