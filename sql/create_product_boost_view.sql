CREATE OR REPLACE VIEW vw_product_boost AS
SELECT
    product_name,
    impression_count,
    click_count,
    ctr_pct,
    CASE
        WHEN impression_count >= 5 AND ctr_pct >= 5 THEN 5
        WHEN impression_count >= 5 AND ctr_pct >= 2 THEN 3
        WHEN impression_count >= 5 AND ctr_pct = 0 THEN -3
        ELSE 0
    END AS product_boost
FROM vw_product_performance;
