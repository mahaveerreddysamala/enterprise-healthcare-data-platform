# Enterprise Healthcare Data Platform

Production-oriented portfolio project combining **senior data engineering, data science, and cloud analytics** patterns on large-scale synthetic healthcare data.

> **Important:** This project uses synthetic data. No real patient or protected health information is included.

## What this demonstrates

- Large-scale synthetic healthcare event generation with deterministic seeds
- PySpark batch processing and scalable Bronze → Silver → Gold architecture
- Data quality, schema enforcement, deduplication, and anomaly checks
- Healthcare dimensional modeling and analytics-ready SQL
- Feature engineering for patient risk and utilization
- ML-ready readmission, cost, and risk-segmentation workflows
- Airflow orchestration, Docker, automated testing, and GitHub Actions CI
- Cloud-ready design for AWS S3/Glue/Redshift and Databricks/Delta Lake

## Architecture

```text
Synthetic Events
      |
      v
   Raw / S3
      |
      v
  PySpark Ingestion
      |
      +---- Data Quality / Schema Checks
      |
      v
 Bronze -> Silver -> Gold
      |                  |
      |                  +--> Dimensional Analytics
      v                  +--> BI / SQL
 Feature Engineering
      |
      +--> Readmission Prediction
      +--> Cost Prediction
      +--> Patient Risk Segmentation
      |
      v
 MLflow / Batch Inference
```

## Scale target

The generator supports configurable volumes so the same code can be used for local development and distributed workloads. The intended benchmark is **50M+ healthcare records/events** across encounters, diagnoses, medications, labs, and claims. CI uses a small dataset for speed.

## Repository layout

```text
src/                 Python and PySpark application code
pipelines/           orchestration entry points
sql/                 dimensional and analytics SQL
tests/               unit and data-contract tests
configs/              local and production-style configuration
data/sample/         tiny non-sensitive sample data
docs/                architecture and data dictionary
notebooks/            analysis workflow placeholders
.github/workflows/   CI/CD automation
```

## Quick start

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
pytest -q
python -m src.ingestion.generate_data --rows 10000 --output data/sample/events.parquet
```

For Spark:

```bash
spark-submit src/transformations/silver.py --input data/sample/events.parquet --output data/sample/silver
```

## Engineering principles

1. **Scalability:** avoid pandas-only transformations for production-scale paths.
2. **Idempotency:** pipeline stages can be rerun without creating duplicate records.
3. **Data contracts:** schemas and quality rules are explicit and testable.
4. **Observability:** pipeline outputs should expose row counts and validation metrics.
5. **Reproducibility:** deterministic synthetic generation and pinned dependencies.
6. **Cloud portability:** local paths mirror object-storage partition patterns.

## Roadmap

- [x] Repository foundation and CI
- [x] Scalable synthetic data generator
- [x] Bronze/Silver/Gold Spark transformations
- [x] Data-quality framework
- [ ] 50M+ benchmark and partition tuning
- [ ] Dimensional warehouse build
- [ ] ML training + MLflow tracking
- [ ] Airflow DAG and backfill strategy
- [ ] Terraform AWS infrastructure
- [ ] BI dashboard screenshots

## Portfolio positioning

This project is intentionally designed to support **Senior Data Engineer, Senior Data Scientist, Data Platform Engineer, and ML/Analytics Engineer** interviews by showing end-to-end ownership from ingestion through analytics and machine learning.
