"""Baseline readmission model for the Gold feature layer."""
from __future__ import annotations

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split

FEATURES = [
    "encounter_count", "emergency_visits", "total_los", "total_cost",
    "avg_risk_score", "high_utilization",
]


def train_readmission_model(df):
    X = df[FEATURES]
    y = df["readmitted_30_days"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    model = HistGradientBoostingClassifier(random_state=42)
    model.fit(X_train, y_train)
    probability = model.predict_proba(X_test)[:, 1]
    metrics = {
        "roc_auc": float(roc_auc_score(y_test, probability)),
        "pr_auc": float(average_precision_score(y_test, probability)),
    }
    return model, metrics
