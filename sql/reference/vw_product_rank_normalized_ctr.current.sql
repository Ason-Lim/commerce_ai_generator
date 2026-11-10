-- vw_product_rank_normalized_ctr 현재 DB 정의 덤프 (참고용, 실행용 아님)
-- 추출: 2026-11-10T01:53:40+00:00
-- 의존 객체: product_click_log, recommendation_impression_log, vw_rank_ctr_baseline

CREATE OR REPLACE VIEW vw_product_rank_normalized_ctr AS
 WITH product_ctr AS (
         SELECT i.product_url,
            max(i.product_name) AS product_name,
            max(i.seller_name) AS seller_name,
            round(avg(i.rank_position), 2) AS avg_rank_position,
            count(*) AS impression_count,
            count(c.id) AS click_count,
            round(count(c.id)::numeric / NULLIF(count(*), 0)::numeric * 100::numeric, 2) AS ctr_pct,
            round(avg(i.score), 1) AS avg_impression_score,
            round(avg(c.score), 1) AS avg_click_score,
            max(i.created_at) AS last_impressed_at,
            max(c.created_at) AS last_clicked_at
           FROM recommendation_impression_log i
             LEFT JOIN product_click_log c ON i.session_id = c.session_id AND i.query = c.query AND i.product_url = c.product_url
          GROUP BY i.product_url
        ), rank_baseline AS (
         SELECT i.product_url,
            round(avg(b_1.baseline_ctr_pct), 2) AS expected_ctr_pct
           FROM recommendation_impression_log i
             LEFT JOIN vw_rank_ctr_baseline b_1 ON i.rank_position = b_1.rank_position
          GROUP BY i.product_url
        )
 SELECT p.product_url,
    p.product_name,
    p.seller_name,
    p.avg_rank_position,
    p.impression_count,
    p.click_count,
    p.ctr_pct,
    p.avg_impression_score,
    p.avg_click_score,
    p.last_impressed_at,
    p.last_clicked_at,
    b.expected_ctr_pct,
    round(p.ctr_pct / NULLIF(b.expected_ctr_pct, 0::numeric), 2) AS rank_normalized_ctr_ratio,
        CASE
            WHEN p.impression_count < 3 THEN '데이터 부족'::text
            WHEN (p.ctr_pct / NULLIF(b.expected_ctr_pct, 0::numeric)) >= 1.5 THEN '순위 대비 클릭 우수'::text
            WHEN (p.ctr_pct / NULLIF(b.expected_ctr_pct, 0::numeric)) >= 1.1 THEN '순위 대비 양호'::text
            WHEN (p.ctr_pct / NULLIF(b.expected_ctr_pct, 0::numeric)) < 0.7 THEN '순위 대비 약함'::text
            ELSE '평균 수준'::text
        END AS rank_ctr_label
   FROM product_ctr p
     LEFT JOIN rank_baseline b ON p.product_url = b.product_url;
