from src.contracts.canonical_schema import COLUMNS, HealthcareEventContract


def test_canonical_contract():
    contract = HealthcareEventContract()
    assert contract.required_columns == tuple(COLUMNS)
    assert contract.partition_column == "event_date"
    assert contract.primary_key == ("encounter_id",)
