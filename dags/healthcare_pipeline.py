"""Airflow DAG skeleton for the production pipeline.

Tasks are intentionally lightweight until cloud connections are configured.
"""
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="healthcare_data_platform",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["healthcare", "pyspark", "data-engineering"],
) as dag:
    generate = BashOperator(
        task_id="generate_or_ingest",
        bash_command="python -m src.ingestion.generate_data --rows 1000000 --output /data/events.parquet",
    )
    quality = BashOperator(
        task_id="run_quality_checks",
        bash_command="python -m src.quality.validation",
    )
    generate >> quality
