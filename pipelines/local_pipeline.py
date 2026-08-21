"""Minimal orchestration entry point; production deployment can map this to Airflow."""
from pathlib import Path

from src.ingestion.generate_data import generate


def run_local_pipeline(rows: int = 10_000) -> Path:
    output = Path("data/sample/events.parquet")
    generate(rows=rows, output=str(output), chunk_size=100_000, seed=42)
    return output


if __name__ == "__main__":
    print(run_local_pipeline())
