# Scale and optimization strategy

## Target benchmark

The platform is designed to generate and process 50M+ synthetic healthcare events. Local development uses a much smaller dataset; the benchmark is intentionally parameterized so the same code can run on a Spark cluster.

## Spark design choices

- Adaptive Query Execution is enabled for dynamic partition coalescing and skew handling.
- Shuffle partitions are configurable instead of fixed to a single cluster size.
- Event data is deduplicated on the immutable event ID before downstream aggregation.
- Parquet with Snappy compression is used for columnar analytics workloads.
- Event date is used as the physical partition because most operational and reporting queries are time bounded.
- Dimension tables use deterministic hash surrogate keys so fact joins remain compact and reproducible.

## Production path

```text
S3 raw JSON/CSV
      |
      v
AWS Glue / Spark ingestion
      |
      v
Bronze Parquet
      |
      v
Silver: schema + DQ + dedupe
      |
      v
Gold: partitioned fact + dimensions
      |
      +--> Redshift / warehouse
      +--> ML feature datasets
      +--> BI semantic layer
```

## Scaling methodology

1. Run 100K rows as a smoke test.
2. Run 1M rows for local Spark validation.
3. Run 10M rows on a multi-worker Spark cluster.
4. Run 50M+ rows for the portfolio benchmark.
5. Record runtime, input size, output size, partition count and peak executor memory.

Do not commit generated benchmark data to Git. The repository stores generators and reproducible configuration, not large binary datasets.
