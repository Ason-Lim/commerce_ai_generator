-- =========================================================
-- AI Recommendation Analytics Views
-- 검색/클릭/의도 로그 기반 성과 분석
-- =========================================================

CREATE OR REPLACE VIEW vw_ai_search_summary AS
SELECT
    DATE(created_at) AS search_date,
    query,
    priority,
    COUNT(*) AS search_count,
    AVG(result_count) AS avg_result_count,
    MAX(created_at) AS last_searched_at
FROM search_log
GROUP BY DATE(created_at), query, priority;


CREATE OR REPLACE VIEW vw_ai_click_summary AS
SELECT
    DATE(created_at) AS click_date,
    query,
    product_name,
    seller_name,
    product_url,
    COUNT(*) AS click_count,
    ROUND(AVG(score), 1) AS avg_clicked_score,
    MAX(created_at) AS last_clicked_at
FROM product_click_log
GROUP BY DATE(created_at), query, product_name, seller_name, product_url;


CREATE OR REPLACE VIEW vw_ai_popular_keyword AS
SELECT
    normalized_keyword,
    intent_type,
    COUNT(*) AS search_count,
    MAX(created_at) AS last_seen_at
FROM user_context_log
WHERE normalized_keyword IS NOT NULL
GROUP BY normalized_keyword, intent_type
ORDER BY search_count DESC;


CREATE OR REPLACE VIEW vw_ai_recommendation_ctr AS
SELECT
    s.query,
    s.priority,
    COUNT(DISTINCT s.id) AS search_count,
    COUNT(DISTINCT c.id) AS click_count,
    ROUND(
        COUNT(DISTINCT c.id)::numeric
        / NULLIF(COUNT(DISTINCT s.id), 0)
        * 100,
        1
    ) AS ctr_pct,
    ROUND(AVG(c.score), 1) AS avg_clicked_score,
    MAX(GREATEST(s.created_at, COALESCE(c.created_at, s.created_at))) AS last_activity_at
FROM search_log s
LEFT JOIN product_click_log c
    ON s.session_id = c.session_id
   AND s.query = c.query
GROUP BY s.query, s.priority
ORDER BY ctr_pct DESC NULLS LAST, search_count DESC;


CREATE OR REPLACE VIEW vw_ai_top_clicked_products AS
SELECT
    product_name,
    seller_name,
    product_url,
    COUNT(*) AS click_count,
    ROUND(AVG(score), 1) AS avg_score,
    MAX(created_at) AS last_clicked_at
FROM product_click_log
GROUP BY product_name, seller_name, product_url
ORDER BY click_count DESC, avg_score DESC;
