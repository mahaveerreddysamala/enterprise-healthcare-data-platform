# Local Spark worker execution and recovery

This completed experiment uses one Spark standalone master and one or two separate worker
processes on **one Linux machine**. No AWS resources or paid model APIs are used.
It demonstrates executor scheduling and task recovery, not multi-node or production resilience.

## Reproduce

Use Linux (or WSL2), Java 17 and Python 3.11/3.12, with enough memory for a driver,
master and two worker/executor processes. Install Spark in a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install pyspark==3.5.3
python scripts/run_local_workers.py --rows 1000000 --workers 1 --output artifacts/workers-one
python scripts/run_local_workers.py --rows 1000000 --workers 2 --output artifacts/workers-two
python scripts/run_local_workers.py --rows 1000000 --workers 2 --inject-failure --output artifacts/workers-retry
```

Each command requires a fresh output directory, launches its own master/workers on local
ports, waits for worker registration, runs Spark, validates output and cleans up its own
processes. Inspect `execution.json`, `metrics.json`, `application.log` and `events/`.
Failures produce a nonzero exit code and a failed execution report. The application timeout
is four minutes. The CI job repeats a 10,000-row two-worker failure run and uploads logs.

## Recorded results — September 11, 2026

All runs used Spark 3.5.3, Python 3.12, Java 17, eight input partitions, one core per executor,
512 MiB executor/driver heaps and local Parquet storage. Workers advertised 1 GiB each.

| Run | Rows | Executors | Workload seconds | Rows/second | Failed tasks / retries | Wall seconds |
|---|---:|---:|---:|---:|---:|---:|
| [One worker](evidence/local-workers/one.json) | 1,000,000 | 1 | 24.293 | 41,163.90 | 0 / 0 | 39.536 |
| [Two workers](evidence/local-workers/two.json) | 1,000,000 | 2 | 21.424 | 46,677.14 | 0 / 0 | 37.479 |
| [Two workers, injected failure](evidence/local-workers/retry.json) | 1,000,000 | 2 | 32.859 | 30,433.08 | 1 / 1 | 47.864 |

Workload timing includes generation, aggregation, writes and output readback checks.
Wall timing additionally includes startup and cleanup. Two workers were approximately
1.13x as fast in this single sequential comparison; there are no repetitions, confidence
intervals or controlled cache conditions. Do not generalize this to cluster scaling or
compare directly with the historical 50M-row AWS benchmark, which excludes these checks.

Every run verified 1,000,000 written patient rows, a summary patient-count total of 1,000,000,
and patient-ID sum 499,999,500,000. These checks catch common output loss/duplication;
they are not full row-by-row correctness proofs.

The failure run deliberately raises `controlled-local-task-failure` for partition zero
on attempt zero. The event log records stage 0, partition 0 failing on attempt 0 and
succeeding on attempt 1. Speculation is disabled and `spark.task.maxFailures=2`.
All jobs completed successfully. This tests task retry, not worker death, driver recovery
or network outages. The failure path adds a Python RDD conversion and cache, so its extra
runtime cannot be attributed solely to retry overhead.

Committed JSON includes event-log hashes and matching recovery evidence extracted from
local raw logs. Full logs are generated on reproduction and retained as CI artifacts for
CI runs; the original local raw logs are not committed.

## Portfolio wording

“Validated a one-million-row synthetic Spark workload using separate local worker processes;
verified controlled task recovery and Parquet row-count/checksum consistency, with repeatable
CI execution and event-log evidence.”

An [AWS or managed multi-node benchmark](multi-node-experiment.md) remains an optional,
separately budgeted follow-up. No paid infrastructure is required for this local demo.
