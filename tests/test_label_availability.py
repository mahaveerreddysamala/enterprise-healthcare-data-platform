from datetime import date

import pandas as pd
import pytest
from pyspark.sql import SparkSession

from src.models.label_availability import available_split
from src.transformations.gold import build_patient_gold
from src.transformations.silver import SCHEMA, transform


def test_maturity_boundaries_pending_labels_and_future_invariance():
    frame = pd.DataFrame({
        "event_date": ["2024-01-01", "2024-01-02", "2024-02-01", "2024-02-02", "2024-04-01"],
        "label_available_at": ["2024-01-31", "2024-02-01", "2024-03-02", None, "2024-05-01"],
        "readmitted_30d": [1, 0, 0, None, 1],
    })
    train, test, counts = available_split(frame, "2024-02-01", evaluation_as_of="2024-03-02")
    assert train.index.tolist() == [0]  # available exactly at fit cutoff is excluded
    assert test.index.tolist() == [2]  # available exactly at snapshot is included
    assert counts["train_pending_rows"] == 1
    assert counts["test_pending_rows"] == 1
    assert counts["after_snapshot_rows"] == 1
    frame.loc[[1, 3, 4], "readmitted_30d"] = [1, 1, 0]
    again, _, _ = available_split(frame, "2024-02-01", evaluation_as_of="2024-03-02")
    pd.testing.assert_frame_equal(train, again)


def test_derived_availability_and_invalid_dates():
    df = pd.DataFrame({"event_date": ["2024-01-01", "2024-03-01"], "readmitted_30d": [0, 1]})
    _, test, counts = available_split(df, "2024-02-01")
    assert test.empty and counts["test_pending_rows"] == 1
    df["label_available_at"] = ["2023-12-31", "2024-03-31"]
    with pytest.raises(ValueError, match="precede"):
        available_split(df, "2024-02-01")
    df["event_date"] = [None, "2024-03-01"]
    with pytest.raises(ValueError, match="prediction times"):
        available_split(df, "2024-02-01")


def test_gold_excludes_immature_outcomes_and_same_day_history():
    spark = SparkSession.builder.master("local[2]").appName("label-availability").getOrCreate()
    try:
        def gold(pending_target):
            rows = [
                (1, 10, 100, 1000, date(2024, 1, 1), 55, "F", 1, 0, 2, 1200., 1, "I10", "commercial"),
                (2, 10, 100, 1000, date(2024, 1, 2), 55, "F", 1, 0, 2, 1200., 1, "I10", "commercial"),
                (3, 10, 100, 1000, date(2024, 1, 20), 55, "F", 1, 0, 2, 1200., pending_target, "I10", "commercial"),
                (4, 10, 100, 1000, date(2024, 2, 1), 55, "F", 1, 0, 2, 1200., 1, "I10", "commercial"),
                (5, 10, 100, 1000, date(2024, 2, 1), 55, "F", 1, 0, 2, 1200., 0, "I10", "commercial"),
            ]
            return build_patient_gold(transform(spark.createDataFrame(rows, SCHEMA))).first().asDict()
        first = gold(0)
        assert first["encounter_count"] == 3
        assert first["prior_readmissions"] == 2
        assert first["mature_history_count"] == 2
        assert first["pending_history_count"] == 1
        assert first["label_available_at"] == date(2024, 3, 2)
        assert gold(1) == first  # unavailable future outcome cannot change current features
    finally:
        spark.stop()
