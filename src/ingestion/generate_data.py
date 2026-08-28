"""Scalable synthetic healthcare event generator using the canonical event contract."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from src.contracts.canonical_schema import COLUMNS


def generate_chunk(start: int, rows: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed + start)
    encounter_id = np.arange(start + 1, start + rows + 1, dtype=np.int64)
    patient_id = rng.integers(1, max(rows * 2, 1000), size=rows, dtype=np.int64)
    age = rng.integers(18, 91, size=rows)
    chronic = rng.binomial(1, 0.28, size=rows)
    emergency = rng.binomial(1, np.clip(0.16 + 0.12 * chronic, 0, 1), size=rows)
    los = np.maximum(0, rng.poisson(2.4 + 2.0 * emergency + chronic, size=rows))
    cost = np.round(
        np.maximum(
            100,
            600
            + age * 28
            + chronic * 1800
            + emergency * 4200
            + rng.normal(0, 900, size=rows),
        ),
        2,
    )
    p_readmit = np.clip(0.04 + 0.08 * chronic + 0.05 * emergency + 0.01 * los, 0, 0.8)
    event_date = (
        pd.Timestamp("2023-01-01")
        + pd.to_timedelta(rng.integers(0, 1095, size=rows), unit="D")
    ).date
    result = pd.DataFrame(
        {
            "encounter_id": encounter_id,
            "patient_id": patient_id,
            "provider_id": rng.integers(1, 100001, size=rows),
            "facility_id": rng.integers(1, 10001, size=rows),
            "event_date": event_date,
            "age": age,
            "gender": rng.choice(["F", "M", "X"], size=rows, p=[0.49, 0.49, 0.02]),
            "chronic_condition": chronic,
            "emergency_visit": emergency,
            "length_of_stay": los,
            "total_cost": cost,
            "readmitted_30d": rng.binomial(1, p_readmit),
            "diagnosis_code": rng.choice(["I10", "E11", "J18", "N18", "Z00"], size=rows),
            "payer_type": rng.choice(
                ["commercial", "medicare", "medicaid", "self_pay"],
                size=rows,
                p=[0.45, 0.30, 0.20, 0.05],
            ),
        }
    )
    return result[COLUMNS].astype(
        {
            "age": np.int32,
            "chronic_condition": np.int32,
            "emergency_visit": np.int32,
            "length_of_stay": np.int32,
            "readmitted_30d": np.int32,
        }
    )


def generate(rows: int, output: str, chunk_size: int, seed: int) -> None:
    """Generate a real Parquet dataset directory at ``output``."""
    if rows <= 0 or chunk_size <= 0:
        raise ValueError("rows and chunk_size must be positive")

    out = Path(output)
    if out.exists():
        if out.is_dir():
            shutil.rmtree(out)
        else:
            out.unlink()
    out.mkdir(parents=True, exist_ok=True)

    for start in range(0, rows, chunk_size):
        n = min(chunk_size, rows - start)
        part = out / f"part-{start // chunk_size:05d}.parquet"
        generate_chunk(start, n, seed).to_parquet(part, index=False)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--rows", type=int, default=10000)
    p.add_argument("--chunk-size", type=int, default=100000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--output", default="data/sample/events.parquet")
    a = p.parse_args()
    generate(a.rows, a.output, a.chunk_size, a.seed)


if __name__ == "__main__":
    main()
