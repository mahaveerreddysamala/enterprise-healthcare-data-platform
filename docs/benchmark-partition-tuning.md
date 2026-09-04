# Spark Partition Tuning Benchmark

This experiment compares Apache Spark partition counts for the same 10,000,000-row synthetic healthcare workload on the same AWS EC2 `t3.small` environment.

## Environment

| Component | Configuration |
|---|---|
| Instance | AWS EC2 `t3.small` |
| Region | `us-east-1` |
| CPU | 2 vCPUs |
| Memory | ~1.9 GiB |
| Python | 3.11.15 |
| Apache Spark | 3.5.3 |
| Storage | Amazon S3 / Snappy Parquet |
| Workload | 10,000,000 synthetic rows |

## Results

| Partitions | Runtime | Throughput | Status |
|---:|---:|---:|---|
| **2** | **52.146 sec** | **191,768.23 rows/sec** | Success |
| 4 | 56.366 sec | 177,410.57 rows/sec | Success |
| 8 | 67.210 sec | 148,786.35 rows/sec | Success |
| 16 | 94.850 sec | 105,429.74 rows/sec | Success |

## Finding

For this specific 2-vCPU `t3.small` environment and workload, **2 partitions produced the fastest measured runtime and highest throughput**. Increasing the partition count from 2 to 4, 8, and 16 progressively increased runtime and reduced throughput.

This does not mean fewer partitions are universally better. Partition sizing depends on CPU cores, executor resources, input size, transformation complexity, shuffle behavior, storage throughput, and cluster topology. These results are environment-specific measurements.

## Benchmark Outputs

Each run wrote partitioned Parquet results to Amazon S3:

```text
s3://<benchmark-bucket>/results/10m-t3small/
s3://<benchmark-bucket>/results/10m-p4-t3small/
s3://<benchmark-bucket>/results/10m-p8-t3small/
s3://<benchmark-bucket>/results/10m-p16-t3small/
```

## Interview Takeaway

The experiment demonstrates practical Spark tuning rather than assuming that more partitions automatically improve performance. On a small two-core instance, additional task scheduling and execution overhead outweighed any benefit from increased partition parallelism for this workload.
