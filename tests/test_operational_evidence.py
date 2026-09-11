import json

import pytest
from pyspark.sql import SparkSession, functions as F

from scripts import run_readmission_validation as workflow
from src.quality.gates import inspect_events, enforce_events
from src.transformations.silver import SCHEMA
from datetime import date


def test_event_quality_rejects_nulls_duplicates_invalid_target_and_empty():
    spark = SparkSession.builder.master("local[2]").appName("quality-gates").getOrCreate()
    try:
        row = (1, 10, 100, 1000, date(2024, 1, 1), 55, "F", 1, 0, 2, 1200., 1, "I10", "commercial")
        valid = spark.createDataFrame([row], SCHEMA)
        enforce_events(inspect_events(valid))
        for invalid in [valid.union(valid), valid.limit(0),
                        valid.withColumn("event_date", F.lit(None).cast("date")),
                        valid.withColumn("readmitted_30d", F.lit(2)),
                        valid.withColumn("total_cost", F.lit(-1.0))]:
            with pytest.raises(ValueError, match="quality gate"):
                enforce_events(inspect_events(invalid))
    finally:
        spark.stop()


def test_failed_stage_writes_manifest_and_requires_fresh_recovery_dir(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("simulated storage failure")
    monkeypatch.setattr(workflow, "generate", fail)
    output = tmp_path / "failed"
    with pytest.raises(OSError):
        workflow.run(100, "2024-07-01", output, 50)
    report = json.loads((output / "pipeline-run.json").read_text())
    assert report["status"] == "failed"
    assert report["stages"][0]["error_type"] == "OSError"
    assert not (output / "readmission_model.joblib").exists()
    with pytest.raises(ValueError, match="new empty"):
        workflow.run(100, "2024-07-01", output, 50)
