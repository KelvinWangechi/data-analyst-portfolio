# Data and methodology

This portfolio case uses simulated process and productivity records; it does not represent an implemented client transformation.

| File | Observed grain | Coverage |
|---|---|---|
| [Process records](operational_efficiency_process_data.csv) | One process × day | 2,192 rows; eight processes; June 2023–February 2024 |
| [Productivity records](operational_efficiency_productivity_data.csv) | Employee/month/department fields; row meaning unresolved | 599 rows; March 2023–February 2024; 404 distinct employee-month keys |

The process phases contain 92 and 182 days. Compare within-process means, not phase totals. Mean recorded processing hours = sum of Processing_Time_Hours / process-day row count. Difference = before mean minus after mean. Relative decrease = difference / before mean. No workload denominator is documented, so this does not establish time per case or labour savings.

Error_Rate has no error count or task-count denominator. Its unweighted mean is not a pooled operational error rate. Productivity keys repeat; no documented key or deduplication rule permits employee-level claims. Before/After labels do not identify a causal treatment effect. Costs and case volumes are absent, so financial benefits are not estimated.

[Run the analysis](../run_analysis.py) · [Outputs, record checks and source hashes](../summary.json)
