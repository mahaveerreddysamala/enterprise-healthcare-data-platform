import pandas as pd
import pytest

from src.contracts.canonical_schema import COLUMNS
from src.quality.schema_validation import validate_columns, validate_unique_key


def test_valid_schema():
    validate_columns(COLUMNS)


def test_missing_schema_column_fails():
    with pytest.raises(ValueError, match="missing columns"):
        validate_columns(COLUMNS[:-1])


def test_duplicate_encounter_fails():
    df = pd.DataFrame({"encounter_id": [1, 1]})
    with pytest.raises(ValueError, match="unique"):
        validate_unique_key(df)
