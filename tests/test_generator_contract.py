from src.contracts.canonical_schema import COLUMNS
from src.ingestion.generate_data import generate_chunk


def test_generator_matches_contract():
    df = generate_chunk(0, 100, 42)
    assert list(df.columns) == COLUMNS
    assert len(df) == 100
    assert df["encounter_id"].is_unique
    assert df["readmitted_30d"].isin([0, 1]).all()
