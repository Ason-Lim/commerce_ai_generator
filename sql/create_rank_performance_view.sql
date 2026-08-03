CREATE OR REPLACE VIEW vw_rank_performance AS
SELECT
    rank,
    COUNT(*) AS impression_count,
    COUNT(DISTINCT product_name) AS unique_product_count
FROM impression_log
WHERE rank IS NOT NULL
GROUP BY rank
ORDER BY rank;
