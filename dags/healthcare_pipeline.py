"""Airflow DAG for the local healthcare data platform workflow.

The DAG is intentionally environment-configurable so the same orchestration
shape can be used locally or adapted to a cloud execution environment.
"""
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

DATA_ROOT = "/data/healthcare"
BRONZE = f"{DATA_ROOT}/bronze/events"
SILVER = f"{DATA_ROOT}/silver"
GOLD = f"{DATA_ROOT}/gold"

with DAG(
    dag_id="healthcare_data_platform",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["healthcare", "pyspark", "data-engineering"],
    default_args={"retries": 2},
) as dag:
    generate = BashOperator(
        task_id="generate_synthetic_events",
        bash_command=(
            "mkdir -p {{ params.output_dir }} && "
            "python -m src.ingestion.generate_data "
            "--rows {{ params.rows }} "
            "--chunk-size 100000 "
            "--seed 42 "
            "--output {{ params.output_dir }}/events.parquet"
        ),
        params={"rows": 1000000, "output_dir": BRONZE},
    )

    quality_bronze = BashOperator(
        task_id="validate_bronze",
        bash_command=(
            "python -m src.quality.check_parquet "
            "--input {{ params.input }}"
        ),
        params={"input": f"{BRONZE}/events.parquet"},
    )

    silver = BashOperator(
        task_id="build_silver",
        bash_command=(
            "spark-submit src/transformations/silver.py "
            "--input {{ params.input }} "
            "--output {{ params.output }}"
        ),
        params={"input": f"{BRONZE}/events.parquet", "output": SILVER},
    )

    quality_silver = BashOperator(
        task_id="validate_silver",
        bash_command=(
            "python -m src.quality.check_parquet "
            "--input {{ params.input }}"
        ),
        params={"input": SILVER},
    )

    gold = BashOperator(
        task_id="build_gold",
        bash_command=(
            "python -m src.transformations.gold_job "
            "--input {{ params.input }} "
            "--output {{ params.output }}"
        ),
        params={"input": SILVER, "output": GOLD},
    )

    generate >> quality_bronze >> silver >> quality_silver >> gold
