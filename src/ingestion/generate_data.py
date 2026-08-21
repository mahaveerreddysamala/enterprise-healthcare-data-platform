"""Scalable synthetic healthcare event generator.

Generates chunked Parquet data so local development can use thousands of rows while
large runs can produce millions of records without holding the full dataset in memory.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd


def generate_chunk(start: int, rows: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed + start)
    patient_id = rng.integers(1, max(rows * 2, 1000), size=rows, dtype=np.int64)
    encounter_id = np.arange(start + 1, start + rows + 1, dtype=np.int64)
    age = rng.integers(18, 91, size=rows)
    chronic = rng.binomial(1, 0.28, size=rows)
    emergency = rng.binomial(1, 0.16 + 0.12 * chronic, size=rows)
    length_of_stay = np.maximum(0, rng.poisson(2.4 + 2.0 * emergency + chronic, size=rows))
    base_cost = 600 + age * 28 + chronic * 1800 + emergency * 4200
    cost = np.round(np.maximum(100, base_cost + rng.normal(0, 900, size=rows)), 2)
    readmit_probability = np.clip(0.04 + 0.08 * chronic + 0.05 * emergency + 0.01 * length_of_stay, 0, 0.8)
    readmitted = rng.binomial(1, readmit_probability)
    return pd.DataFrame({
        "encounter_id": encounter_id,
        "patient_id": patient_id,
        "age": age,
        "chronic_condition": chronic,
        "emergency_visit": emergency,
        "length_of_stay": length_of_stay,
        "total_cost": cost,
        "readmitted_30_days": readmitted,
    })


def generate(rows: int, output: str, chunk_size: int, seed: int) -> None:
    if rows <= 0 or chunk_size <= 0:
        raise ValueError("rows and chunk_size must be positive")
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    parts = []
    for start in range(0, rows, chunk_size):
        n = min(chunk_size, rows - start)
        part = out.parent / f"{out.stem}_part_{start // chunk_size:05d}.parquet"
        generate_chunk(start, n, seed).to_parquet(part, index=False)
        parts.append(part)
    # Keep the requested output as a small manifest rather than concatenating huge files.
    out.write_text("\n".join(str(p.name) for p in parts), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=10000)
    parser.add_argument("--chunk-size", type=int, default=100000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="data/sample/events.parquet")
    args = parser.parse_args()
    generate(args.rows, args.output, args.chunk_size, args.seed)


if __name__ == "__main__":
    main()
