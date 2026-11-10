-- 2026-11-10 1단계 전 정리: 뷰 점수에서 평점·리뷰 제외 (scripts/stage1_view_rating_fix.py 생성)
BEGIN;

CREATE OR REPLACE VIEW vw_recommendation_score AS
WITH base AS (
         SELECT vw_admin_recommendable_products.product_id,
            vw_admin_recommendable_products.platform_code,
            vw_admin_recommendable_products.platform_name,
            vw_admin_recommendable_products.fruit_name,
            vw_admin_recommendable_products.variety_name,
            vw_admin_recommendable_products.product_name,
            vw_admin_recommendable_products.normalized_product_name,
            vw_admin_recommendable_products.seller_name,
            vw_admin_recommendable_products.brand_name,
            vw_admin_recommendable_products.origin_area,
            vw_admin_recommendable_products.product_url,
            vw_admin_recommendable_products.collect_date,
            vw_admin_recommendable_products.collected_at,
            vw_admin_recommendable_products.price,
            vw_admin_recommendable_products.original_price,
            vw_admin_recommendable_products.discount_rate,
            vw_admin_recommendable_products.delivery_fee,
            vw_admin_recommendable_products.weight_text,
            vw_admin_recommendable_products.weight_kg,
            vw_admin_recommendable_products.unit_price_per_kg,
            vw_admin_recommendable_products.stock_status,
            vw_admin_recommendable_products.sale_status,
            vw_admin_recommendable_products.brix,
            vw_admin_recommendable_products.is_high_brix,
            vw_admin_recommendable_products.grade,
            vw_admin_recommendable_products.review_count,
            vw_admin_recommendable_products.rating,
            vw_admin_recommendable_products.trust_score,
            vw_admin_recommendable_products.quality_tags,
            vw_admin_recommendable_products.is_active,
                CASE
                    WHEN vw_admin_recommendable_products.price IS NULL THEN 0
                    ELSE 100 - ntile(100) OVER (PARTITION BY vw_admin_recommendable_products.fruit_name ORDER BY vw_admin_recommendable_products.price)
                END AS price_score,
                CASE
                    WHEN vw_admin_recommendable_products.unit_price_per_kg IS NULL THEN 50
                    ELSE 100 - ntile(100) OVER (PARTITION BY vw_admin_recommendable_products.fruit_name ORDER BY vw_admin_recommendable_products.unit_price_per_kg)
                END AS unit_price_score,
                CASE
                    WHEN vw_admin_recommendable_products.is_high_brix = true THEN 100
                    ELSE 40
                END AS brix_score,
                30 AS review_score,
                50 AS rating_score,
                CASE
                    WHEN vw_admin_recommendable_products.discount_rate IS NULL THEN 50
                    WHEN vw_admin_recommendable_products.discount_rate >= 40::numeric THEN 100
                    WHEN vw_admin_recommendable_products.discount_rate >= 30::numeric THEN 85
                    WHEN vw_admin_recommendable_products.discount_rate >= 20::numeric THEN 70
                    WHEN vw_admin_recommendable_products.discount_rate >= 10::numeric THEN 60
                    ELSE 50
                END AS discount_score
           FROM vw_admin_recommendable_products
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
    round(price_score::numeric * 0.25 + unit_price_score::numeric * 0.20 + brix_score::numeric * 0.20 + review_score::numeric * 0.15 + rating_score::numeric * 0.10 + discount_score::numeric * 0.10, 1) AS recommendation_score,
        CASE
            WHEN is_high_brix = true AND price_score >= 70 THEN '고당도 가성비 추천'::text
            WHEN is_high_brix = true AND review_score >= 70 THEN '고당도 리뷰 추천'::text
            WHEN unit_price_score >= 80 THEN 'kg당 가격 우수'::text
            WHEN discount_score >= 80 THEN '할인율 우수'::text
            ELSE '일반 추천'::text
        END AS recommendation_label
   FROM base;

CREATE OR REPLACE VIEW vw_trust_first_recommendation AS
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
        30 AS trust_review_score,
        50 AS trust_rating_score,
        CASE
            WHEN is_high_brix = true THEN 85
            ELSE 50
        END AS trust_quality_score,
        60 AS trust_platform_score,
    round(
        30::numeric * 0.35 +
        50::numeric * 0.25 +
        CASE
            WHEN is_high_brix = true THEN 85
            ELSE 50
        END::numeric * 0.25 +
        60::numeric * 0.15, 1) AS trust_first_score,
        CASE
            WHEN is_high_brix = true THEN '고당도 신뢰 추천'::text
            ELSE '신뢰 기반 추천'::text
        END AS trust_recommendation_label
   FROM vw_recommendation_score;

COMMIT;
