from pyspark.sql import SparkSession
from src.transformations.dimensional import (
    build_dim_date,
    build_dim_patient,
    build_dim_provider,
    build_fact_encounter,
)


def test_dimensional_builders():
    spark = SparkSession.builder.master("local[2]").appName("test-dimensions").getOrCreate()
    try:
        rows = [
            ("e1", "p1", "pr1", "f1", "2026-01-01", "I10", 0, 100.0, 42, "M", "commercial"),
            ("e2", "p1", "pr1", "f1", "2026-01-02", "E11", 1, 250.0, 42, "M", "commercial"),
        ]
        cols = ["encounter_id", "patient_id", "provider_id", "facility_id", "event_date", "diagnosis_code", "readmitted_30d", "total_cost", "age", "gender", "payer_type"]
        df = spark.createDataFrame(rows, cols)
        assert build_dim_patient(df).count() == 1
        assert build_dim_provider(df).count() == 1
        assert build_dim_date(df).count() == 2
        assert build_fact_encounter(df).count() == 2
    finally:
        spark.stop()
