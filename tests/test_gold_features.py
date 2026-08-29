from src.models.feature_contract import NUMERIC, CATEGORICAL, TARGET


def test_ml_feature_contract_is_patient_level():
    assert NUMERIC == [
        "age",
        "current_chronic_condition",
        "current_emergency_visit",
        "current_length_of_stay",
        "current_risk_score",
        "encounter_count",
        "prior_readmissions",
        "avg_los",
        "total_cost",
    ]
    assert CATEGORICAL == ["gender", "risk_segment"]
    assert TARGET == "readmitted_30d"
