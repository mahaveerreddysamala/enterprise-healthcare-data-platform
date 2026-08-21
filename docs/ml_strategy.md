# ML Strategy

## Objectives

1. Predict 30-day readmission risk to support care-management prioritization.
2. Predict patient-level healthcare cost for planning and utilization analysis.
3. Segment patients into behavioral/utilization risk groups.

## Feature Layer

The ML-ready patient table is produced from the Gold layer and contains utilization, prior-readmission, length-of-stay, demographic, and cost features. Features are computed at patient level to prevent repeated encounter rows from dominating training.

## Models

| Problem | Baseline | Metrics |
|---|---|---|
| Readmission | Logistic Regression | ROC-AUC, PR-AUC, Recall, F1 |
| Cost | HistGradientBoostingRegressor | MAE, RMSE, R2 |
| Segmentation | MiniBatchKMeans | cluster size, profile statistics |

## Production considerations

- Keep patient-level train/validation/test splits time-aware when real temporal data is available.
- Track experiments, parameters, metrics, and model artifacts with MLflow.
- Monitor feature drift, prediction drift, calibration, and performance after deployment.
- Use explainability for clinical/business review and avoid presenting predictions as clinical diagnoses.
- All repository data is synthetic and contains no PHI.
