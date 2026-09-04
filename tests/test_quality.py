import pandas as pd

from src.ingestion.generate_data import generate_chunk
from src.quality.validation import quality_summary


def test_quality_summary():
    base = generate_chunk(0, 2, 42)
    df = pd.concat([base, base.iloc[[1]]], ignore_index=True)
    result = quality_summary(df)
    assert result["row_count"] == 3
    assert result["duplicate_encounters"] == 1
    assert result["invalid_age"] == 0
