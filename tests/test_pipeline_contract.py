from datetime import date

from pyspark.sql import SparkSession

from src.contracts.canonical_schema import COLUMNS
from src.transformations.gold import build_patient_gold
from src.transformations.silver import SCHEMA, transform


def test_canonical_contract_flows_from_bronze_to_gold() -> None:
    spark = SparkSession.builder.master("local[2]").appName("test-pipeline-contract").getOrCreate()
    try:
        rows = [
            (1, 10, 100, 1000, date(2024, 1, 1), 55, "F", 1, 0, 2, 1200.0, 0, "I10", "commercial"),
            (2, 10, 100, 1000, date(2024, 3, 1), 55, "F", 1, 1, 8, 5200.0, 1, "I10", "commercial"),
            (3, 20, 200, 2000, date(2024, 2, 1), 72, "M", 0, 0, 1, 900.0, 0, "Z00", "medicare"),
        ]
        bronze = spark.createDataFrame(rows, schema=SCHEMA)

        silver = transform(bronze)
        gold = build_patient_gold(silver)

        assert bronze.columns == COLUMNS
        assert silver.count() == 3
        assert gold.count() == 2
        patient = gold.filter("patient_id = 10").first().asDict()
        assert patient["encounter_count"] == 1
        assert patient["prior_readmissions"] == 0
        assert patient["readmitted_30d"] == 1
    finally:
        spark.stop()
