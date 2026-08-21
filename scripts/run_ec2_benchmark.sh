#!/usr/bin/env bash
set -euo pipefail

ROWS="${ROWS:-50000000}"
CHUNK_SIZE="${CHUNK_SIZE:-500000}"
BUCKET="${BENCHMARK_BUCKET:?Set BENCHMARK_BUCKET}"
PREFIX="${BENCHMARK_PREFIX:-benchmarks/50m}"

python3.11 scripts/benchmark.py \
  --rows "$ROWS" \
  --chunk-size "$CHUNK_SIZE" \
  --output "/opt/healthcare-benchmark/results/benchmark_${ROWS}.json"

aws s3 cp "/opt/healthcare-benchmark/results/benchmark_${ROWS}.json" \
  "s3://${BUCKET}/${PREFIX}/benchmark_${ROWS}.json"
