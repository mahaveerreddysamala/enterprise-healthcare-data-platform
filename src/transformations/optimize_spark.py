"""Spark optimization helpers for large healthcare workloads.

The functions keep transformations explicit so they can be used from Databricks,
EMR, Glue or a local Spark session. No cloud credentials are required.
"""
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


def configure_spark(spark: SparkSession, shuffle_partitions: int = 200) -> SparkSession:
    """Apply production-oriented defaults without hard-coding cluster settings."""
    spark.conf.set("spark.sql.adaptive.enabled", "true")
    spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
    spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
    spark.conf.set("spark.sql.shuffle.partitions", str(shuffle_partitions))
    spark.conf.set("spark.sql.parquet.compression.codec", "snappy")
    return spark


def normalize_events(df: DataFrame) -> DataFrame:
    """Normalize the canonical event date and remove duplicate encounters."""
    return (
        df.withColumn("event_date", F.to_date("event_date"))
        .dropDuplicates(["encounter_id"])
    )


def partition_for_analytics(df: DataFrame) -> DataFrame:
    """Repartition by date for balanced time-series reads and writes."""
    return df.repartition("event_date")


def write_partitioned_parquet(df: DataFrame, path: str, mode: str = "overwrite") -> None:
    """Write analytics data with stable compression and date partitioning."""
    (
        df.write.mode(mode)
        .option("compression", "snappy")
        .partitionBy("event_date")
        .parquet(path)
    )
