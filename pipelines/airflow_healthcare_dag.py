"""Orchestration blueprint for the healthcare platform."""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    "healthcare_enterprise_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["healthcare", "spark", "ml"],
) as dag:
    ingest = BashOperator(task_id="ingest", bash_command="python src/ingestion/ingest.py")
    transform = BashOperator(task_id="transform", bash_command="python src/transformations/silver.py")
    features = BashOperator(task_id="features", bash_command="python src/features/feature_engineering.py")
    score = BashOperator(task_id="batch_score", bash_command="python src/models/score_patients.py --help")
    ingest >> transform >> features >> score
