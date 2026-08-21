# AWS EC2 + S3 50M Benchmark

This benchmark provisions an Amazon Linux EC2 host with Spark/Python dependencies and an encrypted private S3 bucket for benchmark results. It does **not** create a VPC; provide an existing private subnet with outbound access through NAT.

## Architecture

```text
Terraform
   |
   +--> EC2 m6i.2xlarge (configurable)
   |       |
   |       +--> PySpark / generator
   |       +--> benchmark JSON
   |
   +--> Private S3 bucket
           |
           +--> benchmarks/50m/benchmark_50000000.json
```

## Prerequisites

- AWS account and credentials configured locally.
- Terraform >= 1.6.
- Existing VPC and private subnet with NAT egress.
- Sufficient EC2/S3 quota and budget approval.

## Provision

```bash
cd infrastructure/benchmark
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars with your VPC, subnet and unique bucket name
terraform init
terraform fmt -check
terraform validate
terraform plan
terraform apply
```

Never commit `terraform.tfvars` if it contains account-specific values or secrets.

## Run the 50M benchmark

After SSH/SSM access is configured and the repository is available on the host:

```bash
cd /path/to/enterprise-healthcare-data-platform
export BENCHMARK_BUCKET=$(terraform -chdir=infrastructure/benchmark output -raw bucket_name)
export ROWS=50000000
export CHUNK_SIZE=500000
bash scripts/run_ec2_benchmark.sh
```

The script uploads only the compact benchmark JSON to S3. Generated local Parquet data should be removed after the run unless it is intentionally being used for a storage benchmark.

## Measurements to report

- Total rows
- Wall-clock generation time
- Records/second
- Parquet bytes written
- EC2 instance type
- Spark/Python versions
- Number of output partitions/files
- S3 result URI

Do not publish performance numbers until they have been measured. For cost control, terminate the EC2 instance and destroy benchmark Terraform resources after the experiment.
