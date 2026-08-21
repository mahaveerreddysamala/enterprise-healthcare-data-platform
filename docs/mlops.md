# MLOps and Model Monitoring

## Lifecycle

```text
Gold features -> time-aware training -> evaluation -> MLflow -> model artifact -> batch scoring
                                      \-> metrics / drift baselines
```

## Validation

- Use chronological holdouts when an event timestamp is available.
- Track ROC-AUC and PR-AUC for readmission because class imbalance can make accuracy misleading.
- Track precision, recall, and F1 at the operational threshold.
- For cost prediction, track MAE, RMSE, and R2.

## Monitoring

Production implementations should monitor:

- Feature missingness and distribution drift.
- Prediction distribution and risk-band mix.
- Model performance once labels mature.
- Data freshness and pipeline SLA.
- Segment-level performance to identify degradation hidden by aggregate metrics.

## Experiment tracking

`src/models/mlflow_tracking.py` logs numeric evaluation metrics and the evaluation artifact to an MLflow experiment. The repository intentionally keeps the tracking backend configurable rather than embedding credentials or cloud endpoints.

## Governance

This repository uses synthetic data only. Predictions are examples for engineering and analytics evaluation and are not clinical diagnoses or treatment recommendations.
