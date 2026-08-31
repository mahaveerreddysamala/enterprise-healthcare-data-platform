# Enterprise Healthcare Data Platform

[![CI](https://github.com/mahaveerreddysamala/enterprise-healthcare-data-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/mahaveerreddysamala/enterprise-healthcare-data-platform/actions)

**Enterprise-style healthcare data platform for scalable ingestion, transformation, analytics, and downstream ML workloads.**

Built with **Python, PySpark, Apache Spark, Amazon S3, Amazon EC2, AWS Systems Manager, SQL, Airflow, Terraform, Docker, MLflow, and GitHub Actions**.

> **Data policy:** synthetic data only. No real patients, PHI, or clinical records are included.

---

## 1. Overview

This repository implements a complete data engineering platform that converts high-volume healthcare events into governed, analytics-ready data products.

The platform is designed around real-world engineering concerns: **data contracts, schema enforcement, quality validation, deduplication, partitioning, scalable Spark processing, dimensional modeling, orchestration, infrastructure as code, CI, and cloud performance troubleshooting**.

The pipeline supports workloads from development scale through a validated **50 million-record AWS Spark benchmark**.

### Core pipeline

```text
Healthcare Events
       │
       ▼
Canonical Data Contract
       │
       ▼
Schema + Data Quality Validation
       │
       ▼
Bronze — Raw / Immutable
       │
       ▼
Silver — Clean / Deduplicated
       │
       ▼
Gold — Analytics Data Products
       │
       ├──────────────► Dimensional Analytics / SQL
       │
       └──────────────► ML Feature Layer
```

---

## 2. Engineering Objectives

- Build a scalable healthcare data platform rather than a single ETL script.
- Process datasets from **10K to 50M records**.
- Establish a canonical event contract and explicit schemas.
- Implement **Bronze → Silver → Gold** processing.
- Apply deduplication, validation, derived metrics, and partitioning.
- Store compressed, partitioned **Parquet on Amazon S3**.
- Build warehouse-oriented fact and dimension structures.
- Orchestrate repeatable workflows with **Airflow**.
- Provide reproducible infrastructure through **Terraform and Docker**.
- Validate code through **automated CI**.
- Benchmark Spark on AWS and document performance bottlenecks and remediation.
- Produce reusable Gold datasets for downstream analytics and ML.

---

## 3. Architecture

```text
                         ┌──────────────────────────┐
                         │ Healthcare Event Data    │
                         │ 10K → 100K → 1M → 10M   │
                         │             → 50M       │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │ Canonical Data Contract   │
                         │ Schema + Quality Checks   │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │ Bronze                    │
                         │ Raw / Immutable Events    │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │ Silver                    │
                         │ Clean / Dedupe / Validate │
                         │ Derived Metrics / Partitions│
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │ Gold                      │
                         │ Patient / Analytics Data  │
                         └────────────┬─────────────┘
                                      │
                       ┌──────────────┼──────────────┐
                       ▼              ▼              ▼
                 SQL / Warehouse   BI Analytics   ML Features
                       │                             │
                       ▼                             ▼
                  Redshift / SQL              MLflow / Batch

Cloud Execution

AWS CLI → Systems Manager → EC2 → PySpark/S3A → Amazon S3
```

---

## 4. Data Engineering Workflow

### Ingestion

Synthetic healthcare events are generated in chunks so large workloads can be processed without requiring the complete dataset in memory.

The canonical contract covers:

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

### Bronze

Preserves ingestion-oriented events in a partition-friendly object-storage layout.

### Silver

Creates trusted records through:

- Explicit schema enforcement
- Primary-key deduplication
- Required-field and range validation
- Type consistency checks
- Derived cost-per-day metrics
- Utilization indicators
- Risk calculations
- Date partitioning

### Gold

Creates reusable patient-level and analytics-ready data products. Patient-level aggregation prevents repeated encounters from disproportionately influencing downstream analytics and ML workloads.

Key features include:

- Encounter count
- Prior readmissions
- Average length of stay
- Total cost
- Emergency utilization
- Risk segment

---

## 5. Scale & AWS Performance Benchmark

The platform was executed on AWS using **Amazon EC2 t3.small + Apache Spark 3.5.3 + Amazon S3**.

| Workload | Partitions | Runtime | Throughput | Result |
|---|---:|---:|---:|---|
| 100K | 2 | 22.866 sec | 4,373 rows/sec | ✅ SUCCESS |
| 1M | 2 | 27.710 sec | 36,088 rows/sec | ✅ SUCCESS |
| 10M | 2 | 52.146 sec | 191,768 rows/sec | ✅ SUCCESS |
| **50M** | **2** | **156.294 sec** | **319,909 rows/sec** | **✅ SUCCESS** |

### Verified environment

| Component | Configuration |
|---|---|
| Compute | Amazon EC2 `t3.small` |
| Region | `us-east-1` |
| OS | Amazon Linux 2023 |
| CPU | 2 vCPUs |
| Memory | ~1.9 GiB |
| Python | 3.11.15 |
| Java | OpenJDK Corretto 17.0.20 |
| Spark | 3.5.3 |
| Storage | Amazon S3 |
| Format | Snappy-compressed Parquet |
| Remote execution | AWS Systems Manager |

### 50M validated run

- **Records:** 50,000,000
- **Runtime:** 156.294 seconds
- **Throughput:** 319,909 rows/sec
- **Spark partitions:** 2
- **S3 objects:** 11
- **S3 output:** 440.1 MiB
- **Exit code:** 0

Output is partitioned by region:

```text
results/<workload>/
├── patients/
│   ├── region=Midwest/
│   ├── region=Northeast/
│   ├── region=South/
│   └── region=West/
└── summary/
```

> These are environment-specific benchmark measurements and should not be interpreted as universal Spark performance guarantees.

---

## 6. Production Troubleshooting Example

The AWS benchmark exposed a practical infrastructure problem rather than simply producing a successful happy-path run.

### Problem

The initial environment failed because Spark depended on a small `/tmp` `tmpfs` filesystem. AWS dependency distribution exhausted temporary storage even though the EC2 root filesystem had available capacity. The smaller `t3.micro` environment also experienced memory pressure and kernel OOM events.

### Resolution

1. Moved Spark local execution and temporary storage to the persistent benchmark volume.
2. Configured `SPARK_LOCAL_DIRS` and `TMPDIR` consistently.
3. Increased the benchmark environment from `t3.micro` to `t3.small`.
4. Re-ran progressively larger workloads.
5. Verified successful Parquet output in S3.

```bash
mkdir -p /opt/healthcare-benchmark/spark-local
export SPARK_LOCAL_DIRS=/opt/healthcare-benchmark/spark-local
export TMPDIR=/opt/healthcare-benchmark/spark-local
```

The corrected environment successfully completed **100K, 1M, 10M, and 50M** workloads.

---

## 7. Analytics Data Model

The platform supports warehouse-style dimensional analytics using fact and dimension structures.

```text
                 ┌─────────────────┐
                 │ Dim Patient     │
                 └────────┬────────┘
                          │
┌─────────────────┐       │       ┌─────────────────┐
│ Dim Provider    │───────┼───────│ Dim Facility   │
└─────────────────┘       │       └─────────────────┘
                          ▼
                 ┌─────────────────┐
                 │ Fact Encounter  │
                 └────────┬────────┘
                          │
                    Analytics / BI
```

SQL assets under `sql/` provide reusable dimensional and analytical queries.

---

## 8. Orchestration & Operational Design

The repository includes Airflow DAG assets and pipeline entry points for repeatable execution and backfill-oriented workflows.

Operational patterns include:

- Idempotent processing
- Partition-aware transformations
- Validation before downstream consumption
- Explicit data contracts
- Reproducible execution
- Automated testing
- Containerized runtime
- Infrastructure as code

---

## 9. Cloud & Engineering Stack

| Technology | Purpose |
|---|---|
| **Python** | Data engineering and pipeline implementation |
| **PySpark / Apache Spark** | Distributed processing |
| **Amazon S3** | Data lake / Parquet storage |
| **Amazon EC2** | Spark compute and benchmarking |
| **AWS Systems Manager** | Remote execution |
| **AWS Glue / Spark** | Distributed ETL architecture |
| **Amazon Redshift** | Warehouse / dimensional analytics |
| **Apache Airflow** | Orchestration and backfills |
| **SQL** | Analytics and warehouse modeling |
| **Terraform** | Infrastructure as code |
| **Docker** | Reproducible execution |
| **MLflow** | Downstream ML experiment tracking |
| **GitHub Actions** | CI automation |

Security principles include encrypted storage, blocked public S3 access, least-privilege IAM, no credentials in source control, and synthetic-only data.

---

## 10. Data Quality & Governance

Data quality is enforced as part of the platform pipeline rather than left to downstream reporting.

Controls include:

- Schema enforcement
- Required-field validation
- Range checks
- Duplicate detection
- Type consistency
- Partition validation
- Contract-oriented tests

The repository contains synthetic data only and is designed to demonstrate healthcare data engineering patterns without exposing real patient information.

---

## 11. Downstream ML Integration

ML is intentionally treated as a **consumer of the data platform**, not the primary purpose of the repository.

The Gold layer supports:

| Use Case | Model | Metrics |
|---|---|---|
| 30-day readmission | Logistic Regression | ROC-AUC, PR-AUC, Precision, Recall, F1 |
| Healthcare cost | HistGradientBoostingRegressor | MAE, RMSE, R² |
| Patient segmentation | MiniBatchKMeans | Cluster size and profiles |

The validated temporal readmission workflow achieved **0.6601 ROC-AUC** and **0.1753 PR-AUC** on an EC2 holdout at `2024-07-01`, with historical features restricted to prior encounters to reduce temporal leakage.

> ML outputs are engineering/analytics examples and are not clinical diagnoses or treatment recommendations.

---

## 12. Repository Structure

```text
enterprise-healthcare-data-platform/
│
├── src/
│   ├── contracts/          # Canonical data contracts
│   ├── ingestion/          # Scalable synthetic event generation
│   ├── transformations/    # Bronze/Silver/Gold Spark transformations
│   ├── quality/            # Schema and data-quality validation
│   └── models/             # Training, evaluation, scoring, MLflow
│
├── benchmark/              # AWS Spark benchmark workloads
├── dags/                   # Airflow orchestration assets
├── pipelines/              # Pipeline entry points
├── sql/                    # Dimensional and analytics SQL
├── tests/                  # Unit and contract tests
├── data/sample/            # Representative synthetic data
├── infrastructure/         # Terraform / cloud assets
├── docker/                 # Container assets
├── docs/                   # Architecture and technical documentation
├── scripts/                # Operational utilities
├── config/                 # Runtime configuration
├── .github/workflows/      # CI automation
├── pyproject.toml
└── requirements.txt
```

---

## 13. Quick Start

Create a virtual environment:

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
pytest
```

Start with the smaller synthetic workloads for local development before running cloud benchmarks.

---

## 14. AWS Benchmark Reproduction

Verify AWS authentication:

```powershell
aws sts get-caller-identity
```

Verify Systems Manager connectivity:

```powershell
aws ssm describe-instance-information `
  --region us-east-1 `
  --query "InstanceInformationList[].{InstanceId:InstanceId,PingStatus:PingStatus,Platform:PlatformName,AgentVersion:AgentVersion}" `
  --output table
```

Run the 50M benchmark through Systems Manager:

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

---

## 15. Engineering Outcomes

This implementation demonstrates end-to-end ownership of a cloud data platform, including:

- Scalable PySpark ETL
- AWS data lake architecture
- Bronze/Silver/Gold processing
- Data contracts and quality controls
- Partitioned Parquet design
- Dimensional warehouse modeling
- Airflow orchestration
- Spark performance benchmarking
- Cloud infrastructure troubleshooting
- Terraform and Docker practices
- CI automation
- Reusable analytics and ML-ready data products

---

## 16. Project Status

| Capability | Status |
|---|---|
| Synthetic data generation | ✅ Implemented |
| Canonical data contracts | ✅ Implemented |
| Bronze/Silver/Gold processing | ✅ Implemented |
| Data-quality validation | ✅ Implemented |
| SQL / dimensional analytics | ✅ Implemented |
| AWS Spark benchmark | ✅ Validated through 50M records |
| S3 Parquet output | ✅ Validated |
| Airflow assets | ✅ Included |
| Terraform assets | ✅ Included |
| Docker assets | ✅ Included |
| CI automation | ✅ Included |
| Downstream ML workflows | ✅ Included |

---

## 17. Disclaimer

This repository is an engineering implementation using synthetic healthcare data. It is intended to demonstrate cloud data platform architecture, distributed processing, data quality, analytics engineering, and operational practices. It does not contain real patient information and is not intended for clinical decision-making.
