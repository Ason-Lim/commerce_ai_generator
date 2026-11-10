-- vw_recommendation_score 현재 DB 정의 덤프 (참고용, 실행용 아님)
-- 추출: 2026-11-10T01:53:40+00:00
-- 의존 객체: vw_admin_recommendable_products

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
                CASE
                    WHEN vw_admin_recommendable_products.review_count IS NULL THEN 30
                    WHEN vw_admin_recommendable_products.review_count >= 1000 THEN 100
                    WHEN vw_admin_recommendable_products.review_count >= 500 THEN 85
                    WHEN vw_admin_recommendable_products.review_count >= 100 THEN 70
                    WHEN vw_admin_recommendable_products.review_count >= 30 THEN 55
                    ELSE 40
                END AS review_score,
                CASE
                    WHEN vw_admin_recommendable_products.rating IS NULL THEN 50
                    WHEN vw_admin_recommendable_products.rating >= 4.8 THEN 100
                    WHEN vw_admin_recommendable_products.rating >= 4.5 THEN 90
                    WHEN vw_admin_recommendable_products.rating >= 4.0 THEN 75
                    WHEN vw_admin_recommendable_products.rating >= 3.5 THEN 60
                    ELSE 40
                END AS rating_score,
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
