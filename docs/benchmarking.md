# Benchmarking

## Goal

Measure the platform rather than estimating performance. The repository supports a staged benchmark from developer-scale data through the portfolio target of 50M+ events.

## Workloads

| Workload | Recommended use |
|---:|---|
| 10K | smoke test |
| 100K | integration test |
| 1M | local benchmark |
| 10M | Spark/distributed benchmark |
| 50M+ | portfolio benchmark |

## Generation benchmark

Run:

```bash
python scripts/benchmark.py --rows 1000000 --chunk-size 100000 --output artifacts/benchmark_1m.json
```

For 50M:

```bash
python scripts/benchmark.py --rows 50000000 --chunk-size 500000 --output artifacts/benchmark_50m.json
```

The runner records:

- row count
- chunk size
- elapsed generation time
- rows/second
- generated Parquet size
- random seed

## Spark benchmark

Use the generated Parquet manifest as input to the Silver transformation:

```bash
spark-submit src/transformations/silver.py \
  --input data/benchmarks/events/events_part_00000.parquet \
  --output data/benchmarks/silver
```

For a distributed benchmark, measure the complete dataset rather than one file and capture Spark application metrics.

### Required measurements

- wall-clock runtime
- input records and bytes
- output records and bytes
- partition count
- shuffle read/write
- executor CPU and memory
- peak storage usage
- records/second

### Reproducibility

Use the same seed, row count, chunk size, Spark version, executor configuration, and storage location when comparing runs.

### Important

Do not put benchmark numbers in the README until they have actually been measured. Hardware, Spark configuration, storage, compression, and concurrency materially affect results.
