"""Interactive portfolio dashboard for the Enterprise Healthcare Data Platform."""
from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.dashboard import executive_kpis, load_dashboard_snapshot  # noqa: E402

st.set_page_config(page_title="Enterprise Healthcare Data Platform", page_icon="🏥", layout="wide")


@st.cache_data(show_spinner=False)
def load_snapshot():
    return load_dashboard_snapshot(ROOT)


snapshot = load_snapshot()
kpis = executive_kpis(snapshot)

st.title("Enterprise Healthcare Data Platform")
st.caption(
    "Synthetic-data evidence for Spark scale, Bronze/Silver/Gold quality, chronological "
    "readmission evaluation, and cohort-level model diagnostics."
)

with st.sidebar:
    st.header("Evidence controls")
    selected_dimension = st.selectbox(
        "Model cohort", list(snapshot.cohorts["dimension"].unique())
    )
    st.success("Synthetic data only — no PHI or clinical records.")

metric_columns = st.columns(len(kpis))
for column, (label, value) in zip(metric_columns, kpis.items(), strict=True):
    column.metric(label, value)

overview_tab, quality_tab, model_tab, operations_tab = st.tabs(
    ["Platform overview", "Data quality", "Model cohorts", "Operational evidence"]
)

with overview_tab:
    left, right = st.columns(2)
    benchmark_chart = snapshot.benchmarks.assign(
        workload=snapshot.benchmarks["rows"].map(lambda value: f"{int(value):,}")
    )
    with left:
        st.subheader("Measured AWS Spark runtime")
        st.line_chart(
            benchmark_chart.set_index("workload")[["runtime_seconds"]], color="#2563eb"
        )
    with right:
        st.subheader("Measured AWS Spark throughput")
        st.bar_chart(
            benchmark_chart.set_index("workload")[["rows_per_second"]], color="#0f766e"
        )
    st.dataframe(
        snapshot.benchmarks[
            ["rows", "partitions", "runtime_seconds", "rows_per_second", "status"]
        ],
        hide_index=True,
        width="stretch",
    )
    st.info(
        "The 50M result measures single-node Spark generation, aggregation, and S3 writes on "
        "EC2 t3.small; it is not presented as a multi-node benchmark."
    )

with quality_tab:
    st.subheader("Canonical sample contract")
    quality_columns = st.columns(5)
    quality_columns[0].metric("Rows", f"{snapshot.sample_rows:,}")
    quality_columns[1].metric("Null cells", snapshot.sample_quality["null_cells"])
    quality_columns[2].metric(
        "Duplicate encounters", snapshot.sample_quality["duplicate_encounters"]
    )
    quality_columns[3].metric("Invalid ages", snapshot.sample_quality["invalid_age"])
    quality_columns[4].metric("Negative costs", snapshot.sample_quality["negative_cost"])
    st.markdown(
        "**Contract flow:** canonical events → immutable Bronze → validated/deduplicated Silver "
        "→ patient-level Gold → dimensional analytics and ML features"
    )
    st.code(
        "encounter_id, patient_id, provider_id, facility_id, event_date, age, gender, "
        "chronic_condition, emergency_visit, length_of_stay, total_cost, readmitted_30d, "
        "diagnosis_code, payer_type"
    )

with model_tab:
    st.subheader("Chronological readmission evaluation")
    model_columns = st.columns(5)
    for column, metric in zip(
        model_columns, ["roc_auc", "pr_auc", "precision", "recall", "f1"], strict=True
    ):
        column.metric(metric.replace("_", " ").upper(), f'{snapshot.model_metrics[metric]:.4f}')

    selected = snapshot.cohorts[snapshot.cohorts["dimension"].eq(selected_dimension)].copy()
    supported = selected[selected["status"].eq("ok")].set_index("cohort")
    st.subheader(f"Performance by {selected_dimension.replace('_', ' ')}")
    if not supported.empty:
        st.bar_chart(supported[["pr_auc", "recall"]], color=["#7c3aed", "#ea580c"])
    st.dataframe(
        selected[
            [
                "cohort",
                "rows",
                "prevalence",
                "roc_auc",
                "pr_auc",
                "precision",
                "recall",
                "f1",
                "status",
            ]
        ],
        hide_index=True,
        width="stretch",
    )
    st.warning(
        "Cohort metrics diagnose synthetic model behavior. They are not a clinical fairness "
        "certification or evidence of real-world subgroup performance."
    )

with operations_tab:
    left, right = st.columns(2)
    with left:
        st.subheader("10M partition experiment")
        st.line_chart(
            snapshot.partition_tuning.set_index("partitions")[["runtime_seconds"]],
            color="#dc2626",
        )
        st.caption("Two partitions were fastest on the measured two-vCPU t3.small environment.")
    with right:
        st.subheader("Reproduce the evidence")
        st.code(
            "python benchmark/spark_healthcare_benchmark.py\n"
            "python scripts/run_readmission_validation.py",
            language="bash",
        )
        st.markdown(
            "CI repeats smaller Spark and model-validation profiles, runs tests on Python 3.11 "
            "and 3.12, builds the Docker image, and publishes JSON/CSV/Markdown evidence."
        )
