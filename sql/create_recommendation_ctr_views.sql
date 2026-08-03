-- =========================================================
-- Recommendation CTR Views
-- 노출 대비 클릭률 기반 추천 성과 분석
-- =========================================================

CREATE OR REPLACE VIEW vw_product_ctr_signal AS
SELECT
    i.product_url,
    MAX(i.product_name) AS product_name,
    MAX(i.seller_name) AS seller_name,
    COUNT(*) AS impression_count,
    COUNT(c.id) AS click_count,
    ROUND(
        COUNT(c.id)::numeric / NULLIF(COUNT(*), 0) * 100,
        2
    ) AS ctr_pct,
    ROUND(AVG(i.score), 1) AS avg_impression_score,
    ROUND(AVG(c.score), 1) AS avg_click_score,
    MAX(i.created_at) AS last_impressed_at,
    MAX(c.created_at) AS last_clicked_at
FROM recommendation_impression_log i
LEFT JOIN product_click_log c
    ON i.session_id = c.session_id
   AND i.query = c.query
   AND i.product_url = c.product_url
GROUP BY i.product_url;


CREATE OR REPLACE VIEW vw_query_ctr_signal AS
SELECT
    i.query,
    COUNT(*) AS impression_count,
    COUNT(c.id) AS click_count,
    ROUND(
        COUNT(c.id)::numeric / NULLIF(COUNT(*), 0) * 100,
        2
    ) AS ctr_pct,
    MAX(i.created_at) AS last_impressed_at,
    MAX(c.created_at) AS last_clicked_at
FROM recommendation_impression_log i
LEFT JOIN product_click_log c
    ON i.session_id = c.session_id
   AND i.query = c.query
   AND i.product_url = c.product_url
GROUP BY i.query;


CREATE OR REPLACE VIEW vw_rank_ctr_signal AS
SELECT
    i.rank_position,
    COUNT(*) AS impression_count,
    COUNT(c.id) AS click_count,
    ROUND(
        COUNT(c.id)::numeric / NULLIF(COUNT(*), 0) * 100,
        2
    ) AS ctr_pct
FROM recommendation_impression_log i
LEFT JOIN product_click_log c
    ON i.session_id = c.session_id
   AND i.query = c.query
   AND i.product_url = c.product_url
GROUP BY i.rank_position
ORDER BY i.rank_position;
