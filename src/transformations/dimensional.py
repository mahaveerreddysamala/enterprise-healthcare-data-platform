"""Build a warehouse-friendly dimensional model from Silver events."""
from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def build_dim_patient(events: DataFrame) -> DataFrame:
    return (
        events.select("patient_id", "age", "sex", "state", "insurance_type")
        .dropDuplicates(["patient_id"])
        .withColumn("patient_sk", F.xxhash64("patient_id"))
    )


def build_dim_provider(events: DataFrame) -> DataFrame:
    return (
        events.select("provider_id", "specialty", "facility_id")
        .dropDuplicates(["provider_id"])
        .withColumn("provider_sk", F.xxhash64("provider_id"))
    )


def build_dim_date(events: DataFrame) -> DataFrame:
    return (
        events.select(F.to_date("event_ts").alias("date"))
        .dropDuplicates()
        .withColumn("date_sk", F.date_format("date", "yyyyMMdd").cast("int"))
        .withColumn("year", F.year("date"))
        .withColumn("quarter", F.quarter("date"))
        .withColumn("month", F.month("date"))
        .withColumn("week", F.weekofyear("date"))
        .withColumn("day_of_week", F.dayofweek("date"))
    )


def build_fact_encounter(events: DataFrame) -> DataFrame:
    return (
        events.select(
            "event_id", "patient_id", "provider_id", "facility_id", "event_ts",
            "diagnosis_code", "readmitted_30_days", "total_cost"
        )
        .withColumn("patient_sk", F.xxhash64("patient_id"))
        .withColumn("provider_sk", F.xxhash64("provider_id"))
        .withColumn("date_sk", F.date_format(F.to_date("event_ts"), "yyyyMMdd").cast("int"))
        .withColumn("encounter_count", F.lit(1))
    )
