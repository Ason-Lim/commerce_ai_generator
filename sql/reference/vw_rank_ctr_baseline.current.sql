-- vw_rank_ctr_baseline 현재 DB 정의 덤프 (참고용, 실행용 아님)
-- 추출: 2026-11-10T01:53:40+00:00
-- 의존 객체: product_click_log, recommendation_impression_log

CREATE OR REPLACE VIEW vw_rank_ctr_baseline AS
 SELECT i.rank_position,
    count(*) AS impression_count,
    count(c.id) AS click_count,
    round(count(c.id)::numeric / NULLIF(count(*), 0)::numeric * 100::numeric, 2) AS baseline_ctr_pct
   FROM recommendation_impression_log i
     LEFT JOIN product_click_log c ON i.session_id = c.session_id AND i.query = c.query AND i.product_url = c.product_url
  GROUP BY i.rank_position;
