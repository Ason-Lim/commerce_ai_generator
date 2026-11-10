-- vw_ai_adaptive_recommendation 현재 DB 정의 덤프 (참고용, 실행용 아님)
-- 추출: 2026-11-10T01:53:40+00:00
-- 의존 객체: product_click_log, vw_trust_first_recommendation

CREATE OR REPLACE VIEW vw_ai_adaptive_recommendation AS
 WITH click_signal AS (
         SELECT product_click_log.product_url,
            count(*) AS click_count,
            round(avg(product_click_log.score), 1) AS avg_clicked_score,
            max(product_click_log.created_at) AS last_clicked_at
           FROM product_click_log
          WHERE product_click_log.product_url IS NOT NULL
          GROUP BY product_click_log.product_url
        ), base AS (
         SELECT r.product_id,
            r.fruit_name,
            r.platform_name,
            r.product_name,
            r.seller_name,
            r.price,
            r.unit_price_per_kg,
            r.discount_rate,
            r.is_high_brix,
            r.rating,
            r.review_count,
            r.product_url,
            r.price_score,
            r.unit_price_score,
            r.brix_score,
            r.review_score,
            r.rating_score,
            r.discount_score,
            r.recommendation_score,
            r.recommendation_label,
            r.trust_review_score,
            r.trust_rating_score,
            r.trust_quality_score,
            r.trust_platform_score,
            r.trust_first_score,
            r.trust_recommendation_label,
            COALESCE(c.click_count, 0::bigint) AS click_count,
            c.avg_clicked_score,
            c.last_clicked_at,
                CASE
                    WHEN COALESCE(c.click_count, 0::bigint) >= 10 THEN 15
                    WHEN COALESCE(c.click_count, 0::bigint) >= 5 THEN 10
                    WHEN COALESCE(c.click_count, 0::bigint) >= 2 THEN 5
                    ELSE 0
                END AS click_boost_score
           FROM vw_trust_first_recommendation r
             LEFT JOIN click_signal c ON r.product_url = c.product_url
        )
 SELECT product_id,
    fruit_name,
    platform_name,
    product_name,
    seller_name,
    price,
    unit_price_per_kg,
    discount_rate,
    is_high_brix,
    rating,
    review_count,
    product_url,
    price_score,
    unit_price_score,
    brix_score,
    review_score,
    rating_score,
    discount_score,
    recommendation_score,
    recommendation_label,
    trust_review_score,
    trust_rating_score,
    trust_quality_score,
    trust_platform_score,
    trust_first_score,
    trust_recommendation_label,
    click_count,
    avg_clicked_score,
    last_clicked_at,
    click_boost_score,
    round(LEAST(100::numeric, COALESCE(trust_first_score, recommendation_score, 0::numeric) + click_boost_score::numeric), 1) AS adaptive_score,
        CASE
            WHEN click_count >= 10 THEN '사용자 반응 우수 추천'::text
            WHEN click_count >= 5 THEN '클릭 검증 추천'::text
            WHEN click_count >= 2 THEN '관심 상승 상품'::text
            ELSE trust_recommendation_label
        END AS adaptive_recommendation_label
   FROM base;
