-- One row per response; never join raw weekly orders before counting themes.
WITH eligible AS (
 SELECT r.response_id,c.schedule
 FROM responses r JOIN customers c USING(customer_id)
 WHERE r.reason='Too expensive' AND LENGTH(TRIM(r.text))>0
), theme_counts AS (
 SELECT a.theme_id,COUNT(DISTINCT a.response_id) AS responses_mentioning_issue
 FROM assignments a JOIN eligible e USING(response_id)
 WHERE a.sentiment='negative'
 GROUP BY a.theme_id
)
SELECT theme_id,responses_mentioning_issue,
 (SELECT COUNT(*) FROM eligible) AS responding_customers,
 1.0*responses_mentioning_issue/(SELECT COUNT(*) FROM eligible) AS share
FROM theme_counts ORDER BY share DESC,theme_id;

-- When behavioural context is useful, aggregate weekly records to the customer first.
WITH order_context AS (
 SELECT customer_id,COUNT(*) AS weeks,
 SUM(CASE WHEN status='late' THEN 1 ELSE 0 END) AS late_weeks
 FROM orders GROUP BY customer_id
)
SELECT r.response_id,r.reason,o.weeks,o.late_weeks
FROM responses r LEFT JOIN order_context o USING(customer_id);
