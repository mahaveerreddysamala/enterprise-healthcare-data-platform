# Cloud Architecture

```text
Sources / synthetic events
        |
        v
AWS S3 Raw Zone
        |
   AWS Glue / Spark
        |
Bronze -> Silver -> Gold
        |
        +----> Redshift analytics
        |
        +----> ML feature layer -> training / batch scoring
                              |
                           MLflow
```

## AWS mapping

- **S3:** durable raw, curated, and feature storage.
- **Glue/Spark:** distributed ETL and schema-aware transformations.
- **Redshift:** dimensional analytics and BI serving.
- **Airflow:** cross-service orchestration and retries.
- **MLflow:** experiment/model lifecycle tracking.
- **Terraform:** repeatable infrastructure provisioning.
- **Docker:** reproducible application runtime.

## Security principles

The Terraform foundation blocks public S3 access, enables versioning and server-side encryption, and keeps cloud credentials outside source control. Production deployments should use IAM roles, least privilege, VPC endpoints, centralized logging, KMS-managed keys, and secrets management.

## Cost/scaling strategy

Use Parquet, partition pruning, incremental processing, Spark adaptive execution, and lifecycle policies for object storage. Separate development from production state and use environment-specific Terraform variables.
