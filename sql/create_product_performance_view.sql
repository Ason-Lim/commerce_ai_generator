CREATE OR REPLACE VIEW vw_product_performance AS
WITH impressions AS (
    SELECT
        product_name,
        COUNT(*) AS impression_count
    FROM impression_log
    GROUP BY product_name
),
clicks AS (
    SELECT
        product_name,
        COUNT(*) AS click_count
    FROM product_click_log
    GROUP BY product_name
)
SELECT
    i.product_name,
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
    ON i.product_name = c.product_name
ORDER BY
    impression_count DESC;