-- vw_admin_recommendable_products 현재 DB 정의 덤프 (참고용, 실행용 아님)
-- 추출: 2026-11-10T01:53:40+00:00
-- 의존 객체: vw_product_latest_price

CREATE OR REPLACE VIEW vw_admin_recommendable_products AS
 SELECT product_id,
    platform_code,
    platform_name,
    fruit_name,
    variety_name,
    product_name,
    normalized_product_name,
    seller_name,
    brand_name,
    origin_area,
    product_url,
    collect_date,
    collected_at,
    price,
    original_price,
    discount_rate,
    delivery_fee,
    weight_text,
    weight_kg,
    unit_price_per_kg,
    stock_status,
    sale_status,
    brix,
    is_high_brix,
    grade,
    review_count,
    rating,
    trust_score,
    quality_tags,
    is_active
   FROM vw_product_latest_price
  WHERE is_active = true AND fruit_name IS NOT NULL AND price IS NOT NULL AND product_name IS NOT NULL AND product_url IS NOT NULL;
