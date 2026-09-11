-- SQLite. One row per channel across the supplied 18-month sample.
-- These are simulated data. The spend currency is not documented.
SELECT Channel,
       COUNT(*) AS months,
       ROUND(SUM(Ad_Spend), 2) AS recorded_spend,
       SUM(Leads_Generated) AS recorded_leads,
       ROUND(SUM(Ad_Spend) / NULLIF(SUM(Leads_Generated), 0), 2)
           AS recorded_spend_per_lead
FROM marketing
GROUP BY Channel
ORDER BY recorded_spend_per_lead DESC;
