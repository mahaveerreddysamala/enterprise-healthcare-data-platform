# 50M AWS Spark Benchmark

## Verified Result

The platform successfully processed **50,000,000 synthetic healthcare records** on the AWS benchmark environment.

| Metric | Result |
|---|---:|
| Instance | `t3.small` |
| CPU | 2 vCPUs |
| Memory | ~1.9 GiB |
| Spark | 3.5.3 |
| Python | 3.11.15 |
| Partitions | 2 |
| Records | **50,000,000** |
| Runtime | **156.294 seconds** |
| Throughput | **319,909.05 rows/sec** |
| Exit code | **0** |
| Status | **SUCCESS** |
| S3 objects | **11** |
| S3 output size | **440.1 MiB** |

Output:

```text
s3a://mahaveer-healthcare-benchmark-560396669479/results/50m-t3small/
```

## S3 Layout

```text
results/50m-t3small/
├── patients/
│   ├── region=Midwest/
│   ├── region=Northeast/
│   ├── region=South/
│   └── region=West/
└── summary/
```

The verified run produced eight patient Parquet files across four region partitions, one summary Parquet file, and two `_SUCCESS` markers, totaling 11 objects and 440.1 MiB.

## Scaling Results

| Workload | Runtime | Throughput |
|---|---:|---:|
| 100K | 22.866 sec | 4,373.25 rows/sec |
| 1M | 27.710 sec | 36,087.74 rows/sec |
| 10M | 52.146 sec | 191,768.23 rows/sec |
| **50M** | **156.294 sec** | **319,909.05 rows/sec** |

The workload increased from 10M to 50M records while remaining on the same 2-partition, `t3.small` configuration. Runtime increased from 52.146 seconds to 156.294 seconds, while measured throughput increased from 191,768.23 to 319,909.05 rows/sec.

These results are environment-specific measurements and should not be interpreted as universal Spark performance guarantees.

## Infrastructure Lessons

The benchmark series exposed two practical constraints that were resolved during testing:

1. Spark local execution initially depended on a small `/tmp` `tmpfs`; redirecting Spark temporary/local storage to the persistent benchmark volume avoided `No space left on device` errors during dependency distribution.
2. The earlier `t3.micro` environment experienced kernel OOM pressure. The benchmark was stabilized on `t3.small`, which provided approximately 1.9 GiB of memory.

## Reproduction

Run the benchmark through AWS Systems Manager with Spark local and temporary storage pointed at the persistent volume:

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

Verify the command and S3 output after completion using the AWS CLI.
