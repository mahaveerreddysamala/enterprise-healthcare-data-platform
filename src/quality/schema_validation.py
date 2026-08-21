"""Fail-fast validation for the canonical healthcare event contract."""
from __future__ import annotations

from typing import Iterable
from src.contracts.canonical_schema import COLUMNS


def validate_columns(columns: Iterable[str]) -> None:
    actual = set(columns)
    missing = [c for c in COLUMNS if c not in actual]
    if missing:
        raise ValueError(f"Healthcare event schema missing columns: {missing}")


def validate_unique_key(df) -> None:
    if df["encounter_id"].duplicated().any():
        raise ValueError("encounter_id must be unique")
