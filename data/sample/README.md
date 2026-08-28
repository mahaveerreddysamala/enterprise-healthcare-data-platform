# Sample Healthcare Dataset

This directory contains a small, representative synthetic dataset for local development and portfolio demonstrations.

- `events.csv` — 24 synthetic healthcare encounter records
- Full 100K benchmark — stored in Amazon S3 and not committed to GitHub
- No real patients, PHI, or clinical records are included

## Schema

The sample follows the canonical healthcare event contract used by the platform:

- Identity: `encounter_id`, `patient_id`
- Provider: `provider_id`, `facility_id`
- Time: `event_date`
- Demographics: `age`, `gender`
- Utilization: `emergency_visit`, `length_of_stay`
- Clinical: `chronic_condition`, `diagnosis_code`
- Financial: `total_cost`, `payer_type`
- Outcome: `readmitted_30d`

## Full benchmark

The measured 100K Spark benchmark is stored at:

`s3://mahaveer-healthcare-benchmark-560396669479/results/100k/`

The benchmark output is partitioned by region in Parquet format and includes a summary dataset.
