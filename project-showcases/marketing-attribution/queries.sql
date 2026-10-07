-- Run against the exact-deduplicated events table.
-- source_row preserves original file order when timestamps tie.
-- One terminal conversion per cookie is validated before this query.
WITH ordered AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY cookie ORDER BY time, source_row) AS first_rank,
           ROW_NUMBER() OVER (PARTITION BY cookie ORDER BY time DESC, source_row DESC) AS last_rank,
           MAX(conversion) OVER (PARTITION BY cookie) AS converted
    FROM events
), credits AS (
    SELECT 'First touch' AS model, channel, 1.0 AS credit
    FROM ordered WHERE converted = 1 AND first_rank = 1
    UNION ALL
    SELECT 'Last touch' AS model, channel, 1.0 AS credit
    FROM ordered WHERE converted = 1 AND last_rank = 1
)
SELECT model, channel, SUM(credit) AS conversion_credit
FROM credits GROUP BY model, channel ORDER BY model, channel;
