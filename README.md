# Enterprise Healthcare Data Platform

[![CI](https://github.com/mahaveerreddysamala/enterprise-healthcare-data-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/mahaveerreddysamala/enterprise-healthcare-data-platform/actions)

A production-oriented **Senior Data Engineer + Senior Data Scientist** portfolio project for building a scalable healthcare data platform, analytics warehouse, machine-learning workflow, and cloud benchmarking environment using synthetic data.

> **Data policy:** synthetic data only. No real patients, PHI, or clinical records are included.

## Executive Summary

This platform demonstrates an end-to-end architecture from synthetic healthcare event generation and data contracts through distributed Spark processing, dimensional analytics, ML feature engineering, model evaluation, batch inference, orchestration, CI, containers, and AWS-ready infrastructure.

### Core Capabilities

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
- AWS EC2 + Spark + S3A benchmark infrastructure
- Automated Ruff + pytest CI on Python 3.11 and 3.12

## Architecture

```text
                    ┌──────────────────────────────┐
                    │ Synthetic Healthcare Events  │
                    │ 10K → 100K → 1M → 10M+      │
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

AWS benchmark path: EC2 → Spark → S3A → S3 Parquet
AWS target architecture: S3 → Glue/Spark → Gold → Redshift → BI / ML
```

## Canonical Healthcare Event Contract

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

## Scale Strategy

The generator is chunk-oriented so local development does not require loading the complete benchmark into memory.

| Workload | Purpose |
|---|---|
| 10K | Developer smoke test |
| 100K | Integration and cloud validation |
| 1M | Performance testing |
| 10M | Distributed Spark benchmark |
| 50M+ | Portfolio-scale benchmark |

For production benchmarking, capture runtime, input size, output size, partition count, shuffle volume, executor configuration, and records/second. Benchmark numbers in this README are measured results from the EC2 environment described below.

# AWS EC2 + Spark + S3 Benchmark

The repository includes a working cloud benchmark using **Amazon EC2, Apache Spark 3.5.3, Hadoop S3A, and Amazon S3**.

The benchmark generates synthetic healthcare patient records, performs Spark processing and aggregation, writes partitioned Snappy-compressed Parquet to S3, and reports elapsed time and throughput.

## Verified Cloud Environment

| Resource | Configuration |
|---|---|
| Cloud | AWS |
| Region | us-east-1 |
| Compute | Amazon EC2 |
| CPU | 2 vCPUs |
| Memory | ~916 MiB |
| Root Storage | 100 GB |
| Available Storage during test | ~97 GB |
| Operating System | Amazon Linux |
| Python | 3.11.15 |
| Java | OpenJDK 17.0.20 |
| Apache Spark | 3.5.3 |
| Remote Execution | AWS Systems Manager (SSM) |

## Measured Benchmark Results

### 100,000 Healthcare Records — SUCCESS

| Metric | Measured Result |
|---|---:|
| Records | **100,000** |
| Spark partitions | **2** |
| Runtime | **21.891 seconds** |
| Throughput | **4,568.17 rows/sec** |
| Spark version | **3.5.3** |
| Exit code | **0** |
| Status | **SUCCESS** |
| Output format | **Snappy Parquet** |
| Storage | **Amazon S3** |

Output path:

```text
s3a://<benchmark-bucket>/results/100k
```

The benchmark completed successfully and generated partitioned patient data plus an aggregated summary dataset in S3.

### 10,000-Record Smoke Test — SUCCESS

| Metric | Measured Result |
|---|---:|
| Records | 10,000 |
| Spark partitions | 2 |
| Runtime | 20.434 seconds |
| Throughput | 489.37 rows/sec |
| Spark version | 3.5.3 |
| Status | SUCCESS |

The smoke test produced 11 S3 objects totaling approximately 178.2 KiB, including partitioned patient Parquet files, a summary Parquet file, and Spark `_SUCCESS` markers.

## S3 Data Layout

The benchmark writes healthcare patient data using `region` partitioning:

```text
results/
└── 100k/
    ├── patients/
    │   ├── region=Midwest/
    │   │   ├── part-00000-*.parquet
    │   │   └── part-00001-*.parquet
    │   ├── region=Northeast/
    │   │   ├── part-00000-*.parquet
    │   │   └── part-00001-*.parquet
    │   ├── region=South/
    │   │   ├── part-00000-*.parquet
    │   │   └── part-00001-*.parquet
    │   └── region=West/
    │       ├── part-00000-*.parquet
    │       └── part-00001-*.parquet
    └── summary/
        └── part-00000-*.parquet
```

Partitioning by region supports efficient filtering and downstream analytical workloads.

## Spark Temporary Storage Optimization

The initial EC2 benchmark exposed a practical Spark infrastructure issue. Although the EC2 root filesystem had approximately 97 GB available, `/tmp` was mounted as a 459 MB `tmpfs` filesystem.

Spark attempted to copy the approximately 268 MB AWS Java SDK bundle into its local dependency directory and failed with:

```text
java.io.IOException: No space left on device
```

The benchmark was corrected by moving Spark temporary storage to the larger EBS-backed filesystem:

```bash
mkdir -p /var/tmp/spark
export SPARK_LOCAL_DIRS=/var/tmp/spark
export TMPDIR=/var/tmp/spark
```

After this configuration, the 10K smoke test and 100K benchmark both completed successfully.

This demonstrates practical troubleshooting of **Spark local storage, JVM dependency distribution, EC2 disk configuration, and S3A workloads**.

## Running the Cloud Benchmark

Example EC2 execution:

```bash
export SPARK_LOCAL_DIRS=/var/tmp/spark
export TMPDIR=/var/tmp/spark

python3.11 /opt/healthcare-benchmark/spark_healthcare_benchmark.py \
  --rows 100000 \
  --partitions 2 \
  --output s3a://<benchmark-bucket>/results/100k
```

The benchmark can be scaled by changing `--rows` and `--partitions`.

## AWS Systems Manager Execution

The EC2 benchmark is remotely executed through AWS Systems Manager, avoiding the need for direct SSH access.

Example:

```powershell
$cmd = aws ssm send-command `
  --region us-east-1 `
  --instance-ids <instance-id> `
  --document-name "AWS-RunShellScript" `
  --parameters 'commands=["export SPARK_LOCAL_DIRS=/var/tmp/spark; export TMPDIR=/var/tmp/spark; python3.11 /opt/healthcare-benchmark/spark_healthcare_benchmark.py --rows 100000 --partitions 2 --output s3a://<benchmark-bucket>/results/100k"]' `
  --timeout-seconds 300 `
  --query "Command.CommandId" `
  --output text
```

Check execution:

```powershell
aws ssm get-command-invocation `
  --region us-east-1 `
  --command-id $cmd `
  --instance-id <instance-id> `
  --query "{Status:Status,Code:ResponseCode,Output:StandardOutputContent,Error:StandardErrorContent}" `
  --output json
```

## Data Engineering Design

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

## Machine Learning

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

## Cloud Architecture

The repository is designed to map to AWS services without coupling the local development workflow to a cloud account:

- **Amazon S3** — data lake storage
- **AWS Glue / Spark** — distributed ETL
- **Amazon Redshift** — dimensional analytics warehouse
- **Airflow** — orchestration and backfills
- **MLflow** — experiment/model tracking
- **Terraform** — repeatable infrastructure
- **Docker** — reproducible local/runtime environment
- **Amazon EC2** — benchmark compute
- **AWS Systems Manager** — remote benchmark execution

Security principles include encrypted storage, blocked public S3 access, least-privilege IAM, no credentials in source control, and synthetic-only repository data.

## Repository Structure

```text
src/
  contracts/          canonical data contracts
  ingestion/          scalable synthetic data generation
  transformations/    Silver and Gold Spark transformations
  quality/            schema and data-quality validation
  models/             training, evaluation, scoring, MLflow

benchmark/             EC2/Spark performance benchmark
pipelines/             orchestration entry points
sql/                   dimensional and analytics SQL
tests/                 unit and contract tests
infrastructure/        Terraform / cloud deployment assets
docker/                container assets
docs/                  architecture, ML and MLOps documentation
.github/workflows/     CI automation
```

## Quick Start

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

GitHub Actions validates the project on **Python 3.11 and 3.12** with dependency installation, Ruff, and pytest.

## Engineering Principles

1. **Scalability** — use Spark/distributed processing for production-scale paths.
2. **Data contracts** — schema and primary-key expectations are explicit and tested.
3. **Idempotency** — transformations are designed to be safely rerunnable.
4. **Reproducibility** — deterministic synthetic data and pinned dependencies.
5. **Observability** — expose validation and model metrics for operational monitoring.
6. **Cloud portability** — local layouts mirror object-storage partitioning patterns.
7. **Governance** — synthetic data only and no secrets committed to the repository.

## Portfolio / Interview Positioning

This project demonstrates ownership across:

**Data Engineering:** Python, SQL, PySpark, Spark optimization, Parquet, dimensional modeling, Airflow, AWS S3/Glue/Redshift/EC2, S3A, Terraform, Docker, CI/CD, performance benchmarking.

**Data Science / ML:** feature engineering, classification, regression, clustering, imbalanced-outcome metrics, time-aware evaluation, MLflow, batch inference, model monitoring.

### Resume-Ready Description

> Built a production-oriented healthcare data platform using Python and PySpark with Bronze/Silver/Gold pipelines, schema/data-quality contracts, patient-level feature engineering, readmission/cost/risk ML workflows, MLflow tracking, Docker/Airflow orchestration, AWS-ready Terraform infrastructure, and a measured EC2 Spark-to-S3 benchmark processing 100K synthetic healthcare records at 4,568 rows/sec.

## Roadmap

- [x] Repository foundation and CI
- [x] Canonical healthcare data contract
- [x] Scalable synthetic generator
- [x] Bronze/Silver/Gold processing
- [x] Data-quality and contract tests
- [x] ML training/evaluation/scoring foundation
- [x] MLflow tracking foundation
- [x] Docker/Airflow/AWS architecture foundation
- [x] EC2 + Spark + S3A benchmark infrastructure
- [x] Measured 10K smoke benchmark
- [x] Measured 100K benchmark
- [ ] Execute 1M benchmark
- [ ] Execute and publish measured 10M/50M+ benchmark
- [ ] Compare multiple partition configurations
- [ ] Production Airflow backfill/incremental strategy
- [ ] Deployable AWS Glue/Redshift implementation
- [ ] BI dashboard and measured screenshots
