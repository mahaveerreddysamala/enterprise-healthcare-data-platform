# Data Dictionary

| Field | Type | Meaning |
|---|---|---|
| encounter_id | bigint | Unique synthetic encounter identifier |
| patient_id | bigint | Synthetic patient identifier |
| age | integer | Patient age at encounter |
| chronic_condition | integer | Synthetic chronic-condition indicator |
| emergency_visit | integer | Emergency encounter indicator |
| length_of_stay | integer | Encounter length in days |
| total_cost | double | Synthetic encounter cost |
| readmitted_30_days | integer | Synthetic 30-day readmission target |
| cost_per_day | double | Derived utilization metric |
| high_utilization | integer | LOS-based utilization indicator |
| risk_score | double | Composite risk feature |
| risk_segment | string | Low/medium/high/critical segment |
