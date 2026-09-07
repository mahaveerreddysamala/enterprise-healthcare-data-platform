"""Baseline readmission model for the Gold feature layer."""
from __future__ import annotations

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score
from src.models.label_availability import available_split

FEATURES = [
    "encounter_count", "emergency_visits", "total_los", "total_cost",
    "avg_risk_score", "high_utilization",
]


def train_readmission_model(df, cutoff: str, time_column: str = "event_date", evaluation_as_of=None):
    """Train the nonlinear baseline using a chronological holdout."""
    required = {*FEATURES, "readmitted_30d", time_column}
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"Missing Gold ML columns: {missing}")

    train, test, coverage = available_split(df, cutoff, time_column, evaluation_as_of)
    if train.empty or test.empty:
        raise ValueError("Chronological cutoff must leave mature rows on both sides")

    X_train = train[FEATURES]
    X_test = test[FEATURES]
    y_train = train["readmitted_30d"]
    y_test = test["readmitted_30d"]
    if y_train.nunique() < 2 or y_test.nunique() < 2:
        raise ValueError("Readmission target must contain both classes in train and test sets")
    model = HistGradientBoostingClassifier(random_state=42)
    model.fit(X_train, y_train)
    probability = model.predict_proba(X_test)[:, 1]
    metrics = {
        **coverage,
        "roc_auc": float(roc_auc_score(y_test, probability)),
        "pr_auc": float(average_precision_score(y_test, probability)),
    }
    return model, metrics
