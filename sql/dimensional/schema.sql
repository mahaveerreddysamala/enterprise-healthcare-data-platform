-- Star schema for the analytics warehouse.
-- Intended for Redshift, Snowflake or a Spark SQL warehouse.

CREATE TABLE dim_date (
    date_sk INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    week INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL
);

CREATE TABLE dim_patient (
    patient_sk BIGINT PRIMARY KEY,
    patient_id VARCHAR(64) NOT NULL,
    age INTEGER,
    sex VARCHAR(16),
    state VARCHAR(64),
    insurance_type VARCHAR(64)
);

CREATE TABLE dim_provider (
    provider_sk BIGINT PRIMARY KEY,
    provider_id VARCHAR(64) NOT NULL,
    specialty VARCHAR(128),
    facility_id VARCHAR(64)
);

CREATE TABLE fact_encounter (
    event_id VARCHAR(64) PRIMARY KEY,
    patient_sk BIGINT NOT NULL,
    provider_sk BIGINT,
    date_sk INTEGER NOT NULL,
    facility_id VARCHAR(64),
    event_ts TIMESTAMP NOT NULL,
    diagnosis_code VARCHAR(32),
    readmitted_30_days INTEGER,
    total_cost DECIMAL(14,2),
    encounter_count INTEGER NOT NULL
);

CREATE INDEX idx_fact_encounter_date ON fact_encounter(date_sk);
CREATE INDEX idx_fact_encounter_patient ON fact_encounter(patient_sk);
