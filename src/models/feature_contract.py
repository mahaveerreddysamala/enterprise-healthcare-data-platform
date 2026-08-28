"""Feature contract shared by training and scoring."""
from __future__ import annotations

NUMERIC = [
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
CATEGORICAL = ["gender", "risk_segment"]
TARGET = "readmitted_30d"
