"""Baseline readmission model for the Gold feature layer."""
from __future__ import annotations

import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score

FEATURES = [
    "encounter_count", "emergency_visits", "total_los", "total_cost",
    "avg_risk_score", "high_utilization",
]


def train_readmission_model(df, cutoff: str, time_column: str = "event_date"):
    """Train the nonlinear baseline using a chronological holdout."""
    required = {*FEATURES, "readmitted_30d", time_column}
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"Missing Gold ML columns: {missing}")

    frame = df.copy()
    frame[time_column] = pd.to_datetime(frame[time_column])
    cutoff_ts = pd.Timestamp(cutoff)
    train = frame[frame[time_column] < cutoff_ts]
    test = frame[frame[time_column] >= cutoff_ts]
    if train.empty or test.empty:
        raise ValueError("Chronological cutoff must leave rows on both sides")

    X_train = train[FEATURES]
    X_test = test[FEATURES]
    y_train = train["readmitted_30d"]
    y_test = test["readmitted_30d"]
    model = HistGradientBoostingClassifier(random_state=42)
    model.fit(X_train, y_train)
    probability = model.predict_proba(X_test)[:, 1]
    metrics = {
        "roc_auc": float(roc_auc_score(y_test, probability)),
        "pr_auc": float(average_precision_score(y_test, probability)),
    }
    return model, metrics
