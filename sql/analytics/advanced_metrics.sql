-- Reusable analytics queries for executive and operational reporting.

-- Monthly utilization, readmission and cost KPIs.
WITH monthly AS (
    SELECT
        d.year,
        d.month,
        COUNT(*) AS encounters,
        COUNT(DISTINCT f.patient_sk) AS active_patients,
        SUM(CASE WHEN f.readmitted_30d = 1 THEN 1 ELSE 0 END) AS readmissions,
        SUM(f.total_cost) AS total_cost
    FROM fact_encounter f
    JOIN dim_date d ON f.date_sk = d.date_sk
    GROUP BY d.year, d.month
)
SELECT
    year,
    month,
    encounters,
    active_patients,
    readmissions,
    ROUND(100.0 * readmissions / NULLIF(encounters, 0), 2) AS readmission_rate_pct,
    ROUND(total_cost, 2) AS total_cost
FROM monthly
ORDER BY year, month;

-- Provider-level performance with a minimum volume threshold.
SELECT
    p.provider_id,
    COUNT(*) AS encounters,
    ROUND(AVG(f.total_cost), 2) AS avg_encounter_cost,
    ROUND(100.0 * AVG(CASE WHEN f.readmitted_30d = 1 THEN 1.0 ELSE 0.0 END), 2)
        AS readmission_rate_pct
FROM fact_encounter f
JOIN dim_provider p ON f.provider_sk = p.provider_sk
GROUP BY p.provider_id
HAVING COUNT(*) >= 100
ORDER BY readmission_rate_pct DESC;
