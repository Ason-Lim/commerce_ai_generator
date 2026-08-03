CREATE OR REPLACE VIEW vw_recommendation_mode_ctr AS
WITH impressions AS (
    SELECT
        recommendation_mode,
        selected_priority,
        COUNT(*) AS impression_count
    FROM impression_log
    GROUP BY
        recommendation_mode,
        selected_priority
),
clicks AS (
    SELECT
        recommendation_mode,
        selected_priority,
        COUNT(*) AS click_count
    FROM product_click_log
    GROUP BY
        recommendation_mode,
        selected_priority
)
SELECT
    i.recommendation_mode,
    i.selected_priority,
    i.impression_count,
    COALESCE(c.click_count, 0) AS click_count,
    ROUND(
        COALESCE(c.click_count, 0)::numeric
        / NULLIF(i.impression_count, 0)
        * 100,
        2
    ) AS ctr_pct
FROM impressions i
LEFT JOIN clicks c
    ON i.recommendation_mode = c.recommendation_mode
   AND COALESCE(i.selected_priority, '') = COALESCE(c.selected_priority, '')
ORDER BY ctr_pct DESC, impression_count DESC;
