# Next milestone: prediction-time and label-availability audit

## Review scope

Reviewed the repository's README, Gold transformation, feature contract, chronological
readmission trainer, evaluator, cohort diagnostics and temporal tests on 2026-09-06.
No healthcare code or benchmark results were changed or re-executed during this review.

The project already has substantial platform work: synthetic data contracts, Bronze/Silver/Gold
processing, Spark benchmark tooling, chronological model evaluation, cohort diagnostics and a
dashboard. Another generic RAG feature is not the highest-value next step for its ML evidence.

## Concrete gap

[`build_patient_gold`](../src/transformations/gold.py) orders encounters by event date and ID,
then sums `readmitted_30d` across every earlier-ranked encounter. It does not check when each
30-day outcome became known. [`train`](../src/models/train_readmission.py) selects training rows
by `event_date < cutoff`, without a separate label-availability cutoff. Earlier event time
does not necessarily imply that a 30-day label was available at prediction or training time.

This is a potential temporal-leakage path for an as-of prediction simulation, not proof of
inflated published metrics: outcomes here are synthetic and their availability semantics are
not explicitly modeled. The contract must define those semantics before measuring the effect.
The current temporal tests check row counts on either side of a cutoff, not label maturity.

## Proposed implementation

1. Define whether prediction occurs at admission or discharge. Current length of stay requires
   particular care if prediction is intended at admission. Document the chosen prediction time.
2. Add explicit prediction and outcome-availability timestamps. Prefer observed availability
   when present; otherwise document a conservative synthetic rule with a 30-day maturity window.
   Decide how earlier-confirmed positives and still-unobserved negatives are represented.
3. Include historical readmission labels only when available by the prediction timestamp.
   Do not treat missing or immature labels as confirmed negatives. Handle same-day encounters
   explicitly; sorting IDs alone does not establish within-day knowledge.
4. Train only on labels available before the model-fit cutoff. Evaluate only rows with enough
   follow-up at the evaluation snapshot. Report exclusions and outcome coverage.
5. Rerun chronological and cohort diagnostics, recording changed row counts, prevalence,
   PR-AUC, ROC-AUC and calibration diagnostics. Preserve old evidence as a baseline and explain
   any metric change before refreshing dashboard snapshots.

## Acceptance tests

- A prior encounter whose outcome matures after prediction contributes no readmission label.
- An outcome available exactly at the boundary follows one documented inclusive/exclusive rule.
- Same-day encounters cannot expose another encounter's unavailable outcome.
- Rows before the train cutoff with later label availability are excluded from model fitting.
- Holdout rows lacking full follow-up are retained as pending or explicitly excluded with counts.
- Changing future outcomes leaves all earlier as-of features and training membership unchanged.
- Empty eligible splits and single-class cohorts are reported clearly rather than producing
  misleading metrics.

## Why this milestone matters

It demonstrates ownership of the full prediction contract: what was known, when it was known,
and which evaluation claims follow. Completion would strengthen the project's senior data
scientist story more than an additional interface feature. It remains proposed work; no
label-maturity fix, leakage reduction or clinical-performance improvement is claimed here.
