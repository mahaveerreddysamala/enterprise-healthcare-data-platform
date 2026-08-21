-- Analytics layer: patient-level healthcare utilization and risk.
CREATE TABLE IF NOT EXISTS gold_patient_risk (
    patient_id BIGINT PRIMARY KEY,
    encounter_count INTEGER,
    emergency_visits INTEGER,
    total_los INTEGER,
    total_cost DECIMAL(18,2),
    avg_risk_score DECIMAL(8,3),
    high_utilization INTEGER,
    readmitted_30_days INTEGER,
    risk_segment VARCHAR(20)
);

CREATE INDEX IF NOT EXISTS idx_gold_patient_risk_segment
    ON gold_patient_risk (risk_segment);

CREATE INDEX IF NOT EXISTS idx_gold_patient_risk_readmit
    ON gold_patient_risk (readmitted_30_days);
