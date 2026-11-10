-- vw_product_latest_price 현재 DB 정의 덤프 (참고용, 실행용 아님)
-- 추출: 2026-11-10T01:53:40+00:00
-- 의존 객체: fruit_master, fruit_variety_master, platform_master, product_master, product_price_snapshot, product_quality_snapshot

CREATE OR REPLACE VIEW vw_product_latest_price AS
 WITH latest_price AS (
         SELECT DISTINCT ON (product_price_snapshot.product_id) product_price_snapshot.price_snapshot_id,
            product_price_snapshot.product_id,
            product_price_snapshot.collected_at,
            product_price_snapshot.collect_date,
            product_price_snapshot.price,
            product_price_snapshot.original_price,
            product_price_snapshot.discount_rate,
            product_price_snapshot.delivery_fee,
            product_price_snapshot.unit_price_per_kg,
            product_price_snapshot.weight_text,
            product_price_snapshot.weight_kg,
            product_price_snapshot.stock_status,
            product_price_snapshot.sale_status,
            product_price_snapshot.source_keyword
           FROM product_price_snapshot
          ORDER BY product_price_snapshot.product_id, product_price_snapshot.collected_at DESC, product_price_snapshot.price_snapshot_id DESC
        ), latest_quality AS (
         SELECT DISTINCT ON (product_quality_snapshot.product_id) product_quality_snapshot.quality_snapshot_id,
            product_quality_snapshot.product_id,
            product_quality_snapshot.collected_at,
            product_quality_snapshot.brix,
            product_quality_snapshot.is_high_brix,
            product_quality_snapshot.grade,
            product_quality_snapshot.review_count,
            product_quality_snapshot.rating,
            product_quality_snapshot.trust_score,
            product_quality_snapshot.quality_tags
           FROM product_quality_snapshot
          ORDER BY product_quality_snapshot.product_id, product_quality_snapshot.collected_at DESC, product_quality_snapshot.quality_snapshot_id DESC
        )
 SELECT p.product_id,
    pf.platform_code,
    pf.platform_name,
    fm.fruit_name,
    fv.variety_name,
    p.product_name,
    p.normalized_product_name,
    p.seller_name,
    p.brand_name,
    p.origin_area,
    p.product_url,
    lp.collect_date,
    lp.collected_at,
    lp.price,
    lp.original_price,
    lp.discount_rate,
    lp.delivery_fee,
    lp.weight_text,
    lp.weight_kg,
    lp.unit_price_per_kg,
    lp.stock_status,
    lp.sale_status,
    lq.brix,
    lq.is_high_brix,
    lq.grade,
    lq.review_count,
    lq.rating,
    lq.trust_score,
    lq.quality_tags,
    p.is_active
   FROM product_master p
     LEFT JOIN platform_master pf ON p.platform_id = pf.platform_id
     LEFT JOIN fruit_master fm ON p.fruit_id = fm.fruit_id
     LEFT JOIN fruit_variety_master fv ON p.variety_id = fv.variety_id
     LEFT JOIN latest_price lp ON p.product_id = lp.product_id
     LEFT JOIN latest_quality lq ON p.product_id = lq.product_id
  WHERE p.is_active = true;
