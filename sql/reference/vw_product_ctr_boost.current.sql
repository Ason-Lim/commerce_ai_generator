-- vw_product_ctr_boost 현재 DB 정의 덤프 (참고용, 실행용 아님)
-- 추출: 2026-11-10T01:53:40+00:00
-- 의존 객체: vw_product_ctr_feedback

CREATE OR REPLACE VIEW vw_product_ctr_boost AS
 SELECT product_url,
    impression_count,
    click_count,
    ctr_pct,
        CASE
            WHEN impression_count < 10 THEN 0
            WHEN ctr_pct >= 30::numeric THEN 10
            WHEN ctr_pct >= 20::numeric THEN 7
            WHEN ctr_pct >= 10::numeric THEN 5
            WHEN ctr_pct = 0::numeric AND impression_count >= 20 THEN '-5'::integer
            ELSE 0
        END AS ctr_feedback_boost,
        CASE
            WHEN impression_count < 10 THEN '데이터 부족'::text
            WHEN ctr_pct >= 30::numeric THEN '사용자 반응 매우 우수'::text
            WHEN ctr_pct >= 20::numeric THEN '사용자 반응 우수'::text
            WHEN ctr_pct >= 10::numeric THEN '사용자 반응 양호'::text
            WHEN ctr_pct = 0::numeric AND impression_count >= 20 THEN '노출 대비 반응 낮음'::text
            ELSE '보통'::text
        END AS ctr_feedback_label
   FROM vw_product_ctr_feedback;
