# Enterprise Healthcare Data Platform

[![CI](https://github.com/mahaveerreddysamala/enterprise-healthcare-data-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/mahaveerreddysamala/enterprise-healthcare-data-platform/actions)

A production-oriented **Senior Data Engineer + Senior Data Scientist** portfolio project for building a scalable healthcare data platform, analytics warehouse, distributed Spark processing pipeline, and machine-learning workflow using synthetic data.

> **Data policy:** synthetic data only. No real patients, PHI, or clinical records are included.

## Executive Summary

This platform demonstrates an end-to-end healthcare data engineering and machine learning architecture covering large-scale synthetic healthcare event generation, canonical data contracts, PySpark Bronze → Silver → Gold processing, data validation, partitioned Parquet storage, patient-level feature engineering, dimensional analytics, ML workflows, MLflow tracking, batch inference, Airflow orchestration design, Dockerized execution, Terraform infrastructure, and AWS benchmarking.

The project includes a **measured 100,000-row Apache Spark benchmark running on AWS EC2 and writing partitioned Parquet results to Amazon S3**.

## Architecture

```text
                    ┌──────────────────────────────┐
                    │ Synthetic Healthcare Events  │
                    │ 10K → 100K → 1M → 10M → 50M+│
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

AWS Benchmark Architecture

        Windows PowerShell
               │
               │ AWS CLI
               ▼
        AWS Systems Manager
               │
               ▼
        ┌───────────────────┐
        │   EC2 Instance    │
        │ Python 3.11       │
        │ Java 17           │
        │ Spark 3.5.3       │
        └─────────┬─────────┘
                  │
                  │ PySpark / S3A
                  ▼
        ┌───────────────────┐
        │     Amazon S3     │
        │ Partitioned       │
        │ Parquet Results   │
        └───────────────────┘
```

## Canonical Healthcare Event Contract

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

| Workload | Purpose | Status |
|---|---|---|
| 10K | Developer smoke test | ✅ Complete |
| **100K** | AWS Spark integration benchmark | ✅ **Measured** |
| 1M | Performance testing | Planned |
| 10M | Distributed Spark benchmark | Planned |
| 50M+ | Portfolio-scale benchmark | Planned |

## AWS EC2 + Spark + S3 Benchmark

The cloud benchmark executes PySpark on Amazon EC2 through AWS Systems Manager and writes Snappy-compressed Parquet to Amazon S3 through Hadoop S3A.

### Verified Environment

| Component | Configuration |
|---|---|
| Instance type | **t3.small** |
| Region | `us-east-1` |
| Compute | Amazon EC2 |
| Operating System | Amazon Linux 2023 |
| CPU | 2 vCPUs |
| Memory | ~1.9 GiB |
| Root Storage | 100 GB |
| Python | 3.11.15 |
| Java | OpenJDK Corretto 17.0.20 |
| Apache Spark | 3.5.3 |
| Remote Execution | AWS Systems Manager |
| Storage | Amazon S3 |
| Format | Snappy Parquet |

### Official 100K Benchmark Result

The official benchmark uses the upgraded `t3.small` instance with approximately 1.9 GiB of memory.

| Metric | Measured Result |
|---|---:|
| Records processed | **100,000** |
| Spark partitions | **2** |
| Runtime | **22.866 seconds** |
| Throughput | **4,373.25 rows/sec** |
| Spark version | **3.5.3** |
| Exit code | **0** |
| Status | **SUCCESS** |
| S3 output objects | **11** |

Output location:

```text
s3a://<benchmark-bucket>/results/100k-t3small
```

The validated output contains eight patient Parquet files partitioned across four regions, one summary Parquet file, and two Spark `_SUCCESS` markers.

### Verified S3 Layout

```text
results/100k-t3small/
├── patients/
│   ├── region=Midwest/
│   ├── region=Northeast/
│   ├── region=South/
│   └── region=West/
└── summary/
```

### Benchmark Summary

The generated 100K dataset was aggregated by region and diagnosis. The verified summary includes balanced synthetic distributions across the modeled regions and diagnoses.

| Region | Diagnosis | Patient Count | Avg Annual Cost | Avg Risk Score |
|---|---|---:|---:|---:|
| Midwest | Asthma | 8,334 | $61,992.80 | 53.15 |
| Midwest | COPD | 8,333 | $61,988.97 | 53.15 |
| Midwest | Diabetes | 8,333 | $62,023.03 | 53.15 |
| Northeast | Asthma | 8,333 | $61,991.60 | 51.85 |
| Northeast | COPD | 8,333 | $61,996.87 | 51.85 |
| Northeast | Diabetes | 8,334 | $61,993.53 | 51.85 |
| South | Arthritis | 8,333 | $61,981.15 | 52.50 |
| South | CHF | 8,333 | $62,004.68 | 52.50 |
| South | Hypertension | 8,334 | $62,007.57 | 52.50 |
| West | Arthritis | 8,333 | $62,002.05 | 53.80 |
| West | CHF | 8,334 | $62,006.83 | 53.80 |
| West | Hypertension | 8,333 | $61,992.92 | 53.80 |

## Spark Temporary Storage Optimization

The first cloud benchmark attempt exposed a practical Spark infrastructure issue: `/tmp` was a 459 MB `tmpfs`, while Spark attempted to distribute a roughly 268 MB AWS Java SDK bundle. The job failed with `java.io.IOException: No space left on device` even though the EC2 root filesystem had ample free capacity.

The benchmark was corrected by directing Spark local execution and temporary storage to the persistent benchmark volume:

```bash
mkdir -p /opt/healthcare-benchmark/spark-local
export SPARK_LOCAL_DIRS=/opt/healthcare-benchmark/spark-local
export TMPDIR=/opt/healthcare-benchmark/spark-local
```

The benchmark script also configures the same local directory internally so Spark does not depend on the small `/tmp` filesystem.

The `t3.micro` environment also exposed memory pressure and kernel OOM events during repeated Spark dependency distribution. The benchmark environment was upgraded to `t3.small`, providing approximately 1.9 GiB of memory.

After these changes, SSM returned to `Online` and the 100K benchmark completed successfully.

## Reproducing the Benchmark

Verify AWS authentication:

```powershell
aws sts get-caller-identity
```

Verify EC2/SSM connectivity:

```powershell
aws ssm describe-instance-information `
  --region us-east-1 `
  --query "InstanceInformationList[].{InstanceId:InstanceId,PingStatus:PingStatus,Platform:PlatformName,AgentVersion:AgentVersion}" `
  --output table
```

Run the 100K benchmark:

```powershell
$cmd = aws ssm send-command `
  --region us-east-1 `
  --instance-ids <instance-id> `
  --document-name "AWS-RunShellScript" `
  --parameters 'commands=["export SPARK_LOCAL_DIRS=/opt/healthcare-benchmark/spark-local; export TMPDIR=/opt/healthcare-benchmark/spark-local; python3.11 /opt/healthcare-benchmark/spark_healthcare_benchmark.py --rows 100000 --partitions 2 --output s3a://<benchmark-bucket>/results/100k-t3small"]' `
  --timeout-seconds 300 `
  --query "Command.CommandId" `
  --output text
```

Retrieve results:

```powershell
aws ssm get-command-invocation `
  --region us-east-1 `
  --command-id $cmd `
  --instance-id <instance-id> `
  --query "{Status:Status,Code:ResponseCode,Output:StandardOutputContent,Error:StandardErrorContent}" `
  --output json
```

Verify S3 output:

```powershell
aws s3 ls `
  s3://<benchmark-bucket>/results/100k-t3small/ `
  --recursive `
  --human-readable `
  --summarize `
  --region us-east-1
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
- Data-quality validation

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

## Cloud Architecture

| Service | Purpose |
|---|---|
| Amazon S3 | Data lake and Parquet storage |
| Amazon EC2 | Spark benchmark compute |
| AWS Systems Manager | Remote execution |
| AWS Glue / Spark | Distributed ETL |
| Amazon Redshift | Dimensional analytics warehouse |
| Airflow | Orchestration and backfills |
| MLflow | Experiment/model tracking |
| Terraform | Infrastructure as code |
| Docker | Reproducible execution |

Security principles include encrypted storage, blocked public S3 access, least-privilege IAM, no credentials in source control, and synthetic-only repository data.

## Repository Structure

```text
src/
  contracts/          canonical data contracts
  ingestion/          scalable synthetic data generation
  transformations/    Silver and Gold Spark transformations
  quality/            schema and data-quality validation
  models/             training, evaluation, scoring, MLflow

benchmark/
  spark_healthcare_benchmark.py

data/sample/
  events.csv          representative synthetic sample
  README.md           sample-data documentation

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
```

Windows:

```powershell
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run tests:

```bash
pytest -q
```

Run linting:

```bash
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
8. **Measured performance** — benchmark claims are based on observed execution results.

## Portfolio / Interview Positioning

**Data Engineering:** Python, SQL, PySpark, Apache Spark, Spark optimization, Parquet, AWS S3, AWS EC2, AWS Systems Manager, AWS Glue, Redshift, Airflow, Terraform, Docker, CI/CD, data contracts, data quality, partitioning, distributed processing, performance benchmarking.

**Data Science / ML:** Python, Scikit-learn, feature engineering, classification, regression, clustering, imbalanced-outcome metrics, time-aware evaluation, MLflow, batch inference, model monitoring.

### Resume-Ready Description

> Built a production-oriented healthcare data platform using Python, PySpark, AWS EC2, S3, and Systems Manager; implemented Bronze/Silver/Gold pipelines, healthcare data contracts, partitioned Parquet storage, patient-level feature engineering, dimensional analytics, readmission/cost/risk ML workflows, MLflow tracking, Docker/Airflow orchestration, Terraform infrastructure, and a measured 100K-row Spark benchmark achieving **4,373 rows/sec** with **22.9-second runtime** on a `t3.small` while writing partitioned Parquet results to Amazon S3.

## Roadmap

- [x] Repository foundation and CI
- [x] Canonical healthcare data contract
- [x] Scalable synthetic generator
- [x] Bronze/Silver/Gold processing
- [x] Data-quality and contract tests
- [x] ML training/evaluation/scoring foundation
- [x] MLflow tracking foundation
- [x] Docker/Airflow/AWS architecture foundation
- [x] AWS EC2 + SSM + S3 benchmark infrastructure
- [x] Measured 10K smoke benchmark
- [x] **Measured 100K Spark benchmark on t3.small**
- [x] **Verified partitioned Parquet output in Amazon S3**
- [ ] Execute 1M benchmark
- [ ] Execute 10M distributed Spark benchmark
- [ ] Execute and publish measured 50M+ benchmark
- [ ] Compare multiple partition configurations
- [ ] Production Airflow backfill/incremental strategy
- [ ] Deployable AWS Glue/Redshift implementation
- [ ] BI dashboard and measured screenshots

## Current Benchmark Status

```text
Dataset:        100,000 synthetic healthcare records
Instance:       AWS EC2 t3.small
Runtime:        22.866 seconds
Throughput:     4,373.25 rows/sec
Partitions:     2
Spark:          3.5.3
Compute:        AWS EC2
Storage:        Amazon S3
Format:         Snappy Parquet
S3 Objects:     11
Status:         SUCCESS
```

The benchmark is a measured reference point for this EC2 configuration, not a universal Spark performance guarantee.
