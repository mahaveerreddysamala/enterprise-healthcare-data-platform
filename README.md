# Enterprise Healthcare Data Platform

[![CI](https://github.com/mahaveerreddysamala/enterprise-healthcare-data-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/mahaveerreddysamala/enterprise-healthcare-data-platform/actions)

A production-oriented **Senior Data Engineer + Senior Data Scientist** portfolio project for building a scalable healthcare data platform, analytics warehouse, and machine-learning workflow using synthetic data.

> **Data policy:** synthetic data only. No real patients, PHI, or clinical records are included.

## Executive summary

This platform demonstrates an end-to-end architecture from large-scale event generation and data contracts through distributed processing, dimensional analytics, ML feature engineering, model evaluation, batch inference, orchestration, CI, containers, and AWS-ready infrastructure.

### Core capabilities

- Configurable synthetic healthcare event generation with deterministic seeds
- Canonical schema and primary-key contracts
- PySpark Bronze → Silver → Gold processing
- Partitioning, deduplication, validation, and data-quality controls
- Patient-level feature engineering
- Readmission classification
- Healthcare cost prediction
- Patient risk segmentation
- Time-aware model evaluation
- MLflow experiment tracking
- Batch patient scoring
- Airflow orchestration design
- Dockerized execution
- Terraform AWS foundation
- Automated Ruff + pytest CI on Python 3.11 and 3.12

## Architecture

```text
                    ┌──────────────────────────────┐
                    │ Synthetic Healthcare Events  │
                    │ 10K → 1M → 10M → 50M+       │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                         Canonical Data Contract
                                   │
                                   ▼
                         Schema / Quality Checks
                                   │
                                   ▼
                     ┌─────────────────────────┐
                     │ Bronze: Raw Events      │
                     └────────────┬────────────┘
                                  ▼
                     ┌─────────────────────────┐
                     │ Silver: Clean + Valid   │
                     │ dedupe / partitions     │
                     └────────────┬────────────┘
                                  ▼
                     ┌─────────────────────────┐
                     │ Gold: Patient Features  │
                     └───────┬─────────┬───────┘
                             │         │
                ┌────────────┘         └─────────────┐
                ▼                                    ▼
       Dimensional Analytics                  ML Feature Layer
       fact + dimensions                    ┌──────┬──────┬──────┐
                │                           │      │      │      │
                ▼                           ▼      ▼      ▼      │
          SQL / BI                    Readmit  Cost  Risk Seg.  │
                                            │      │      │
                                            └──────┴──────┘
                                                   ▼
                                                MLflow
                                                   ▼
                                            Batch Inference

AWS target: S3 → Glue/Spark → Gold → Redshift → BI / ML
```

## Canonical healthcare event contract

The platform standardizes ingestion around these fields:

| Domain | Fields |
|---|---|
| Identity | `encounter_id`, `patient_id` |
| Provider | `provider_id`, `facility_id` |
| Time | `event_date` |
| Demographics | `age`, `gender` |
| Utilization | `emergency_visit`, `length_of_stay` |
| Clinical | `chronic_condition`, `diagnosis_code` |
| Financial | `total_cost`, `payer_type` |
| Outcome | `readmitted_30d` |

## Scale strategy

The generator is chunk-oriented so local development does not require loading the complete benchmark into memory.

| Workload | Purpose |
|---|---|
| 10K | Developer smoke test |
| 100K | Unit/integration validation |
| 1M | Local performance testing |
| 10M | Distributed Spark benchmark |
| **50M+** | Portfolio-scale benchmark |

For a real benchmark, capture runtime, input size, output size, partition count, shuffle volume, executor configuration, and records/second. Do **not** claim benchmark numbers until they are measured on the target environment.

## Data engineering design

### Bronze

Immutable ingestion-oriented events stored in partition-friendly Parquet/object-storage layouts.

### Silver

- Explicit schema
- Primary-key deduplication
- Valid age and cost ranges
- Derived cost-per-day
- Utilization indicators
- Risk score
- Date partitioning

### Gold

Patient-level aggregates prevent repeated encounter rows from dominating ML training and provide reusable analytics features.

Key features include:

- encounter count
- prior readmissions
- average length of stay
- total cost
- emergency utilization
- risk segment

## Machine learning

| Problem | Model | Evaluation |
|---|---|---|
| 30-day readmission | Logistic Regression | ROC-AUC, PR-AUC, precision, recall, F1 |
| Healthcare cost | HistGradientBoostingRegressor | MAE, RMSE, R² |
| Patient segmentation | MiniBatchKMeans | cluster size + profile statistics |

The readmission workflow supports chronological evaluation when an event timestamp is available. MLflow records evaluation metrics and artifacts without embedding credentials or cloud endpoints in source code.

> Model outputs in this project are engineering/analytics examples, not clinical diagnoses or treatment recommendations.

## MLOps

```text
Gold features
    ↓
Time-aware evaluation
    ↓
Model artifact
    ↓
MLflow experiment
    ↓
Batch scoring
    ↓
Prediction / drift monitoring
```

Production monitoring should cover feature missingness, feature drift, prediction distribution, risk-band mix, data freshness, pipeline SLA, and matured model performance.

## Cloud architecture

The repository is designed to map to AWS services without coupling the local development workflow to a cloud account:

- **Amazon S3** — data lake storage
- **AWS Glue / Spark** — distributed ETL
- **Amazon Redshift** — dimensional analytics warehouse
- **Airflow** — orchestration and backfills
- **MLflow** — experiment/model tracking
- **Terraform** — repeatable infrastructure
- **Docker** — reproducible local/runtime environment

Security principles include encrypted storage, blocked public S3 access, least-privilege IAM, no credentials in source control, and synthetic-only repository data.

## Repository structure

```text
src/
  contracts/          canonical data contracts
  ingestion/          scalable synthetic data generation
  transformations/    Silver and Gold Spark transformations
  quality/            schema and data-quality validation
  models/             training, evaluation, scoring, MLflow

pipelines/             orchestration entry points
sql/                   dimensional and analytics SQL
tests/                 unit and contract tests
infrastructure/        Terraform / cloud deployment assets
docker/                container assets
docs/                  architecture, ML and MLOps documentation
.github/workflows/     CI automation
```

## Quick start

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
pytest -q
ruff check src tests
```

Generate a small dataset:

```bash
python -m src.ingestion.generate_data \
  --rows 10000 \
  --chunk-size 100000 \
  --output data/sample/events.parquet
```

Run the Spark Silver transformation:

```bash
spark-submit src/transformations/silver.py \
  --input data/sample/events.parquet \
  --output data/sample/silver
```

## CI

GitHub Actions validates the project on **Python 3.11 and 3.12** with dependency installation, Ruff, and pytest. The current CI pipeline is green.

## Engineering principles

1. **Scalability** — use Spark/distributed processing for production-scale paths.
2. **Data contracts** — schema and primary-key expectations are explicit and tested.
3. **Idempotency** — transformations are designed to be safely rerunnable.
4. **Reproducibility** — deterministic synthetic data and pinned dependencies.
5. **Observability** — expose validation and model metrics for operational monitoring.
6. **Cloud portability** — local layouts mirror object-storage partitioning patterns.
7. **Governance** — synthetic data only and no secrets committed to the repository.

## Portfolio / interview positioning

This project is designed to demonstrate ownership across:

**Data Engineering:** Python, SQL, PySpark, Spark optimization, Parquet, dimensional modeling, Airflow, AWS S3/Glue/Redshift, Terraform, Docker, CI/CD.

**Data Science / ML:** feature engineering, classification, regression, clustering, imbalanced-outcome metrics, time-aware evaluation, MLflow, batch inference, model monitoring.

### Resume-ready description

> Built a production-oriented healthcare data platform processing configurable large-scale synthetic encounter data using Python and PySpark; implemented Bronze/Silver/Gold pipelines, schema/data-quality contracts, patient-level feature engineering, dimensional analytics, readmission/cost/risk ML workflows, MLflow tracking, Docker/Airflow orchestration, AWS-ready Terraform infrastructure, and automated CI with Python 3.11/3.12.

## Roadmap

- [x] Repository foundation and CI
- [x] Canonical healthcare data contract
- [x] Scalable synthetic generator
- [x] Bronze/Silver/Gold processing
- [x] Data-quality and contract tests
- [x] ML training/evaluation/scoring foundation
- [x] MLflow tracking foundation
- [x] Docker/Airflow/AWS architecture foundation
- [ ] Execute and publish measured 50M+ benchmark
- [ ] Production Airflow backfill/incremental strategy
- [ ] Deployable AWS Glue/Redshift implementation
- [ ] BI dashboard and measured screenshots
