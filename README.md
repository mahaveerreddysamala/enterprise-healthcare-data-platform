# Enterprise Healthcare Data Platform

[![CI](https://github.com/mahaveerreddysamala/enterprise-healthcare-data-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/mahaveerreddysamala/enterprise-healthcare-data-platform/actions)

A production-oriented **Senior Data Scientist** portfolio project for building a scalable healthcare data platform, analytics warehouse, distributed Spark processing pipeline, and machine-learning workflow using synthetic data.

> **Data policy:** synthetic data only. No real patients, PHI, or clinical records are included.

## Executive Summary

This platform demonstrates an end-to-end healthcare data engineering and machine learning architecture covering large-scale synthetic healthcare event generation, canonical data contracts, PySpark Bronze → Silver → Gold processing, data validation, partitioned Parquet storage, patient-level feature engineering, dimensional analytics, ML workflows, MLflow tracking, batch inference, Airflow orchestration design, Dockerized execution, Terraform infrastructure, and AWS benchmarking.

The project includes measured Spark benchmarks on AWS EC2 writing partitioned Parquet results to Amazon S3.

## Architecture

```text
                    ┌──────────────────────────────┐
                    │ Synthetic Healthcare Events  │
                    │ 10K → 100K → 1M → 10M → 50M │
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
| 100K | AWS Spark integration benchmark | ✅ Measured |
| **1M** | AWS Spark performance benchmark | ✅ **Measured** |
| **10M** | Distributed Spark benchmark | ✅ **Measured** |
| **50M** | Portfolio-scale Spark benchmark | ✅ **Measured** |

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

### Benchmark Results

| Workload | Rows | Partitions | Runtime | Throughput | S3 objects | S3 size | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| 100K | 100,000 | 2 | 22.866 sec | 4,373.25 rows/sec | 11 | — | ✅ Success |
| 1M | 1,000,000 | 2 | 27.710 sec | 36,087.74 rows/sec | 11 | 10.0 MiB | ✅ Success |
| **10M** | **10,000,000** | **2** | **52.146 sec** | **191,768.23 rows/sec** | **11** | — | ✅ **Success** |
| **50M** | **50,000,000** | **2** | **156.294 sec** | **319,909.05 rows/sec** | **11** | **440.1 MiB** | ✅ **Success** |

### 50M Benchmark Result

The 50M benchmark completed successfully on the same `t3.small` EC2 environment used for the smaller workloads.

| Metric | Measured Result |
|---|---:|
| Records processed | **50,000,000** |
| Spark partitions | **2** |
| Runtime | **156.294 seconds** |
| Throughput | **319,909.05 rows/sec** |
| Spark version | **3.5.3** |
| Exit code | **0** |
| S3 output objects | **11** |
| S3 output size | **440.1 MiB** |
| Status | **SUCCESS** |

Output location:

```text
s3a://mahaveer-healthcare-benchmark-560396669479/results/50m-t3small
```

The verified S3 layout contains regional patient Parquet partitions for Midwest, Northeast, South, and West plus a summary output.

### 10M Benchmark Result

The 10M benchmark used the same `t3.small` EC2 configuration and successfully processed ten million synthetic healthcare records.

| Metric | Measured Result |
|---|---:|
| Records processed | **10,000,000** |
| Spark partitions | **2** |
| Runtime | **52.146 seconds** |
| Throughput | **191,768.23 rows/sec** |
| Spark version | **3.5.3** |
| Exit code | **0** |
| Status | **SUCCESS** |

Output location:

```text
s3a://<benchmark-bucket>/results/10m-t3small
```

### 1M Benchmark Result

The 1M benchmark used the same `t3.small` EC2 configuration and successfully processed ten times as many records as the 100K run.

| Metric | Measured Result |
|---|---:|
| Records processed | **1,000,000** |
| Spark partitions | **2** |
| Runtime | **27.710 seconds** |
| Throughput | **36,087.74 rows/sec** |
| Spark version | **3.5.3** |
| Exit code | **0** |
| Status | **SUCCESS** |
| S3 output objects | **11** |
| S3 output size | **10.0 MiB** |

Output location:

```text
s3a://<benchmark-bucket>/results/1m-t3small
```

### 100K Benchmark Result

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

### Scaling Observation

The measured workload increased from 100K to 50M records on the same `t3.small` environment. Runtime increased from 22.866 seconds to 156.294 seconds while throughput increased from 4,373.25 to 319,909.05 rows/sec. These measurements show substantial amortization of Spark startup/JVM overhead on this benchmark environment.

These results are environment-specific reference measurements, not universal Spark performance guarantees.

### Verified S3 Layout

The benchmark writes patient data partitioned by region:

```text
results/<workload>/
├── patients/
│   ├── region=Midwest/
│   ├── region=Northeast/
│   ├── region=South/
│   └── region=West/
└── summary/
```

The verified 50M run produced 11 S3 objects totaling 440.1 MiB. The verified 1M run produced 11 S3 objects totaling 10.0 MiB, and the 100K run produced the same 11-object output structure.

### Benchmark Summary

The generated benchmark data is synthetic and can be aggregated by region and diagnosis for analytics validation.

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

After these changes, the 100K, 1M, 10M, and 50M benchmarks completed successfully.

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

Run a 50M benchmark:

```powershell
$cmd = aws ssm send-command `
  --region us-east-1 `
  --instance-ids <instance-id> `
  --document-name "AWS-RunShellScript" `
  --parameters 'commands=["rm -rf /opt/healthcare-benchmark/spark-local/*; mkdir -p /opt/healthcare-benchmark/spark-local; export SPARK_LOCAL_DIRS=/opt/healthcare-benchmark/spark-local; export TMPDIR=/opt/healthcare-benchmark/spark-local; python3.11 /opt/healthcare-benchmark/spark_healthcare_benchmark.py --rows 50000000 --partitions 2 --output s3a://<benchmark-bucket>/results/50m-t3small"]' `
  --timeout-seconds 1800 `
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
  s3://<benchmark-bucket>/results/50m-t3small/ `
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

### Leakage-Free Readmission Benchmark

The corrected temporal workflow rebuilt Gold features with current-encounter fields available at prediction time and historical aggregates restricted to prior encounters. The validated EC2 holdout at `2024-07-01` achieved:

| Metric | Result |
|---|---:|
| ROC-AUC | **0.6601** |
| PR-AUC | **0.1753** |
| Precision | **0.1630** |
| Recall | **0.6116** |
| F1 | **0.2574** |
| Training rows | **15,165** |
| Test rows | **183,501** |

This benchmark replaced the earlier invalid `ROC-AUC = 1.0` result that came from inconsistent feature availability during evaluation.

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

> Built a production-oriented healthcare data platform using Python, PySpark, AWS EC2, S3, and Systems Manager; implemented Bronze/Silver/Gold pipelines, healthcare data contracts, partitioned Parquet storage, patient-level feature engineering, dimensional analytics, readmission/cost/risk ML workflows, MLflow tracking, Docker/Airflow orchestration, Terraform infrastructure, and measured 100K, 1M, 10M, and 50M-row Spark benchmarks. The 50M benchmark achieved **156.294-second runtime and 319,909.05 rows/sec throughput** on a `t3.small` while writing partitioned Parquet results to Amazon S3.

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
- [x] **Measured 1M Spark benchmark on t3.small**
- [x] **Measured 10M Spark benchmark on t3.small**
- [x] **Measured 50M Spark benchmark on t3.small**
- [x] **Verified partitioned Parquet output in Amazon S3**
- [x] **Documented leakage-free temporal readmission benchmark**
- [ ] Production Airflow backfill/incremental strategy
- [ ] Deployable AWS Glue/Redshift implementation
- [ ] BI dashboard and measured screenshots

## Current Benchmark Status

```text
100K:   22.866 sec    |   4,373.25 rows/sec
1M:     27.710 sec    |  36,087.74 rows/sec
10M:    52.146 sec    | 191,768.23 rows/sec
50M:   156.294 sec    | 319,909.05 rows/sec
```

All four workloads completed successfully on the same `t3.small` benchmark environment using Spark 3.5.3 and S3A-backed Parquet output.
