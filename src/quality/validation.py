"""Reusable data-quality checks for healthcare pipeline contracts."""
from __future__ import annotations

REQUIRED_COLUMNS = {
    "encounter_id", "patient_id", "age", "chronic_condition",
    "emergency_visit", "length_of_stay", "total_cost", "readmitted_30_days",
}


def validate_columns(columns):
    missing = REQUIRED_COLUMNS - set(columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")


def quality_summary(df):
    validate_columns(df.columns)
    return {
        "row_count": len(df),
        "null_cells": int(df[list(REQUIRED_COLUMNS)].isna().sum().sum()),
        "duplicate_encounters": int(df["encounter_id"].duplicated().sum()),
        "invalid_age": int((~df["age"].between(18, 120)).sum()),
        "negative_cost": int((df["total_cost"] < 0).sum()),
    }
