CREATE OR REPLACE VIEW vw_platform_performance AS
WITH impressions AS (
    SELECT
        platform,
        COUNT(*) AS impression_count
    FROM impression_log
    GROUP BY platform
),
clicks AS (
    SELECT
        platform,
        COUNT(*) AS click_count
    FROM product_click_log
    GROUP BY platform
)
SELECT
    COALESCE(i.platform, 'unknown') AS platform,
    i.impression_count,
    COALESCE(c.click_count, 0) AS click_count,
    LEAST(
        ROUND(
            COALESCE(c.click_count, 0)::numeric
            / NULLIF(i.impression_count, 0)
            * 100,
            2
        ),
        100
    ) AS ctr_pct
FROM impressions i
LEFT JOIN clicks c
    ON COALESCE(i.platform, '') = COALESCE(c.platform, '')
ORDER BY impression_count DESC;
