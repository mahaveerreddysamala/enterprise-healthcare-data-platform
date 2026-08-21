import pandas as pd
from src.quality.validation import quality_summary


def test_quality_summary():
    df = pd.DataFrame({
        "encounter_id": [1, 2, 2],
        "patient_id": [10, 11, 11],
        "age": [45, 70, 70],
        "chronic_condition": [0, 1, 1],
        "emergency_visit": [0, 1, 0],
        "length_of_stay": [2, 8, 3],
        "total_cost": [500.0, 9000.0, 3000.0],
        "readmitted_30_days": [0, 1, 0],
    })
    result = quality_summary(df)
    assert result["row_count"] == 3
    assert result["duplicate_encounters"] == 1
    assert result["invalid_age"] == 0
