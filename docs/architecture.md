# Architecture

## Layers

**Bronze** preserves source-shaped events and ingestion metadata. **Silver** applies schema enforcement, deduplication, validity checks, and derived metrics. **Gold** contains patient-level aggregates optimized for analytics and machine learning.

## Production cloud mapping

| Local component | AWS / Databricks equivalent |
|---|---|
| Parquet | S3 / Delta Lake |
| PySpark | EMR / Glue / Databricks |
| SQL gold tables | Redshift / Snowflake |
| Orchestration | Airflow / MWAA |
| ML tracking | MLflow |
| CI | GitHub Actions |

The design intentionally separates compute, storage, quality, and serving layers so individual components can scale independently.
