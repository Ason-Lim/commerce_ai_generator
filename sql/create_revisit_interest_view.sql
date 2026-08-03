CREATE OR REPLACE VIEW vw_revisit_keyword_interest AS
SELECT
    query,
    COUNT(*) AS click_count,
    MAX(clicked_at) AS last_clicked_at
FROM product_click_log
WHERE query IS NOT NULL
GROUP BY query
ORDER BY click_count DESC, last_clicked_at DESC;
