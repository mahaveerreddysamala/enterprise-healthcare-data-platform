"""Canonical event contract shared by ingestion, Spark, SQL and ML layers."""
from __future__ import annotations

from dataclasses import dataclass

COLUMNS = [
    "encounter_id", "patient_id", "provider_id", "facility_id", "event_date",
    "age", "gender", "chronic_condition", "emergency_visit", "length_of_stay",
    "total_cost", "readmitted_30d", "diagnosis_code", "payer_type",
]

@dataclass(frozen=True)
class HealthcareEventContract:
    required_columns: tuple[str, ...] = tuple(COLUMNS)
    partition_column: str = "event_date"
    primary_key: tuple[str, ...] = ("encounter_id",)
