"""Run a measured synthetic-data benchmark and write JSON results.

Example:
  python scripts/benchmark.py --rows 1000000 --chunk-size 100000 --output artifacts/benchmark_1m.json

The script measures generation throughput and reports the generated Parquet size.
It intentionally does not claim Spark cluster performance; distributed benchmarks
should be run with spark-submit using the generated data.
"""
from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

from src.ingestion.generate_data import generate


def directory_size(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=1_000_000)
    parser.add_argument("--chunk-size", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="artifacts/benchmark.json")
    parser.add_argument("--data-dir", default="data/benchmarks/events")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if data_dir.exists():
        shutil.rmtree(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    manifest = data_dir / "events.parquet"

    started = time.perf_counter()
    generate(args.rows, str(manifest), args.chunk_size, args.seed)
    elapsed = time.perf_counter() - started
    size_bytes = directory_size(data_dir)
    result = {
        "rows": args.rows,
        "chunk_size": args.chunk_size,
        "elapsed_seconds": round(elapsed, 3),
        "rows_per_second": round(args.rows / elapsed, 2),
        "parquet_size_bytes": size_bytes,
        "parquet_size_mb": round(size_bytes / 1024**2, 2),
        "seed": args.seed,
        "status": "completed",
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
