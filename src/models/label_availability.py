"""As-of readmission splits under the synthetic discharge-plus-30-day contract."""
from __future__ import annotations

import pandas as pd


def available_split(frame, cutoff, time_column="event_date", evaluation_as_of=None):
    """Training labels precede cutoff; evaluation labels are available by snapshot.

    Missing explicit availability is unknown, never a negative label. Legacy input
    without an availability column uses the documented synthetic 30-day delay.
    """
    data = frame.copy()
    if time_column not in data:
        raise ValueError(f"Missing time column: {time_column}")
    prediction = pd.to_datetime(data[time_column], utc=True, errors="raise")
    if prediction.isna().any() or data.empty:
        raise ValueError("Nonempty rows with valid prediction times are required")
    if "prediction_time" in data:
        declared = pd.to_datetime(data["prediction_time"], utc=True, errors="raise")
        if not declared.equals(prediction):
            raise ValueError("prediction_time must match the selected prediction time column")
    availability = (pd.to_datetime(data["label_available_at"], utc=True, errors="raise")
                    if "label_available_at" in data else prediction + pd.Timedelta(days=30))
    if (availability < prediction).any():
        raise ValueError("Label availability cannot precede prediction time")
    boundary = pd.to_datetime(cutoff, utc=True, errors="raise")
    snapshot = (prediction.max() if evaluation_as_of is None else
                pd.to_datetime(evaluation_as_of, utc=True, errors="raise"))
    if pd.isna(boundary) or pd.isna(snapshot) or snapshot < boundary:
        raise ValueError("Evaluation snapshot must be on or after cutoff")
    before = prediction < boundary
    holdout = (prediction >= boundary) & (prediction <= snapshot)
    train_mask = before & (availability < boundary)
    test_mask = holdout & (availability <= snapshot)
    train, test = data.loc[train_mask].copy(), data.loc[test_mask].copy()
    for subset in (train, test):
        if not subset.empty and not subset["readmitted_30d"].isin([0, 1]).all():
            raise ValueError("Mature targets must be binary, nonmissing labels")
    counts = {"train_rows": len(train), "test_rows": len(test),
              "train_pending_rows": int((before & ~train_mask).sum()),
              "test_pending_rows": int((holdout & ~test_mask).sum()),
              "after_snapshot_rows": int((prediction > snapshot).sum()),
              "evaluation_as_of": snapshot.isoformat(), "fit_cutoff": boundary.isoformat(),
              "label_contract": "synthetic_discharge_plus_30_days",
              "availability_source": "explicit" if "label_available_at" in data else "derived"}
    return train, test, counts
