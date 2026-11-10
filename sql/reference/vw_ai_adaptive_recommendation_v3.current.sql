-- vw_ai_adaptive_recommendation_v3 현재 DB 정의 덤프 (참고용, 실행용 아님)
-- 추출: 2026-11-10T01:53:40+00:00
-- 의존 객체: vw_ai_adaptive_recommendation, vw_product_rank_normalized_ctr

CREATE OR REPLACE VIEW vw_ai_adaptive_recommendation_v3 AS
 WITH ctr_signal AS (
         SELECT vw_product_rank_normalized_ctr.product_url,
            vw_product_rank_normalized_ctr.impression_count,
            vw_product_rank_normalized_ctr.click_count,
            vw_product_rank_normalized_ctr.ctr_pct,
            vw_product_rank_normalized_ctr.expected_ctr_pct,
            vw_product_rank_normalized_ctr.rank_normalized_ctr_ratio,
            vw_product_rank_normalized_ctr.rank_ctr_label
           FROM vw_product_rank_normalized_ctr
        ), base AS (
         SELECT r.fruit_name,
            r.product_name,
            r.seller_name,
            r.platform_name,
            r.price,
            r.unit_price_per_kg,
            r.discount_rate,
            r.is_high_brix,
            r.review_count,
            r.rating,
            r.recommendation_score,
            r.trust_first_score,
            r.adaptive_score,
            r.recommendation_label,
            r.trust_recommendation_label,
            r.adaptive_recommendation_label,
            r.product_url,
            COALESCE(c.impression_count, 0::bigint) AS impression_count,
            COALESCE(c.click_count, 0::bigint) AS click_count,
            COALESCE(c.ctr_pct, 0::numeric) AS ctr_pct,
            c.expected_ctr_pct,
            c.rank_normalized_ctr_ratio,
            COALESCE(c.rank_ctr_label, '데이터 없음'::text) AS rank_ctr_label,
                CASE
                    WHEN COALESCE(c.impression_count, 0::bigint) < 10 THEN 0
                    WHEN c.ctr_pct >= 30::numeric THEN 15
                    WHEN c.ctr_pct >= 20::numeric THEN 10
                    WHEN c.ctr_pct >= 10::numeric THEN 5
                    ELSE 0
                END AS ctr_boost,
                CASE
                    WHEN COALESCE(c.impression_count, 0::bigint) < 10 THEN 0
                    WHEN c.rank_normalized_ctr_ratio >= 1.5 THEN 10
                    WHEN c.rank_normalized_ctr_ratio >= 1.2 THEN 5
                    WHEN c.rank_normalized_ctr_ratio < 0.7 THEN '-5'::integer
                    ELSE 0
                END AS rank_ctr_boost
           FROM vw_ai_adaptive_recommendation r
             LEFT JOIN ctr_signal c ON r.product_url = c.product_url
        )
 SELECT fruit_name,
    product_name,
    seller_name,
    platform_name,
    price,
    unit_price_per_kg,
    discount_rate,
    is_high_brix,
    review_count,
    rating,
    recommendation_score,
    trust_first_score,
    adaptive_score,
    recommendation_label,
    trust_recommendation_label,
    adaptive_recommendation_label,
    product_url,
    impression_count,
    click_count,
    ctr_pct,
    expected_ctr_pct,
    rank_normalized_ctr_ratio,
    rank_ctr_label,
    ctr_boost,
    rank_ctr_boost,
    round(GREATEST(0::numeric, LEAST(100::numeric, COALESCE(adaptive_score, trust_first_score, recommendation_score, 0::numeric) + ctr_boost::numeric + rank_ctr_boost::numeric)), 1) AS adaptive_score_v3,
        CASE
            WHEN impression_count < 10 THEN adaptive_recommendation_label
            WHEN rank_ctr_boost >= 10 THEN '순위 대비 반응 우수'::text
            WHEN ctr_boost >= 15 THEN '클릭률 우수 추천'::text
            WHEN rank_ctr_boost < 0 THEN '순위 대비 반응 약함'::text
            ELSE adaptive_recommendation_label
        END AS adaptive_label_v3
   FROM base;
