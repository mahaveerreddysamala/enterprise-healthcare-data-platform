# Multi-node execution protocol — prepared, not yet measured

The historical 50M-row EC2/S3 benchmark used one node. Multiple partitions or executors
on one machine do not establish multi-node scale. No new cloud infrastructure is provisioned
by this change. Use an approved cluster, unique shared output prefix and spending limit.

## Same workload, controlled comparison

Run `benchmark/spark_healthcare_benchmark.py` on one worker, then two workers with the
same Spark version, input row count and worker type. Start with 1M rows. Repeat with 4 and
8 partitions. Keep output storage identical, use fresh prefixes and record cold/warm cache
conditions. Do not compare these runs directly to the model-validation CLI's workload.

Example on an existing YARN cluster configured for S3A access (replace placeholders):

```bash
spark-submit --master yarn --deploy-mode client \
  --num-executors 2 --executor-cores 2 --executor-memory 2g \
  --conf spark.dynamicAllocation.enabled=false \
  --conf spark.eventLog.enabled=true \
  --conf spark.eventLog.compress=false \
  --conf spark.eventLog.rolling.enabled=false \
  --conf spark.eventLog.dir=hdfs:///spark-events \
  benchmark/spark_healthcare_benchmark.py \
  --rows 1000000 --partitions 4 --output s3a://YOUR_BUCKET/UNIQUE_RUN_PREFIX
```

Two executors may still be scheduled on the same host. Download the completed application's
uncompressed event log and inspect it alongside cluster inventory:

```bash
python scripts/summarize_spark_events.py downloaded-event-log \
  --require-multiple-hosts --output artifacts/multi-node-execution.json
```

The command fails if it does not observe at least two executor host identities. Host identities
must be checked against actual instance inventory; containers can have different hostnames on
one physical machine. The parser records executor removals, non-success task ends, higher
task attempts, failed jobs and application duration. A completed application is not proof of
successful output. Preserve workload metrics, output counts and the process exit status too.

## Failure experiment and cost

After the baseline succeeds, repeat in a disposable test cluster and deliberately terminate
one executor during processing. Preserve scheduler/event logs, verify replacement/retried
tasks and compare output row counts. This destructive experiment has not been executed.
Do not terminate a shared cluster worker or claim fault tolerance from a fixture-only test.

Supply `--allocated-hourly-cost` to the parser only with a verified aggregate cluster rate.
Its estimate covers application runtime; add startup/idle time, storage, transfer and managed
service fees from billing for a full cost comparison. Save region, instance types, timestamps,
partition counts, runtime, rows/sec, cost per million rows and failure/retry results for each run.
No dollar costs or multi-node speedup are claimed until that evidence exists.

Spark's [monitoring documentation](https://spark.apache.org/docs/latest/monitoring.html)
describes event logging and the History Server. This repository pins Spark 3.5.3; verify the
selected managed runtime and storage connector configuration before execution.
