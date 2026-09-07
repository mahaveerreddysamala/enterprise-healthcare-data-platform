# Readmission prediction time and label maturity

## Contract

This synthetic workflow predicts at discharge. `event_date` is interpreted as the discharge
date; current length of stay and encounter risk are therefore available. It is not an
admission-time model. Gold adds `prediction_time` and `label_available_at` (discharge + 30 days).
Both positive and negative synthetic labels mature after the full window. Early-confirmed
positive outcomes and real reporting delays are not modeled.

Historical encounters must have a strictly earlier discharge date. Encounter IDs select the
latest record deterministically, but do not imply within-day information availability; other
same-day encounters are excluded from history. `prior_readmissions` sums only labels available
on or before prediction. `mature_history_count` and `pending_history_count` distinguish observed
history from pending outcomes; zero observed readmissions does not mean pending outcomes are
confirmed negatives. These counts are diagnostic columns, not new model inputs.

Training requires prediction time and label availability strictly before the fit cutoff.
Evaluation requires prediction at/after cutoff, by the observation snapshot, and label
availability on or before that snapshot. Defaults use the latest observed discharge date as
the snapshot, never the maximum future label date. An explicit `--evaluation-as-of` is an
assertion about data observation coverage; callers must choose a justified snapshot.

The shared split applies to logistic training, nonlinear baseline and standalone evaluation.
Legacy Gold without an availability column derives the documented 30-day delay. Explicit
missing availability remains pending. Invalid dates, availability before prediction and mature
nonbinary targets fail clearly. Standalone evaluation cannot establish how an externally
supplied model was trained; artifact provenance still matters.

## Paired execution

Both runs used 20,000 generated encounters, seed 42, the same raw rows (verified equal),
cutoff 2024-07-01 and 15,800 latest-patient Gold rows. Baseline commit:
`71009fb466d6bcbf5dc71544f3b2d6507e7e69d5`. Corrected snapshot: 2025-12-30 UTC.

| Metric | Previous workflow | Maturity-aware workflow |
|---|---:|---:|
| Training rows | 6,915 | 6,494 |
| Holdout rows | 8,885 | 8,323 |
| PR-AUC (average precision) | 0.181864 | 0.177736 |
| ROC-AUC | 0.675143 | 0.675257 |
| Recall at 0.5 | 0.642935 | 0.639286 |
| Brier score | 0.229919 | 0.231034 |

421 pre-cutoff training rows and 562 holdout rows were excluded for immature labels.
187 historical outcomes were pending; 23 patients' prior-readmission counts changed.
These are protocol corrections, not measured performance gains. Training features and eligible
populations both change, so differences do not isolate a causal effect of one feature fix.
Class-balanced model outputs are not calibrated risk estimates; Brier score is a diagnostic.
See `label-maturity-results.json` for prevalence, versions and source hashes. Dashboard snapshots
now use this corrected 20K run; historical AWS benchmarks remain separate evidence.

## Reproduce

```bash
python scripts/run_readmission_validation.py --rows 20000 \
  --cutoff 2024-07-01 --evaluation-as-of 2025-12-30 \
  --output-dir artifacts/readmission-maturity
pytest -q tests/test_label_availability.py tests/test_temporal_models.py
```

To reproduce the old baseline, use a separate checkout of the baseline commit and run its
`scripts/run_readmission_validation.py --rows 20000` with a separate output directory.
Do not mix old Gold features or models with corrected evidence snapshots.

Boundary tests cover availability exactly at cutoff/snapshot, unknown labels, same-day
encounters, and invariance when an unavailable future outcome changes. Existing tests exercise
the pipeline, both trainers, cohort support handling and dashboard evidence.

## Limits

This is an explicit synthetic as-of contract, not verification against clinical event or
discharge timestamps. The dataset selects each patient's latest encounter in the supplied
snapshot; it is not a prospective rolling cohort reconstruction. Real deployment also needs
historical snapshot retention, feature ingestion timestamps, censoring rules and validated
outcome definitions. No clinical benefit, fairness certification or production impact is claimed.
