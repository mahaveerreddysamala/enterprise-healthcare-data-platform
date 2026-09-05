from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.contracts.canonical_schema import COLUMNS


def test_committed_sample_matches_canonical_contract() -> None:
    sample = pd.read_csv(Path(__file__).parents[1] / "data" / "sample" / "events.csv")

    assert list(sample.columns) == COLUMNS
    assert sample["encounter_id"].is_unique
    assert sample["gender"].isin(["F", "M", "X"]).all()
    assert sample["chronic_condition"].isin([0, 1]).all()
    assert sample["readmitted_30d"].isin([0, 1]).all()
