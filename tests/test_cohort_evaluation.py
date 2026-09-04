from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.models.cohort_evaluation import (
    add_default_cohorts,
    evaluate_cohorts,
    render_cohort_report,
    write_cohort_evidence,
)


def _evaluation_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age": [25, 32, 45, 58, 68, 75, 28, 52, 70, 36, 61, 82],
            "gender": ["F", "M"] * 6,
            "risk_segment": ["low"] * 4 + ["high"] * 4 + ["medium"] * 4,
        }
    )


def test_default_cohorts_add_age_bands() -> None:
    frame = add_default_cohorts(_evaluation_frame())
    assert set(frame["age_band"]) == {"18-39", "40-64", "65+"}


def test_cohort_metrics_include_supported_and_guarded_groups() -> None:
    frame = add_default_cohorts(_evaluation_frame())
    targets = np.array([0, 1] * 6)
    probabilities = np.array([0.1, 0.8, 0.3, 0.7, 0.2, 0.9, 0.4, 0.6, 0.2, 0.8, 0.4, 0.7])

    results = evaluate_cohorts(
        frame,
        targets,
        probabilities,
        ["gender", "risk_segment"],
        min_rows=5,
    )

    assert set(results["dimension"]) == {"gender", "risk_segment"}
    assert set(results.loc[results["dimension"].eq("gender"), "status"]) == {"single_class"}
    assert set(results.loc[results["dimension"].eq("risk_segment"), "status"]) == {
        "insufficient_rows<5"
    }


def test_cohort_report_and_files_make_limitations_explicit(tmp_path) -> None:
    frame = add_default_cohorts(_evaluation_frame())
    targets = np.array([0, 1] * 6)
    probabilities = np.linspace(0.05, 0.95, 12)
    results = evaluate_cohorts(frame, targets, probabilities, ["age_band"], min_rows=4)

    report = render_cohort_report(results, threshold=0.5, min_rows=4)
    report_path = write_cohort_evidence(
        results, tmp_path / "cohorts.csv", threshold=0.5, min_rows=4
    )

    assert "Diagnostic ranges" in report
    assert "not a clinical fairness certification" in report
    assert report_path.is_file()
    assert (tmp_path / "cohorts.csv").is_file()


def test_cohort_evaluation_rejects_bad_probabilities() -> None:
    frame = add_default_cohorts(_evaluation_frame())
    with pytest.raises(ValueError, match="probabilities"):
        evaluate_cohorts(frame, [0] * len(frame), [1.5] * len(frame), min_rows=2)
