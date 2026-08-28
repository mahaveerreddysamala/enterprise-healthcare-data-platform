# Enterprise Healthcare Data Platform

[![CI](https://github.com/mahaveerreddysamala/enterprise-healthcare-data-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/mahaveerreddysamala/enterprise-healthcare-data-platform/actions)

A production-oriented **Senior Data Engineer + Senior Data Scientist** portfolio project for building a scalable healthcare data platform, analytics warehouse, distributed Spark processing pipeline, and machine-learning workflow using synthetic data.

> **Data policy:** synthetic data only. No real patients, PHI, or clinical records are included.

---

## Executive Summary

This platform demonstrates an end-to-end healthcare data engineering and machine learning architecture covering:

- Large-scale synthetic healthcare event generation
- Canonical data contracts
- PySpark Bronze → Silver → Gold processing
- Data validation and quality controls
- Partitioned Parquet data
- Patient-level feature engineering
- Dimensional analytics
- Healthcare ML workflows
- MLflow experiment tracking
- Batch inference
- Airflow orchestration design
- Dockerized execution
- Terraform AWS infrastructure
- AWS EC2 + SSM + S3 distributed Spark benchmarking
- Automated Ruff + pytest CI

The project has been validated with a **measured 100,000-row Spark benchmark running on AWS EC2 and writing partitioned Parquet results to Amazon S3**.

---

# Architecture

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
        │                   │
        │ Python 3.11       │
        │ Java 17           │
        │ Spark 3.5.3       │
        └─────────┬─────────┘
                  │
                  │ PySpark / S3A
                  ▼
        ┌───────────────────┐
        │     Amazon S3     │
        │                   │
        │ Partitioned       │
        │ Parquet Results   │
        └───────────────────┘