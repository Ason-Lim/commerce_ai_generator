-- =========================================================
-- Rank Normalized CTR Views
-- 순위 편향을 보정한 CTR 성과 분석
-- =========================================================

CREATE OR REPLACE VIEW vw_rank_ctr_baseline AS
SELECT
    rank_position,
    COUNT(*) AS impression_count,
    COUNT(c.id) AS click_count,
    ROUND(
        COUNT(c.id)::numeric / NULLIF(COUNT(*), 0) * 100,
        2
    ) AS baseline_ctr_pct
FROM recommendation_impression_log i
LEFT JOIN product_click_log c
    ON i.session_id = c.session_id
   AND i.query = c.query
   AND i.product_url = c.product_url
GROUP BY rank_position;


CREATE OR REPLACE VIEW vw_product_rank_normalized_ctr AS
WITH product_ctr AS (
    SELECT
        i.product_url,
        MAX(i.product_name) AS product_name,
        MAX(i.seller_name) AS seller_name,
        ROUND(AVG(i.rank_position), 2) AS avg_rank_position,
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
    GROUP BY i.product_url
),
rank_baseline AS (
    SELECT
        i.product_url,
        ROUND(AVG(b.baseline_ctr_pct), 2) AS expected_ctr_pct
    FROM recommendation_impression_log i
    LEFT JOIN vw_rank_ctr_baseline b
        ON i.rank_position = b.rank_position
    GROUP BY i.product_url
)
SELECT
    p.*,
    b.expected_ctr_pct,
    ROUND(
        p.ctr_pct / NULLIF(b.expected_ctr_pct, 0),
        2
    ) AS rank_normalized_ctr_ratio,

    CASE
        WHEN p.impression_count < 3 THEN '데이터 부족'
        WHEN p.ctr_pct / NULLIF(b.expected_ctr_pct, 0) >= 1.5 THEN '순위 대비 클릭 우수'
        WHEN p.ctr_pct / NULLIF(b.expected_ctr_pct, 0) >= 1.1 THEN '순위 대비 양호'
        WHEN p.ctr_pct / NULLIF(b.expected_ctr_pct, 0) < 0.7 THEN '순위 대비 약함'
        ELSE '평균 수준'
    END AS rank_ctr_label
FROM product_ctr p
LEFT JOIN rank_baseline b
    ON p.product_url = b.product_url;
